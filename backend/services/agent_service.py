"""Serviço de análise baseado em Pydantic AI e Groq.

As rotas dependem apenas de ``AgentService``. O serviço traduz erros de
configuração e de comunicação em resultados seguros para o contrato HTTP,
enquanto o ciclo de tool calling fica inteiramente sob responsabilidade do
Pydantic AI.
"""

from __future__ import annotations

import logging
import os
import re
from abc import ABC, abstractmethod
from dataclasses import replace
from typing import Any

import httpx
from pydantic_ai import Agent
from pydantic_ai.exceptions import (
    ModelAPIError,
    ModelHTTPError,
    ToolFailedError,
    ToolRetryError,
    UnexpectedModelBehavior,
)
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider
from pydantic_ai.messages import ToolCallPart

from agents.data_agent import DatasetAgentDeps, create_data_agent
from schemas.models import (
    AgentAnalyzeResponse,
    DatasetContext,
    ErrorQueryResult,
    TextQueryResult,
)
from services.dataset_service import DatasetService

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "openai/gpt-oss-20b"
SOURCE = "pydantic-ai-groq"

_MARKDOWN_MARKERS = re.compile(r"\*\*|__|`")
_TECHNICAL_COLUMN_NOTE = re.compile(
    r"\s*\(\s*coluna\s+[^()\n]{1,160}\)", re.IGNORECASE
)


def humanize_answer(answer: str) -> str:
    """Remove formatting that the text result component does not render."""

    cleaned = _TECHNICAL_COLUMN_NOTE.sub("", answer)
    cleaned = _MARKDOWN_MARKERS.sub("", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r" *\n *", "\n", cleaned)
    return cleaned.strip()


class AgentService(ABC):
    """Interface pública consumida pelas rotas FastAPI."""

    @abstractmethod
    def analyze(
        self, question: str, dataset_context: DatasetContext | None = None
    ) -> AgentAnalyzeResponse:
        raise NotImplementedError


class _MissingApiKeyError(Exception):
    pass


def _normalize_tool_call_name(name: str) -> str:
    """Remove o canal de saída que o GPT-OSS às vezes anexa ao nome."""

    return re.sub(r"<\|channel\|>.*$", "", name).strip()


class _NormalizedGroqModel(GroqModel):
    """Compatibilidade para o formato de tool call emitido pelo GPT-OSS.

    Em algumas respostas, o Groq devolve o canal de saída anexado ao nome da
    função (por exemplo, ``listar_colunas<|channel|>commentary``). O Pydantic
    AI recebe a resposta normalmente, mas não consegue localizar a tool. A
    correção é limitada à fronteira do provedor; o ciclo de execução continua
    sendo controlado pelo Pydantic AI.
    """

    def _process_response(self, response: Any) -> Any:
        model_response = super()._process_response(response)
        normalized_parts = []
        changed = False

        for part in model_response.parts:
            if isinstance(part, ToolCallPart):
                normalized_name = _normalize_tool_call_name(part.tool_name)
                if normalized_name != part.tool_name:
                    part = replace(part, tool_name=normalized_name)
                    changed = True
            normalized_parts.append(part)

        return replace(model_response, parts=normalized_parts) if changed else model_response


class PydanticAIAgentService(AgentService):
    """Executa o agente de dados com um modelo Groq configurável."""

    def __init__(
        self,
        agent: Agent[DatasetAgentDeps, str] | Any | None = None,
        dataset_service: DatasetService | None = None,
        model: str | None = None,
    ) -> None:
        self._agent = agent
        self._dataset_service = dataset_service or DatasetService()
        self._model = model or os.getenv("GROQ_MODEL", DEFAULT_MODEL)

    @property
    def model(self) -> str:
        """Nome do modelo configurado, útil para diagnóstico e testes."""

        return self._model

    def analyze(
        self, question: str, dataset_context: DatasetContext | None = None
    ) -> AgentAnalyzeResponse:
        trimmed = question.strip()
        if not trimmed:
            return self._error("Pergunta vazia", "Envie uma pergunta com pelo menos um caractere.")
        if dataset_context is None:
            return self._error(
                "Nenhum dataset carregado", "Carregue um dataset antes de fazer perguntas."
            )

        try:
            result = self._get_agent().run_sync(
                trimmed,
                deps=DatasetAgentDeps(
                    dataset_id=dataset_context.datasetId,
                    dataset_service=self._dataset_service,
                ),
            )
        except _MissingApiKeyError:
            logger.error("GROQ_API_KEY não configurada.")
            return self._error(
                "Configuração ausente",
                "A chave da API Groq (GROQ_API_KEY) não está configurada no servidor.",
            )
        except ModelHTTPError as exc:
            if exc.status_code == 413 or _is_oversized_request(exc):
                logger.warning("A requisição para a Groq excedeu o limite de contexto.")
                return self._error(
                    "Consulta muito grande",
                    "A consulta retornou dados demais para o modelo. Tente especificar uma tabela, coluna ou filtro.",
                )
            if exc.status_code == 429:
                logger.warning("Limite da API Groq atingido.")
                return self._error(
                    "Limite atingido",
                    "O limite de uso da API Groq foi atingido. Tente novamente em instantes.",
                )
            if exc.status_code in (408, 504):
                logger.warning("Timeout retornado pela API Groq: %s", exc.status_code)
                return self._error(
                    "Tempo esgotado",
                    "A análise demorou mais que o esperado. Tente novamente.",
                )
            logger.exception("Falha HTTP da API Groq: %s", exc.status_code)
            return self._error(
                "Falha de comunicação",
                "Não foi possível falar com o serviço de IA no momento. Tente novamente.",
            )
        except (httpx.TimeoutException, TimeoutError):
            logger.warning("Timeout ao comunicar com a API Groq.")
            return self._error(
                "Tempo esgotado", "A análise demorou mais que o esperado. Tente novamente."
            )
        except (ToolFailedError, ToolRetryError) as exc:
            logger.exception("Falha durante execução de tool: %s", type(exc).__name__)
            return self._error(
                "Falha na consulta",
                "Não foi possível consultar os dados necessários para responder. Tente novamente.",
            )
        except UnexpectedModelBehavior as exc:
            if "Unknown tool name" in str(exc) or "<|channel|>" in str(exc):
                logger.warning("O modelo retornou uma chamada de tool inválida.")
                return self._error(
                    "Falha ao interpretar a consulta",
                    "O agente não conseguiu interpretar essa consulta. Tente reformular a pergunta.",
                )
            logger.exception("Resposta inesperada do agente Pydantic AI.")
            return self._error(
                "Resposta inválida",
                "O agente não conseguiu produzir uma resposta válida para esta pergunta.",
            )
        except ModelAPIError:
            logger.exception("Erro de comunicação com a API Groq.")
            return self._error(
                "Falha de comunicação",
                "Não foi possível falar com o serviço de IA no momento. Tente novamente.",
            )
        except Exception:
            logger.exception("Erro inesperado durante a execução do agente.")
            return self._error(
                "Falha de comunicação",
                "Ocorreu uma falha inesperada ao analisar a pergunta. Tente novamente.",
            )

        answer = getattr(result, "output", None)
        if not isinstance(answer, str) or not answer.strip():
            logger.error("O agente retornou uma saída vazia ou incompatível.")
            return self._error(
                "Resposta inválida",
                "O agente não conseguiu produzir uma resposta válida para esta pergunta.",
            )

        return AgentAnalyzeResponse(
            status="success", source=SOURCE, result=TextQueryResult(answer=humanize_answer(answer))
        )

    def _get_agent(self) -> Agent[DatasetAgentDeps, str] | Any:
        if self._agent is not None:
            return self._agent

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise _MissingApiKeyError()

        model = _NormalizedGroqModel(
            self._model,
            provider=GroqProvider(api_key=api_key),
        )
        self._agent = create_data_agent(model)
        return self._agent

    def _error(self, title: str, message: str) -> AgentAnalyzeResponse:
        return AgentAnalyzeResponse(
            status="error",
            source=SOURCE,
            result=ErrorQueryResult(title=title, message=message),
        )


agent_service: AgentService = PydanticAIAgentService()


def _is_oversized_request(error: ModelHTTPError) -> bool:
    """Identifica o erro de payload grande mesmo quando o provedor usa 429."""

    body = error.body
    if not isinstance(body, dict):
        return False
    details = body.get("error")
    if not isinstance(details, dict):
        return False
    code = str(details.get("code", "")).lower()
    message = str(details.get("message", "")).lower()
    return code in {"request_too_large", "context_length_exceeded"} or (
        "request too large" in message or "reduce your message size" in message
    )
