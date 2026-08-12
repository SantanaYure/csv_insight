"""Implementação real do AgentService usando a API Gemini (google-genai).

Nenhuma rota e nenhum outro serviço deve importar `GeminiAgentService`
diretamente — todos dependem apenas da interface `AgentService`. Trocar de
implementação (outro provedor de LLM, por exemplo) é só apontar
`agent_service` (no fim do arquivo) para uma nova classe; nenhum contrato
HTTP muda.
"""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Callable

from google import genai
from google.genai import errors as genai_errors

from schemas.models import (
    AgentAnalyzeResponse,
    DatasetContext,
    ErrorQueryResult,
    TextQueryResult,
)
from services.dataset_service import (
    DatasetToolError,
    buscar_registros,
    calcular_estatisticas,
    filtrar_dados,
    listar_colunas,
    obter_resumo,
)

logger = logging.getLogger(__name__)


class AgentService(ABC):
    """Interface pública conhecida pelo resto da aplicação."""

    @abstractmethod
    def analyze(
        self, question: str, dataset_context: DatasetContext | None = None
    ) -> AgentAnalyzeResponse:
        """Analisa `question` no contexto (opcional) de um dataset e
        devolve um `AgentAnalyzeResponse` com um `QueryResult` pronto para
        ser devolvido ao front-end."""
        raise NotImplementedError


DEFAULT_MODEL = "gemini-3.6-flash"
MAX_TOOL_ITERATIONS = 5

SYSTEM_INSTRUCTION = """Você é um analista de dados que responde perguntas sobre um \
dataset carregado nesta sessão (arquivos CSV de um ZIP enviado pelo usuário).

Regras:
- Responda apenas com base no que as ferramentas devolverem sobre este dataset. \
Nunca use conhecimento geral do mundo, mesmo que "saiba" a resposta de outro \
contexto (ex.: perguntas sobre futebol, geografia, cultura geral).
- Se a pergunta não tem relação com as tabelas/colunas carregadas, diga isso \
claramente e informe que assuntos o dataset cobre (use obter_resumo e \
listar_colunas para descobrir).
- Nunca invente valores, totais ou nomes que não vieram de uma ferramenta.
- Use as ferramentas sempre que precisar consultar dados; não tente adivinhar.
- Seja objetivo: respostas diretas, sem enrolação.
- Se não houver dados suficientes para responder, diga isso explicitamente.
- Você nunca recebe nem interpreta o arquivo ZIP bruto — todo acesso aos dados \
é feito através das ferramentas disponíveis.
"""

TOOL_DECLARATIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "listar_colunas",
        "description": (
            "Lista as colunas (nome, tipo, descrição, se aceita nulo) de uma "
            "tabela do dataset, ou de todas as tabelas se nenhuma for informada."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "table": {
                    "type": "string",
                    "description": "Nome da tabela. Omita para listar as colunas de todas as tabelas.",
                },
            },
        },
    },
    {
        "type": "function",
        "name": "obter_resumo",
        "description": "Devolve um resumo do dataset: nome, tabelas disponíveis, total de linhas e colunas.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "buscar_registros",
        "description": "Devolve uma amostra de linhas de uma tabela do dataset.",
        "parameters": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Nome da tabela."},
                "limit": {
                    "type": "integer",
                    "description": "Quantidade máxima de linhas a devolver (padrão 10, máximo 50).",
                },
                "offset": {
                    "type": "integer",
                    "description": "Quantas linhas pular a partir do início (padrão 0).",
                },
            },
            "required": ["table"],
        },
    },
    {
        "type": "function",
        "name": "filtrar_dados",
        "description": "Devolve as linhas de uma tabela que atendem a uma condição sobre uma coluna.",
        "parameters": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Nome da tabela."},
                "column": {"type": "string", "description": "Nome da coluna a filtrar."},
                "operator": {
                    "type": "string",
                    "enum": ["=", "!=", ">", "<", ">=", "<=", "contains"],
                    "description": "Operador de comparação.",
                },
                "value": {"type": "string", "description": "Valor a comparar."},
            },
            "required": ["table", "column", "operator", "value"],
        },
    },
    {
        "type": "function",
        "name": "calcular_estatisticas",
        "description": (
            "Calcula estatísticas de uma coluna: soma, média, mínimo, máximo e "
            "contagem de nulos (colunas numéricas/moeda), ou valores mais "
            "frequentes (colunas de texto)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Nome da tabela."},
                "column": {"type": "string", "description": "Nome da coluna."},
            },
            "required": ["table", "column"],
        },
    },
]


class _MissingApiKeyError(Exception):
    """GEMINI_API_KEY não configurada."""


class _RateLimitError(Exception):
    """Limite da API Gemini (HTTP 429) atingido."""


class _ModelCommunicationError(Exception):
    """Erro de rede/servidor ao falar com a API Gemini."""


class _InvalidModelResponseError(Exception):
    """O modelo não produziu uma resposta de texto utilizável."""


class GeminiAgentService(AgentService):
    """Agente real: usa a API Gemini (Interactions API) com function calling
    sobre as tools de `dataset_service` para responder perguntas com base
    exclusivamente nos dados do dataset carregado."""

    SOURCE = "gemini"

    def __init__(self, client: genai.Client | None = None, model: str | None = None) -> None:
        self._client = client
        self._model = model or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)

    def analyze(
        self, question: str, dataset_context: DatasetContext | None = None
    ) -> AgentAnalyzeResponse:
        trimmed = question.strip()
        if not trimmed:
            return self._error(
                "Pergunta vazia", "Envie uma pergunta com pelo menos um caractere."
            )
        if dataset_context is None:
            return self._error(
                "Nenhum dataset carregado",
                "Carregue um dataset antes de fazer perguntas.",
            )

        try:
            client = self._get_client()
        except _MissingApiKeyError:
            logger.error("GEMINI_API_KEY não configurada.")
            return self._error(
                "Configuração ausente",
                "A chave da API Gemini (GEMINI_API_KEY) não está configurada no servidor.",
            )

        tools = self._build_tools(dataset_context.datasetId)

        try:
            answer = self._run_conversation(client, trimmed, tools)
        except _RateLimitError:
            logger.exception("Limite da API Gemini excedido.")
            return self._error(
                "Limite atingido",
                "O limite de uso da API Gemini foi atingido. Tente novamente em instantes.",
            )
        except _ModelCommunicationError:
            logger.exception("Erro de comunicação com a API Gemini.")
            return self._error(
                "Falha de comunicação",
                "Não foi possível falar com o serviço de IA no momento. Tente novamente.",
            )
        except _InvalidModelResponseError:
            logger.exception("Resposta inválida do modelo Gemini.")
            return self._error(
                "Resposta inválida",
                "O modelo não conseguiu produzir uma resposta válida para esta pergunta.",
            )

        return AgentAnalyzeResponse(
            status="success", source=self.SOURCE, result=TextQueryResult(answer=answer)
        )

    def _get_client(self) -> genai.Client:
        if self._client is not None:
            return self._client
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise _MissingApiKeyError()
        self._client = genai.Client(api_key=api_key)
        return self._client

    def _build_tools(self, dataset_id: str) -> dict[str, Callable[..., dict[str, Any]]]:
        return {
            "listar_colunas": lambda table=None: listar_colunas(dataset_id, table),
            "obter_resumo": lambda: obter_resumo(dataset_id),
            "buscar_registros": lambda table, limit=10, offset=0: buscar_registros(
                dataset_id, table, limit, offset
            ),
            "filtrar_dados": lambda table, column, operator, value: filtrar_dados(
                dataset_id, table, column, operator, value
            ),
            "calcular_estatisticas": lambda table, column: calcular_estatisticas(
                dataset_id, table, column
            ),
        }

    def _run_conversation(
        self,
        client: genai.Client,
        question: str,
        tools: dict[str, Callable[..., dict[str, Any]]],
    ) -> str:
        previous_id: str | None = None
        current_input: Any = question

        for _ in range(MAX_TOOL_ITERATIONS):
            try:
                interaction = client.interactions.create(
                    model=self._model,
                    input=current_input,
                    tools=TOOL_DECLARATIONS,
                    system_instruction=SYSTEM_INSTRUCTION,
                    previous_interaction_id=previous_id,
                )
            except genai_errors.APIError as exc:
                if exc.code == 429:
                    raise _RateLimitError() from exc
                raise _ModelCommunicationError() from exc
            except Exception as exc:
                raise _ModelCommunicationError() from exc

            function_results = []
            for step in interaction.steps:
                if getattr(step, "type", None) != "function_call":
                    continue

                tool = tools.get(step.name)
                if tool is None:
                    output: dict[str, Any] = {"error": f"Ferramenta '{step.name}' não existe."}
                else:
                    try:
                        output = tool(**step.arguments)
                    except DatasetToolError as exc:
                        output = {"error": str(exc)}
                    except TypeError as exc:
                        output = {"error": f"Parâmetros inválidos para '{step.name}': {exc}"}

                function_results.append(
                    {
                        "type": "function_result",
                        "name": step.name,
                        "call_id": step.id,
                        "result": [
                            {"type": "text", "text": json.dumps(output, ensure_ascii=False)}
                        ],
                    }
                )

            if not function_results:
                text = interaction.output_text
                if not text or not text.strip():
                    raise _InvalidModelResponseError()
                return text

            previous_id = interaction.id
            current_input = function_results

        raise _InvalidModelResponseError()

    def _error(self, title: str, message: str) -> AgentAnalyzeResponse:
        return AgentAnalyzeResponse(
            status="error",
            source=self.SOURCE,
            result=ErrorQueryResult(title=title, message=message),
        )


agent_service: AgentService = GeminiAgentService()
