from __future__ import annotations

from types import SimpleNamespace

from pydantic_ai import capture_run_messages
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.models.test import TestModel

from agents.data_agent import DatasetAgentDeps, create_data_agent
from schemas.models import DatasetContext, ErrorQueryResult
from services.agent_service import (
    PydanticAIAgentService,
    _normalize_tool_call_name,
    humanize_answer,
)
from services.dataset_service import DatasetService


class FakeAgent:
    def __init__(self, output: object = "Resposta baseada no dataset.", error: Exception | None = None):
        self.output = output
        self.error = error
        self.calls: list[tuple[str, DatasetAgentDeps]] = []

    def run_sync(self, prompt: str, *, deps: DatasetAgentDeps):
        self.calls.append((prompt, deps))
        if self.error is not None:
            raise self.error
        return SimpleNamespace(output=self.output)


def make_context(dataset_id: str) -> DatasetContext:
    return DatasetContext(
        datasetId=dataset_id,
        datasetName="Dataset de teste",
        tables=["fornecedores"],
        totalRows=3,
        totalColumns=3,
    )


def test_empty_question_returns_error_without_calling_agent():
    agent = FakeAgent()
    response = PydanticAIAgentService(agent=agent).analyze("   ", dataset_context=None)
    assert response.status == "error"
    assert isinstance(response.result, ErrorQueryResult)
    assert agent.calls == []


def test_missing_dataset_context_returns_error_without_calling_agent():
    agent = FakeAgent()
    response = PydanticAIAgentService(agent=agent).analyze(
        "Qual o total?", dataset_context=None
    )
    assert response.status == "error"
    assert "dataset" in response.result.message.lower()
    assert agent.calls == []


def test_missing_groq_api_key_returns_error(monkeypatch, stored_dataset_id):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    response = PydanticAIAgentService().analyze(
        "Qual o total?", dataset_context=make_context(stored_dataset_id)
    )
    assert response.status == "error"
    assert "GROQ_API_KEY" in response.result.message


def test_direct_text_answer_preserves_http_result_contract(stored_dataset_id):
    agent = FakeAgent(output="Existem 3 fornecedores.")
    service = PydanticAIAgentService(agent=agent)

    response = service.analyze(
        "Quantos fornecedores existem?", dataset_context=make_context(stored_dataset_id)
    )

    assert response.status == "success"
    assert response.source == "pydantic-ai-groq"
    assert response.result.answer == "Existem 3 fornecedores."
    assert agent.calls[0][1].dataset_id == stored_dataset_id
    assert isinstance(agent.calls[0][1].dataset_service, DatasetService)


def test_humanize_answer_removes_raw_markdown_and_technical_column_note():
    answer = "O valor total das notas fiscais (coluna **VALOR NOTA FISCAL**) é **R$ 3.371.754,84**."

    assert humanize_answer(answer) == "O valor total das notas fiscais é R$ 3.371.754,84."


def test_agent_service_humanizes_text_output_before_returning_it(stored_dataset_id):
    agent = FakeAgent(
        output="O valor total (coluna **VALOR_NOTA**) é **R$ 10,00**."
    )
    service = PydanticAIAgentService(agent=agent)

    response = service.analyze("Qual o total?", dataset_context=make_context(stored_dataset_id))

    assert response.result.answer == "O valor total é R$ 10,00."


def test_model_is_configurable_with_groq_model(monkeypatch):
    monkeypatch.setenv("GROQ_MODEL", "custom/gpt-oss")
    assert PydanticAIAgentService(agent=FakeAgent()).model == "custom/gpt-oss"


def test_gpt_oss_tool_channel_suffix_is_normalized():
    assert _normalize_tool_call_name("listar_colunas<|channel|>commentary") == "listar_colunas"
    assert _normalize_tool_call_name("obter_resumo") == "obter_resumo"


def test_pydantic_ai_controls_tool_calling_and_tool_delegates_to_dataset_service(
    stored_dataset_id,
):
    agent = create_data_agent(
        TestModel(call_tools=["obter_resumo"], custom_output_text="Resumo final.")
    )
    service = PydanticAIAgentService(agent=agent)

    with capture_run_messages() as messages:
        response = service.analyze(
            "Quantas tabelas tem o dataset?", dataset_context=make_context(stored_dataset_id)
        )

    assert response.status == "success"
    assert response.result.answer == "Resumo final."
    tool_return = next(
        part
        for message in messages
        for part in getattr(message, "parts", [])
        if getattr(part, "tool_name", None) == "obter_resumo"
        and hasattr(part, "content")
    )
    assert tool_return.content["datasetName"] == "Dataset de teste"


def test_all_dataset_tools_are_registered():
    agent = create_data_agent(TestModel(custom_output_text="ok"))
    assert set(agent._function_toolset.tools) == {
        "listar_colunas",
        "obter_resumo",
        "buscar_registros",
        "filtrar_dados",
        "calcular_estatisticas",
    }


def test_rate_limit_returns_friendly_message(stored_dataset_id):
    agent = FakeAgent(error=ModelHTTPError(429, "openai/gpt-oss-20b", {"error": "quota"}))
    response = PydanticAIAgentService(agent=agent).analyze(
        "Qual o total?", dataset_context=make_context(stored_dataset_id)
    )
    assert response.status == "error"
    assert "limite" in response.result.title.lower()


def test_oversized_request_returns_specific_message(stored_dataset_id):
    agent = FakeAgent(
        error=ModelHTTPError(
            413,
            "openai/gpt-oss-20b",
            {
                "error": {
                    "code": "rate_limit_exceeded",
                    "message": "Request too large; please reduce your message size",
                }
            },
        )
    )
    response = PydanticAIAgentService(agent=agent).analyze(
        "Liste o conteúdo", dataset_context=make_context(stored_dataset_id)
    )
    assert response.status == "error"
    assert response.result.title == "Consulta muito grande"
    assert "tabela" in response.result.message


def test_blank_agent_response_returns_invalid_response_error(stored_dataset_id):
    agent = FakeAgent(output="   ")
    response = PydanticAIAgentService(agent=agent).analyze(
        "Qual o total?", dataset_context=make_context(stored_dataset_id)
    )
    assert response.status == "error"
    assert "inválida" in response.result.title.lower()
