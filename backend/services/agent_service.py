"""Implementação real do AgentService usando a API Groq (SDK oficial `groq`,
modelo openai/gpt-oss-20b por padrão).

Nenhuma rota e nenhum outro serviço deve importar `GroqAgentService`
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

import groq

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


DEFAULT_MODEL = "openai/gpt-oss-20b"
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
        "function": {
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
    },
    {
        "type": "function",
        "function": {
            "name": "obter_resumo",
            "description": "Devolve um resumo do dataset: nome, tabelas disponíveis, total de linhas e colunas.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
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
    },
    {
        "type": "function",
        "function": {
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
    },
    {
        "type": "function",
        "function": {
            "name": "calcular_estatisticas",
            "description": (
                "Calcula estatísticas de uma coluna: soma, média, mínimo, máximo, "
                "contagem de nulos e de valores não numéricos (colunas numéricas/moeda), "
                "ou valores mais frequentes (colunas de texto)."
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
    },
]


class _MissingApiKeyError(Exception):
    """GROQ_API_KEY não configurada."""


class _RateLimitError(Exception):
    """Limite da API Groq (HTTP 429) atingido."""


class _TimeoutError(Exception):
    """A requisição à API Groq estourou o tempo limite."""


class _ModelCommunicationError(Exception):
    """Erro de rede/servidor ao falar com a API Groq."""


class _ModelUnavailableError(Exception):
    """Modelo configurado não existe ou está indisponível na Groq."""


class _InvalidModelResponseError(Exception):
    """O modelo não produziu uma resposta de texto utilizável."""


class _InvalidApiKeyError(Exception):
    """GROQ_API_KEY configurada, mas rejeitada pela API (inválida, revogada ou expirada)."""


_GPT_OSS_TOOL_CALL_CORRUPTION_MARKERS = ("tool_use_failed", "<|channel|>")


def _is_gpt_oss_tool_call_corruption(exc: Exception) -> bool:
    """Detecta uma falha de validação de tool call vinda da Groq (`tool_use_failed`
    ou vazamento do token interno `<|channel|>` do formato Harmony no nome da tool).
    O gpt-oss-20b tem uma falha de serving conhecida e intermitente em que vaza esse
    token dentro do nome da tool chamada (ex.: `listar_colunas<|channel|>commentary`),
    o que a Groq rejeita como tool inexistente antes mesmo de nos devolver uma
    resposta — esse é o caso dominante na prática, mas a checagem também pega
    qualquer outra falha de validação de tool call que reporte o mesmo código de
    erro. Não é algo que o nosso código causa ou pode evitar na requisição — é uma
    tentativa de mitigação tentando de novo, já que é um artefato estocástico da
    geração, não determinístico."""
    text = str(exc)
    return any(marker in text for marker in _GPT_OSS_TOOL_CALL_CORRUPTION_MARKERS)


class GroqAgentService(AgentService):
    """Agente real: usa a API Groq (chat completions, compatível com o padrão
    OpenAI) com function calling sobre as tools de `dataset_service` para
    responder perguntas com base exclusivamente nos dados do dataset
    carregado."""

    SOURCE = "groq"

    def __init__(self, client: groq.Groq | None = None, model: str | None = None) -> None:
        self._client = client
        self._model = model or os.getenv("GROQ_MODEL", DEFAULT_MODEL)

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
            logger.error("GROQ_API_KEY não configurada.")
            return self._error(
                "Configuração ausente",
                "A chave da API Groq (GROQ_API_KEY) não está configurada no servidor.",
            )

        tools = self._build_tools(dataset_context.datasetId)

        try:
            answer = self._run_conversation(client, trimmed, tools)
        except _RateLimitError:
            logger.exception("Limite da API Groq excedido.")
            return self._error(
                "Limite atingido",
                "O limite de uso da API Groq foi atingido. Tente novamente em instantes.",
            )
        except _TimeoutError:
            logger.exception("Timeout ao falar com a API Groq.")
            return self._error(
                "Tempo esgotado",
                "A requisição ao serviço de IA demorou demais. Tente novamente.",
            )
        except _ModelCommunicationError:
            logger.exception("Erro de comunicação com a API Groq.")
            return self._error(
                "Falha de comunicação",
                "Não foi possível falar com o serviço de IA no momento. Tente novamente.",
            )
        except _ModelUnavailableError:
            logger.exception("Modelo Groq indisponível.")
            return self._error(
                "Modelo indisponível",
                "O modelo de IA configurado não está disponível no momento.",
            )
        except _InvalidModelResponseError:
            logger.exception("Resposta inválida do modelo Groq.")
            return self._error(
                "Resposta inválida",
                "O modelo não conseguiu produzir uma resposta válida para esta pergunta.",
            )
        except _InvalidApiKeyError:
            logger.exception("GROQ_API_KEY rejeitada pela API Groq.")
            return self._error(
                "Chave inválida",
                "A chave da API Groq (GROQ_API_KEY) foi rejeitada. Verifique o valor em backend/.env.",
            )

        return AgentAnalyzeResponse(
            status="success", source=self.SOURCE, result=TextQueryResult(answer=answer)
        )

    def _get_client(self) -> groq.Groq:
        if self._client is not None:
            return self._client
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise _MissingApiKeyError()
        self._client = groq.Groq(api_key=api_key)
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

    def _create_completion(self, client: groq.Groq, messages: list[Any]) -> Any:
        """Chamada crua à API Groq, sem mapear exceções — quem chama decide o
        que fazer com elas (inclui a retentativa em `_run_conversation` para o
        artefato de corrupção do gpt-oss-20b antes do mapeamento final)."""
        return client.chat.completions.create(
            model=self._model,
            messages=messages,
            tools=TOOL_DECLARATIONS,
            tool_choice="auto",
        )

    def _run_conversation(
        self,
        client: groq.Groq,
        question: str,
        tools: dict[str, Callable[..., dict[str, Any]]],
    ) -> str:
        messages: list[Any] = [
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": question},
        ]

        for _ in range(MAX_TOOL_ITERATIONS):
            try:
                try:
                    response = self._create_completion(client, messages)
                except groq.BadRequestError as exc:
                    if not _is_gpt_oss_tool_call_corruption(exc):
                        raise
                    # Artefato de geração intermitente e conhecido do gpt-oss-20b
                    # (ver _is_gpt_oss_tool_call_corruption). Tenta a mesma
                    # requisição mais uma única vez antes de desistir; não conta
                    # como uma nova iteração do loop de tools (messages não muda).
                    # Qualquer exceção da segunda tentativa (sucesso ou não) segue
                    # para o mapeamento abaixo sem uma nova retentativa.
                    logger.warning(
                        "Tool call corrompida pelo gpt-oss-20b (<|channel|> vazado "
                        "no nome da tool); tentando novamente uma vez."
                    )
                    response = self._create_completion(client, messages)
            except groq.RateLimitError as exc:
                raise _RateLimitError() from exc
            except groq.APITimeoutError as exc:
                raise _TimeoutError() from exc
            except groq.NotFoundError as exc:
                raise _ModelUnavailableError() from exc
            except groq.APIConnectionError as exc:
                raise _ModelCommunicationError() from exc
            except groq.AuthenticationError as exc:
                raise _InvalidApiKeyError() from exc
            except groq.APIStatusError as exc:
                raise _ModelCommunicationError() from exc
            except Exception as exc:
                raise _ModelCommunicationError() from exc

            choices = getattr(response, "choices", None)
            if not choices:
                raise _InvalidModelResponseError()

            message = choices[0].message
            tool_calls = message.tool_calls

            if not tool_calls:
                content = message.content
                if not content or not content.strip():
                    raise _InvalidModelResponseError()
                return content

            messages.append(message)

            for tool_call in tool_calls:
                name = tool_call.function.name
                tool = tools.get(name)

                try:
                    args = json.loads(tool_call.function.arguments)
                except (TypeError, ValueError) as exc:
                    output: dict[str, Any] = {
                        "error": f"Argumentos inválidos para '{name}': {exc}"
                    }
                else:
                    if tool is None:
                        output = {"error": f"Ferramenta '{name}' não existe."}
                    else:
                        try:
                            output = tool(**args)
                        except DatasetToolError as exc:
                            output = {"error": str(exc)}
                        except TypeError as exc:
                            output = {
                                "error": f"Parâmetros inválidos para '{name}': {exc}"
                            }

                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": name,
                        "content": json.dumps(output, ensure_ascii=False),
                    }
                )

        raise _InvalidModelResponseError()

    def _error(self, title: str, message: str) -> AgentAnalyzeResponse:
        return AgentAnalyzeResponse(
            status="error",
            source=self.SOURCE,
            result=ErrorQueryResult(title=title, message=message),
        )


agent_service: AgentService = GroqAgentService()
