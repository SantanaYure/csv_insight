from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from google.genai import errors as genai_errors

from schemas.models import DatasetContext, ErrorQueryResult, TextQueryResult
from services.agent_service import GeminiAgentService


class FakeInteractions:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class FakeClient:
    def __init__(self, responses):
        self.interactions = FakeInteractions(responses)


def make_interaction(id_: str, steps=None, output_text: str | None = None):
    return SimpleNamespace(id=id_, steps=steps or [], output_text=output_text)


def make_function_call_step(name: str, arguments: dict, call_id: str):
    return SimpleNamespace(type="function_call", name=name, arguments=arguments, id=call_id)


def make_context(dataset_id: str) -> DatasetContext:
    return DatasetContext(
        datasetId=dataset_id,
        datasetName="Dataset de teste",
        tables=["fornecedores"],
        totalRows=3,
        totalColumns=3,
    )


def test_empty_question_returns_error_without_calling_client():
    service = GeminiAgentService(client=FakeClient([]))
    response = service.analyze("   ", dataset_context=None)
    assert response.status == "error"
    assert isinstance(response.result, ErrorQueryResult)


def test_missing_dataset_context_returns_error_without_calling_client():
    service = GeminiAgentService(client=FakeClient([]))
    response = service.analyze("Qual o total?", dataset_context=None)
    assert response.status == "error"
    assert "dataset" in response.result.message.lower()


def test_missing_api_key_returns_error(monkeypatch, stored_dataset_id):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    service = GeminiAgentService()
    response = service.analyze("Qual o total?", dataset_context=make_context(stored_dataset_id))
    assert response.status == "error"
    assert "GEMINI_API_KEY" in response.result.message


def test_direct_text_answer_without_tool_call(stored_dataset_id):
    client = FakeClient([make_interaction("int-1", output_text="Existem 3 fornecedores.")])
    service = GeminiAgentService(client=client)
    response = service.analyze(
        "Quantos fornecedores existem?", dataset_context=make_context(stored_dataset_id)
    )
    assert response.status == "success"
    assert response.source == "gemini"
    assert response.result == TextQueryResult(answer="Existem 3 fornecedores.")


def test_answers_after_one_real_tool_call(stored_dataset_id):
    call_step = make_function_call_step("obter_resumo", {}, "call-1")
    client = FakeClient(
        [
            make_interaction("int-1", steps=[call_step]),
            make_interaction("int-2", output_text="O dataset tem 1 tabela (fornecedores)."),
        ]
    )
    service = GeminiAgentService(client=client)
    response = service.analyze(
        "Quantas tabelas tem o dataset?", dataset_context=make_context(stored_dataset_id)
    )

    assert response.status == "success"
    assert response.result.answer == "O dataset tem 1 tabela (fornecedores)."

    second_call_kwargs = client.interactions.calls[1]
    assert second_call_kwargs["previous_interaction_id"] == "int-1"
    function_result = second_call_kwargs["input"][0]
    assert function_result["name"] == "obter_resumo"
    assert function_result["call_id"] == "call-1"
    payload = json.loads(function_result["result"][0]["text"])
    assert payload["datasetName"] == "Dataset de teste"


def test_unknown_tool_is_reported_back_to_model_and_recovers(stored_dataset_id):
    call_step = make_function_call_step("ferramenta_fantasma", {}, "call-1")
    client = FakeClient(
        [
            make_interaction("int-1", steps=[call_step]),
            make_interaction("int-2", output_text="Não sei responder isso."),
        ]
    )
    service = GeminiAgentService(client=client)
    response = service.analyze("Pergunta qualquer", dataset_context=make_context(stored_dataset_id))

    assert response.status == "success"
    function_result = client.interactions.calls[1]["input"][0]
    payload = json.loads(function_result["result"][0]["text"])
    assert "error" in payload


def test_tool_execution_error_is_reported_back_to_model(stored_dataset_id):
    call_step = make_function_call_step("listar_colunas", {"table": "inexistente"}, "call-1")
    client = FakeClient(
        [
            make_interaction("int-1", steps=[call_step]),
            make_interaction("int-2", output_text="Essa tabela não existe."),
        ]
    )
    service = GeminiAgentService(client=client)
    response = service.analyze(
        "Liste as colunas de inexistente", dataset_context=make_context(stored_dataset_id)
    )

    assert response.status == "success"
    function_result = client.interactions.calls[1]["input"][0]
    payload = json.loads(function_result["result"][0]["text"])
    assert "não existe" in payload["error"]


def test_rate_limit_error_returns_friendly_message(stored_dataset_id):
    client = FakeClient([genai_errors.ClientError(429, {"error": {"message": "quota exceeded"}})])
    service = GeminiAgentService(client=client)
    response = service.analyze("Qual o total?", dataset_context=make_context(stored_dataset_id))
    assert response.status == "error"
    assert "limite" in response.result.title.lower()


def test_server_error_returns_communication_failure_message(stored_dataset_id):
    client = FakeClient([genai_errors.ServerError(500, {"error": {"message": "internal"}})])
    service = GeminiAgentService(client=client)
    response = service.analyze("Qual o total?", dataset_context=make_context(stored_dataset_id))
    assert response.status == "error"
    assert "comunica" in response.result.title.lower()


def test_network_error_returns_communication_failure_message(stored_dataset_id):
    client = FakeClient([ConnectionError("connection reset")])
    service = GeminiAgentService(client=client)
    response = service.analyze("Qual o total?", dataset_context=make_context(stored_dataset_id))
    assert response.status == "error"
    assert "comunica" in response.result.title.lower()


def test_blank_final_response_returns_invalid_response_error(stored_dataset_id):
    client = FakeClient([make_interaction("int-1", output_text="   ")])
    service = GeminiAgentService(client=client)
    response = service.analyze("Qual o total?", dataset_context=make_context(stored_dataset_id))
    assert response.status == "error"
    assert "inválida" in response.result.title.lower()


def test_exceeding_tool_iterations_returns_generic_error(stored_dataset_id):
    call_step = make_function_call_step("obter_resumo", {}, "call-loop")
    client = FakeClient([make_interaction(f"int-{i}", steps=[call_step]) for i in range(5)])
    service = GeminiAgentService(client=client)
    response = service.analyze("Pergunta qualquer", dataset_context=make_context(stored_dataset_id))
    assert response.status == "error"
