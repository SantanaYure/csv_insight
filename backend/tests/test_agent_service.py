from __future__ import annotations

import json
from types import SimpleNamespace

import groq
import httpx

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


def test_invalid_api_key_returns_friendly_message(stored_dataset_id):
    client = FakeClient([_http_status_error(groq.AuthenticationError, 401, "invalid api key")])
    service = GroqAgentService(client=client)
    response = service.analyze("Qual o total?", dataset_context=make_context(stored_dataset_id))
    assert response.status == "error"
    title_and_message = (response.result.title + " " + response.result.message).lower()
    assert "inválida" in title_and_message or "chave" in title_and_message


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


def test_gpt_oss_tool_call_corruption_is_retried_once_and_succeeds(stored_dataset_id):
    corrupted_error = _http_status_error(
        groq.BadRequestError,
        400,
        "Tool call validation failed: tool call validation failed: attempted to call "
        "tool 'listar_colunas<|channel|>commentary' which was not in request.tools "
        "(code: tool_use_failed)",
    )
    client = FakeClient(
        [
            corrupted_error,
            make_response(content="Existem 3 fornecedores."),
        ]
    )
    service = GroqAgentService(client=client)
    response = service.analyze(
        "Quantos fornecedores existem?", dataset_context=make_context(stored_dataset_id)
    )

    assert response.status == "success"
    assert response.result == TextQueryResult(answer="Existem 3 fornecedores.")

    calls = client.chat.completions.calls
    assert len(calls) == 2
    assert calls[0]["messages"] == calls[1]["messages"]
    assert calls[0]["tools"] == calls[1]["tools"]


def test_gpt_oss_tool_call_corruption_retry_also_fails_falls_back_to_communication_error(
    stored_dataset_id,
):
    def corrupted_error():
        return _http_status_error(
            groq.BadRequestError,
            400,
            "Tool call validation failed: tool call validation failed: attempted to "
            "call tool 'listar_colunas<|channel|>commentary' which was not in "
            "request.tools (code: tool_use_failed)",
        )

    client = FakeClient([corrupted_error(), corrupted_error()])
    service = GroqAgentService(client=client)
    response = service.analyze(
        "Quantos fornecedores existem?", dataset_context=make_context(stored_dataset_id)
    )

    assert response.status == "error"
    assert "comunica" in response.result.title.lower()
    assert len(client.chat.completions.calls) == 2


def test_unrelated_bad_request_error_is_not_retried(stored_dataset_id):
    client = FakeClient(
        [_http_status_error(groq.BadRequestError, 400, "malformed request: missing field")]
    )
    service = GroqAgentService(client=client)
    response = service.analyze(
        "Quantos fornecedores existem?", dataset_context=make_context(stored_dataset_id)
    )

    assert response.status == "error"
    assert "comunica" in response.result.title.lower()
    assert len(client.chat.completions.calls) == 1


def test_exceeding_tool_iterations_returns_generic_error(stored_dataset_id):
    tool_call = make_tool_call("obter_resumo", {}, "call-loop")
    client = FakeClient([make_response(tool_calls=[tool_call]) for _ in range(5)])
    service = GroqAgentService(client=client)
    response = service.analyze("Pergunta qualquer", dataset_context=make_context(stored_dataset_id))
    assert response.status == "error"
