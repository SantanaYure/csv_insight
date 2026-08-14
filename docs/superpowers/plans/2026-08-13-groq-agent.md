# Migração do agente Gemini → Groq (GPT-OSS) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Substituir `GeminiAgentService` por `GroqAgentService` (SDK oficial `groq`, modelo `openai/gpt-oss-20b`), mantendo a interface `AgentService`, o contrato HTTP e todas as tools de `dataset_service.py` inalterados.

**Architecture:** `routes/analyze.py` (inalterado) → `AgentService.analyze()` (interface inalterada) → `GroqAgentService` faz o loop de function calling contra `client.chat.completions.create(...)` (formato compatível com OpenAI), chamando de volta as mesmas 5 funções de `dataset_service.py` já usadas pelo agente Gemini.

**Tech Stack:** Python 3.11+, FastAPI (já no projeto), `groq` (SDK oficial Groq, novo), `python-dotenv`/`pytest` (já no projeto, sem mudança).

## Global Constraints

- Não alterar o contrato HTTP: rotas, `schemas/models.py` e os formatos `{status, data}` / `{status, message, detail}` continuam exatamente como estão.
- Não alterar `dataset_service.py`: as 5 tools são reaproveitadas sem nenhuma mudança.
- `GROQ_API_KEY` é lida via `os.getenv`, nunca hardcoded no código.
- Nenhum stack trace, chave ou dado sensível pode aparecer no corpo de uma resposta ao front-end; detalhes completos só via `logger.exception(...)` no servidor.
- Um registro explícito de tools permitidas (dicionário nome→callable fechado por `dataset_id`); nenhuma função fora desse registro é executada, mesmo que o modelo peça.
- Referência completa de decisões: [`docs/superpowers/specs/2026-08-13-groq-agent-design.md`](../specs/2026-08-13-groq-agent-design.md).

---

## Task 1: `GroqAgentService` — loop de function calling

**Files:**
- Modify: `backend/services/agent_service.py` (reescrita completa — `GeminiAgentService` é removida)
- Modify: `backend/tests/test_agent_service.py` (reescrita completa — testes do Gemini removidos, novos testes para Groq)
- Modify: `backend/requirements.txt`

**Interfaces:**
- Consumes (já existem, não mudam): `DatasetToolError`, `listar_colunas`, `obter_resumo`, `buscar_registros`, `filtrar_dados`, `calcular_estatisticas` de `services.dataset_service`; `AgentAnalyzeResponse`, `DatasetContext`, `ErrorQueryResult`, `TextQueryResult` de `schemas.models`; fixture `stored_dataset_id` de `tests/conftest.py` (não muda).
- Produces: `class GroqAgentService(AgentService)` com `analyze(question, dataset_context=None) -> AgentAnalyzeResponse` (assinatura idêntica à interface `AgentService` já usada por `routes/analyze.py` — nenhuma rota muda); `agent_service: AgentService = GroqAgentService()` no fim do módulo, mesmo nome que `routes/analyze.py` já importa (`from services.agent_service import agent_service`).

- [ ] **Step 1: Trocar `google-genai` por `groq` em `requirements.txt`**

`backend/requirements.txt` fica (remove a linha `google-genai>=2.0,<3.0`, adiciona `groq`):

```text
fastapi>=0.115,<1.0
uvicorn[standard]>=0.30,<1.0
python-multipart>=0.0.9,<1.0
pytest>=8.0,<9.0
python-dotenv>=1.0,<2.0
groq>=0.30,<1.0
```

(Mantenha qualquer outra linha que já exista no arquivo atual além de `google-genai`, ex.: `httpx` se já tiver sido adicionada — só remova a linha do `google-genai` e adicione a do `groq`.)

```bash
cd backend && .venv/Scripts/pip uninstall -y google-genai && .venv/Scripts/pip install -r requirements.txt
```

- [ ] **Step 2: Reescrever `backend/tests/test_agent_service.py` por completo (vai falhar — `GroqAgentService` ainda não existe)**

```python
from __future__ import annotations

import json
from types import SimpleNamespace

import groq
import httpx
import pytest

from schemas.models import DatasetContext, ErrorQueryResult, TextQueryResult
from services.agent_service import GroqAgentService


class FakeCompletions:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class FakeChat:
    def __init__(self, responses):
        self.completions = FakeCompletions(responses)


class FakeClient:
    def __init__(self, responses):
        self.chat = FakeChat(responses)


def make_response(content: str | None = None, tool_calls: list | None = None):
    message = SimpleNamespace(content=content, tool_calls=tool_calls or [])
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


def make_tool_call(name: str, arguments: dict, call_id: str):
    function = SimpleNamespace(name=name, arguments=json.dumps(arguments))
    return SimpleNamespace(id=call_id, function=function)


def make_context(dataset_id: str) -> DatasetContext:
    return DatasetContext(
        datasetId=dataset_id,
        datasetName="Dataset de teste",
        tables=["fornecedores"],
        totalRows=3,
        totalColumns=3,
    )


def _http_status_error(exc_class, status_code: int, message: str = "erro"):
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(status_code, request=request)
    return exc_class(message, response=response, body=None)


def test_empty_question_returns_error_without_calling_client():
    service = GroqAgentService(client=FakeClient([]))
    response = service.analyze("   ", dataset_context=None)
    assert response.status == "error"
    assert isinstance(response.result, ErrorQueryResult)


def test_missing_dataset_context_returns_error_without_calling_client():
    service = GroqAgentService(client=FakeClient([]))
    response = service.analyze("Qual o total?", dataset_context=None)
    assert response.status == "error"
    assert "dataset" in response.result.message.lower()


def test_missing_api_key_returns_error(monkeypatch, stored_dataset_id):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    service = GroqAgentService()
    response = service.analyze("Qual o total?", dataset_context=make_context(stored_dataset_id))
    assert response.status == "error"
    assert "GROQ_API_KEY" in response.result.message


def test_direct_text_answer_without_tool_call(stored_dataset_id):
    client = FakeClient([make_response(content="Existem 3 fornecedores.")])
    service = GroqAgentService(client=client)
    response = service.analyze(
        "Quantos fornecedores existem?", dataset_context=make_context(stored_dataset_id)
    )
    assert response.status == "success"
    assert response.source == "groq"
    assert response.result == TextQueryResult(answer="Existem 3 fornecedores.")


def test_answers_after_one_real_tool_call(stored_dataset_id):
    tool_call = make_tool_call("obter_resumo", {}, "call-1")
    client = FakeClient(
        [
            make_response(tool_calls=[tool_call]),
            make_response(content="O dataset tem 1 tabela (fornecedores)."),
        ]
    )
    service = GroqAgentService(client=client)
    response = service.analyze(
        "Quantas tabelas tem o dataset?", dataset_context=make_context(stored_dataset_id)
    )

    assert response.status == "success"
    assert response.result.answer == "O dataset tem 1 tabela (fornecedores)."

    second_call_messages = client.chat.completions.calls[1]["messages"]
    tool_message = second_call_messages[-1]
    assert tool_message["role"] == "tool"
    assert tool_message["tool_call_id"] == "call-1"
    assert tool_message["name"] == "obter_resumo"
    payload = json.loads(tool_message["content"])
    assert payload["datasetName"] == "Dataset de teste"


def test_unknown_tool_is_reported_back_to_model_and_recovers(stored_dataset_id):
    tool_call = make_tool_call("ferramenta_fantasma", {}, "call-1")
    client = FakeClient(
        [
            make_response(tool_calls=[tool_call]),
            make_response(content="Não sei responder isso."),
        ]
    )
    service = GroqAgentService(client=client)
    response = service.analyze("Pergunta qualquer", dataset_context=make_context(stored_dataset_id))

    assert response.status == "success"
    tool_message = client.chat.completions.calls[1]["messages"][-1]
    payload = json.loads(tool_message["content"])
    assert "error" in payload


def test_tool_execution_error_is_reported_back_to_model(stored_dataset_id):
    tool_call = make_tool_call("listar_colunas", {"table": "inexistente"}, "call-1")
    client = FakeClient(
        [
            make_response(tool_calls=[tool_call]),
            make_response(content="Essa tabela não existe."),
        ]
    )
    service = GroqAgentService(client=client)
    response = service.analyze(
        "Liste as colunas de inexistente", dataset_context=make_context(stored_dataset_id)
    )

    assert response.status == "success"
    tool_message = client.chat.completions.calls[1]["messages"][-1]
    payload = json.loads(tool_message["content"])
    assert "não existe" in payload["error"]


def test_invalid_tool_arguments_json_is_reported_back_to_model(stored_dataset_id):
    bad_tool_call = SimpleNamespace(
        id="call-1",
        function=SimpleNamespace(name="obter_resumo", arguments="{not valid json"),
    )
    client = FakeClient(
        [
            make_response(tool_calls=[bad_tool_call]),
            make_response(content="Não consegui processar isso."),
        ]
    )
    service = GroqAgentService(client=client)
    response = service.analyze("Pergunta qualquer", dataset_context=make_context(stored_dataset_id))

    assert response.status == "success"
    tool_message = client.chat.completions.calls[1]["messages"][-1]
    payload = json.loads(tool_message["content"])
    assert "error" in payload


def test_rate_limit_error_returns_friendly_message(stored_dataset_id):
    client = FakeClient([_http_status_error(groq.RateLimitError, 429, "quota exceeded")])
    service = GroqAgentService(client=client)
    response = service.analyze("Qual o total?", dataset_context=make_context(stored_dataset_id))
    assert response.status == "error"
    assert "limite" in response.result.title.lower()


def test_timeout_error_returns_friendly_message(stored_dataset_id):
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    client = FakeClient([groq.APITimeoutError(request=request)])
    service = GroqAgentService(client=client)
    response = service.analyze("Qual o total?", dataset_context=make_context(stored_dataset_id))
    assert response.status == "error"
    assert "tempo" in response.result.title.lower()


def test_model_unavailable_error_returns_friendly_message(stored_dataset_id):
    client = FakeClient([_http_status_error(groq.NotFoundError, 404, "model not found")])
    service = GroqAgentService(client=client)
    response = service.analyze("Qual o total?", dataset_context=make_context(stored_dataset_id))
    assert response.status == "error"
    assert "indispon" in response.result.title.lower()


def test_connection_error_returns_communication_failure_message(stored_dataset_id):
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    client = FakeClient([groq.APIConnectionError(request=request)])
    service = GroqAgentService(client=client)
    response = service.analyze("Qual o total?", dataset_context=make_context(stored_dataset_id))
    assert response.status == "error"
    assert "comunica" in response.result.title.lower()


def test_blank_final_response_returns_invalid_response_error(stored_dataset_id):
    client = FakeClient([make_response(content="   ")])
    service = GroqAgentService(client=client)
    response = service.analyze("Qual o total?", dataset_context=make_context(stored_dataset_id))
    assert response.status == "error"
    assert "inválida" in response.result.title.lower()


def test_exceeding_tool_iterations_returns_generic_error(stored_dataset_id):
    tool_call = make_tool_call("obter_resumo", {}, "call-loop")
    client = FakeClient([make_response(tool_calls=[tool_call]) for _ in range(5)])
    service = GroqAgentService(client=client)
    response = service.analyze("Pergunta qualquer", dataset_context=make_context(stored_dataset_id))
    assert response.status == "error"
```

- [ ] **Step 3: Rodar os testes e confirmar que falham**

Run: `cd backend && .venv/Scripts/pytest tests/test_agent_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'groq'` (se o Step 1 não rodou ainda) ou `ImportError: cannot import name 'GroqAgentService'`.

- [ ] **Step 4: Reescrever `backend/services/agent_service.py` por completo**

```python
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
                response = client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    tools=TOOL_DECLARATIONS,
                    tool_choice="auto",
                )
            except groq.RateLimitError as exc:
                raise _RateLimitError() from exc
            except groq.APITimeoutError as exc:
                raise _TimeoutError() from exc
            except groq.NotFoundError as exc:
                raise _ModelUnavailableError() from exc
            except groq.APIConnectionError as exc:
                raise _ModelCommunicationError() from exc
            except groq.APIStatusError as exc:
                raise _ModelCommunicationError() from exc
            except Exception as exc:
                raise _ModelCommunicationError() from exc

            message = response.choices[0].message
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
```

- [ ] **Step 5: Rodar os testes e confirmar que passam**

Run: `cd backend && .venv/Scripts/pytest tests/test_agent_service.py -v`
Expected: PASS — 14 testes verdes.

- [ ] **Step 6: Rodar a suíte inteira para garantir que nada quebrou (tools do dataset + smoke test HTTP não mudam)**

Run: `cd backend && .venv/Scripts/pytest -v`
Expected: PASS — 33 testes verdes no total (31 atuais − 12 do `test_agent_service.py` antigo do Gemini + 14 novos do Groq = 19 de `dataset_service`/smoke + 14 do agente).

- [ ] **Step 7: Commit**

```bash
git add backend/services/agent_service.py backend/tests/test_agent_service.py backend/requirements.txt
git commit -m "Replace GeminiAgentService with GroqAgentService (openai/gpt-oss-20b via Groq API)"
```

---

## Task 2: Configuração, docs e verificação manual de ponta a ponta

**Files:**
- Modify: `backend/.env.example`
- Modify: `backend/README.md`

**Interfaces:**
- Consumes: nada de código novo — só documenta o que a Task 1 já produziu.
- Produces: nada consumido por outra task (é a última).

- [ ] **Step 1: Atualizar `backend/.env.example`**

Trocar as variáveis do Gemini pelas da Groq, mantendo o resto do arquivo como já está (comentário sobre `CORS_ORIGINS` etc. permanece igual — só troque o bloco do provedor de LLM):

```text
# Chave da API Groq (gere em https://console.groq.com/keys).
# Obrigatória para /api/analyze e /api/datasets/{id}/questions.
# Atenção: uma vez configurada, linhas do CSV (até 50 por chamada de ferramenta) são enviadas à API da Groq para responder às perguntas.
GROQ_API_KEY=

# Modelo usado pelo agente. Opcional — usa o GPT-OSS 20B por padrão.
GROQ_MODEL=openai/gpt-oss-20b
```

Remova por completo as linhas `GEMINI_API_KEY` e `GEMINI_MODEL` (e qualquer comentário que só fizer sentido para elas).

- [ ] **Step 2: Atualizar `backend/README.md`**

Substituir a seção `## Agente de IA (Gemini)` (e a subseção "Privacidade" dentro dela, se existir) por:

```markdown
## Agente de IA (Groq · GPT-OSS)

`services/agent_service.py` define a interface `AgentService` (método `analyze`) e
`GroqAgentService`, que usa a API Groq (SDK oficial `groq`, endpoint de chat completions
compatível com o padrão OpenAI) com function calling sobre 5 ferramentas de consulta
implementadas em `services/dataset_service.py`:

| Tool | Parâmetros | Devolve |
| --- | --- | --- |
| `listar_colunas` | `table?` | colunas (nome, tipo, descrição, nulos) de uma tabela ou de todas |
| `obter_resumo` | — | nome do dataset, tabelas, total de linhas/colunas, resumo |
| `buscar_registros` | `table, limit=10, offset=0` | amostra de linhas (máx. 50) |
| `filtrar_dados` | `table, column, operator, value` | linhas que batem o filtro (`=,!=,>,<,>=,<=,contains`) |
| `calcular_estatisticas` | `table, column` | numérico: count/sum/avg/min/max/nullCount/nonNumericCount · texto: distinct/top-values |

Fluxo: a pergunta vai para `client.chat.completions.create(...)`; se o modelo pedir uma tool
(`message.tool_calls`), o `GroqAgentService` executa a função correspondente em
`dataset_service.py` e devolve o resultado como mensagem `role: "tool"`, repetindo até o
modelo responder com texto (limite de 5 idas e voltas). O agente só responde com base no
que as tools devolverem — nunca usa conhecimento geral do modelo — e diz explicitamente
quando a pergunta não tem relação com os dados carregados.

Configuração (`backend/.env`, veja `.env.example`):

| Variável | Obrigatória | Padrão | Descrição |
| --- | --- | --- | --- |
| `GROQ_API_KEY` | sim | — | chave da API Groq |
| `GROQ_MODEL` | não | `openai/gpt-oss-20b` | modelo usado pelo agente |

**Privacidade:** uma vez configurada `GROQ_API_KEY`, as linhas devolvidas por
`buscar_registros`/`filtrar_dados` (até 50 por chamada) são enviadas à API da Groq como
parte da resposta à pergunta — os dados saem da máquina local.

Erros (chave ausente, dataset não carregado, timeout, limite de uso, falha de comunicação,
modelo indisponível, ferramenta inexistente, erro de execução de ferramenta, resposta
inválida do modelo) nunca geram uma exceção HTTP nova: viram um `QueryResult` do tipo
`error`, no mesmo formato que qualquer outra resposta de pergunta — sem stack trace nem
detalhe interno exposto ao front-end.

Rotas e outros serviços só conhecem a interface `AgentService` — trocar a implementação
(outro provedor de LLM, por exemplo) é apontar a variável `agent_service` para uma nova
classe, sem tocar nas rotas.
```

Se o `README.md` tiver qualquer outra menção a "Gemini" fora dessa seção (ex.: no cabeçalho da
estrutura de pastas), atualize para "Groq" também — grep por "Gemini" no arquivo antes de
finalizar este passo para não deixar nenhuma sobrando.

- [ ] **Step 3: Confirmar que não sobrou nenhuma referência a Gemini no código do backend**

Run: `cd backend && grep -ril "gemini" --include="*.py" --include="*.md" --include="*.txt" --include="*.example" . || echo "nenhuma referência encontrada"`
Expected: `nenhuma referência encontrada` (ou, na pior das hipóteses, só comentários históricos claramente identificados como tal — não deve haver import, classe, variável de ambiente ou dependência viva com "gemini" no nome).

- [ ] **Step 4: Verificação manual de ponta a ponta com uma `GROQ_API_KEY` real**

Peça ao usuário a `GROQ_API_KEY` (ele gera em https://console.groq.com/keys) antes deste
passo; coloque em `backend/.env` (nunca no código nem em texto plano fora do `.env`, que já
está no `.gitignore` da raiz do projeto).

Gerar um ZIP de teste mínimo (não versionado):

```bash
cd backend
python -c "
import zipfile
with zipfile.ZipFile('sample.zip', 'w') as zf:
    zf.writestr('fornecedores.csv', 'id_fornecedor,razao_social,valor_total\n1,Alfa Ltda,100.00\n2,Beta SA,250.50\n3,Alfa Filial,\n')
"
```

Rodar o servidor:

```bash
cd backend && .venv/Scripts/uvicorn main:app --port 8000
```

Em outro terminal:

```bash
curl.exe -s -X POST http://localhost:8000/api/datasets -F "file=@sample.zip" | python -m json.tool
```

Guardar o `data.id` da resposta e usar nas duas chamadas seguintes (substituir `<DATASET_ID>`):

```bash
curl.exe -s -X POST http://localhost:8000/api/analyze -H "Content-Type: application/json" -d "{\"datasetId\": \"<DATASET_ID>\", \"question\": \"Qual o valor total dos fornecedores?\"}" | python -m json.tool
```

```bash
curl.exe -s -X POST http://localhost:8000/api/analyze -H "Content-Type: application/json" -d "{\"datasetId\": \"<DATASET_ID>\", \"question\": \"Qual foi o resultado do jogo de futebol de ontem?\"}" | python -m json.tool
```

Confirmar:
- a primeira pergunta devolve `data.type == "text"` com um valor que bate com os dados do
  `sample.zip` (soma de 100.00 + 250.50 = 350.50, ignorando a linha vazia) e `data.source`
  (se exposto) ou o campo interno `source` do agente é `"groq"`;
- a segunda pergunta não inventa uma resposta sobre futebol — devolve texto dizendo que o
  dataset não tem esse assunto;
- nenhuma chave ou stack trace aparece na resposta HTTP (só no console do servidor, se algo
  falhar).

Depois de confirmar, apagar o `sample.zip` de teste (não deve ser commitado):

```bash
rm backend/sample.zip
```

- [ ] **Step 5: Commit**

```bash
git add backend/.env.example backend/README.md
git commit -m "Update config and docs for the Groq migration"
```
