# Agente Gemini real no AgentService — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Substituir `MockAgentService` por `GeminiAgentService`, um agente real que usa a API Gemini (`google-genai`, Interactions API) com function calling sobre ferramentas de consulta ao dataset, sem alterar o contrato HTTP existente.

**Architecture:** `routes/analyze.py` (inalterado) → `AgentService.analyze()` (interface inalterada) → `GeminiAgentService` faz o loop de function calling contra `client.interactions.create(...)`, chamando de volta 5 funções puras novas em `dataset_service.py` que leem do `store` em memória já existente.

**Tech Stack:** Python 3.11+, FastAPI (já no projeto), `google-genai` (SDK oficial Gemini), `python-dotenv` (carrega `backend/.env`), `pytest` (testes, novo no projeto).

## Global Constraints

- Não alterar o contrato HTTP: rotas, `schemas/models.py` e os formatos `{status, data}` / `{status, message, detail}` continuam exatamente como estão.
- `GEMINI_API_KEY` é lida via `os.getenv`, nunca hardcoded no código.
- Nenhum stack trace ou dado sensível pode aparecer no corpo de uma resposta ao front-end; detalhes completos só via `logger.exception(...)` no servidor.
- Tools do agente vivem em `dataset_service.py` (não duplicar lógica de dados dentro do agente); `agent_service.py` só orquestra o loop com o Gemini.
- Referência completa de decisões: [`docs/superpowers/specs/2026-08-12-gemini-agent-design.md`](../specs/2026-08-12-gemini-agent-design.md).

---

## Task 1: Tools de consulta ao dataset em `dataset_service.py`

**Files:**
- Modify: `backend/services/dataset_service.py`
- Create: `backend/pytest.ini`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_dataset_tools.py`
- Modify: `backend/requirements.txt`

**Interfaces:**
- Consumes: `store` (instância de `_DatasetStore`, já existe no fim de `dataset_service.py`), `Dataset`/`DatasetTable`/`DatasetColumn`/`DatasetColumnType` de `schemas/models.py`, `parse_number` (já existe em `dataset_service.py`).
- Produces (usado pela Task 2):
  - `class DatasetToolError(Exception)`
  - `def listar_colunas(dataset_id: str, table: str | None = None) -> dict[str, Any]`
  - `def obter_resumo(dataset_id: str) -> dict[str, Any]`
  - `def buscar_registros(dataset_id: str, table: str, limit: int = 10, offset: int = 0) -> dict[str, Any]`
  - `def filtrar_dados(dataset_id: str, table: str, column: str, operator: str, value: str) -> dict[str, Any]`
  - `def calcular_estatisticas(dataset_id: str, table: str, column: str) -> dict[str, Any]`
  - fixture `stored_dataset_id` (pytest, em `tests/conftest.py`, tabela `fornecedores` com 3 linhas) — reaproveitada pela Task 2.

- [ ] **Step 1: Adicionar `pytest` ao `requirements.txt` e criar `backend/pytest.ini`**

`backend/requirements.txt` fica:

```text
fastapi>=0.115,<1.0
uvicorn[standard]>=0.30,<1.0
python-multipart>=0.0.9,<1.0
pytest>=8.0,<9.0
```

Criar `backend/pytest.ini`:

```ini
[pytest]
pythonpath = .
```

(`pythonpath = .` garante que `from services.dataset_service import ...` e `from schemas.models import ...` resolvam do jeito que `uvicorn main:app` já resolve, rodando os testes com `cwd` em `backend/`.)

Instalar a dependência nova no venv existente:

```bash
cd backend && .venv/Scripts/pip install -r requirements.txt
```

- [ ] **Step 2: Criar a fixture de dataset de teste em `backend/tests/conftest.py`**

```python
from __future__ import annotations

import pytest

from schemas.models import Dataset, DatasetColumn, DatasetTable
from services.dataset_service import store

FORNECEDORES_ROWS = [
    {"id_fornecedor": "1", "razao_social": "Alfa Ltda", "valor_total": 100.0},
    {"id_fornecedor": "2", "razao_social": "Beta SA", "valor_total": 250.5},
    {"id_fornecedor": "3", "razao_social": "Alfa Filial", "valor_total": None},
]


@pytest.fixture
def stored_dataset_id() -> str:
    dataset_id = "ds-test-tools"
    columns = [
        DatasetColumn(name="id_fornecedor", dataType="string", nullable=False, nullCount=0),
        DatasetColumn(name="razao_social", dataType="string", nullable=False, nullCount=0),
        DatasetColumn(name="valor_total", dataType="currency", nullable=True, nullCount=1),
    ]
    table = DatasetTable(
        id="fornecedores",
        name="fornecedores",
        fileName="fornecedores.csv",
        description="id_fornecedor, razao_social e mais 1 colunas.",
        rowCount=len(FORNECEDORES_ROWS),
        columnCount=len(columns),
        columns=columns,
        preview=[],
    )
    dataset = Dataset(
        id=dataset_id,
        name="Dataset de teste",
        uploadedAt="2026-08-12T00:00:00Z",
        status="ready",
        totalRows=len(FORNECEDORES_ROWS),
        totalColumns=len(columns),
        tables=[table],
        summary="Foram lidas 1 tabelas (fornecedores), somando 3 colunas.",
    )
    store.save(dataset, {"fornecedores": [dict(row) for row in FORNECEDORES_ROWS]})
    return dataset_id
```

- [ ] **Step 3: Escrever os testes das 5 tools em `backend/tests/test_dataset_tools.py` (vão falhar — as funções ainda não existem)**

```python
from __future__ import annotations

import pytest

from services.dataset_service import (
    DatasetToolError,
    buscar_registros,
    calcular_estatisticas,
    filtrar_dados,
    listar_colunas,
    obter_resumo,
)


def test_listar_colunas_returns_all_tables_when_no_table_given(stored_dataset_id):
    result = listar_colunas(stored_dataset_id)
    assert result["tables"][0]["table"] == "fornecedores"
    names = [c["name"] for c in result["tables"][0]["columns"]]
    assert names == ["id_fornecedor", "razao_social", "valor_total"]


def test_listar_colunas_returns_single_table(stored_dataset_id):
    result = listar_colunas(stored_dataset_id, table="fornecedores")
    assert result["table"] == "fornecedores"
    assert len(result["columns"]) == 3


def test_listar_colunas_unknown_table_raises(stored_dataset_id):
    with pytest.raises(DatasetToolError, match="não existe"):
        listar_colunas(stored_dataset_id, table="clientes")


def test_listar_colunas_unknown_dataset_raises():
    with pytest.raises(DatasetToolError, match="não encontrado"):
        listar_colunas("dataset-inexistente")


def test_obter_resumo(stored_dataset_id):
    result = obter_resumo(stored_dataset_id)
    assert result["datasetName"] == "Dataset de teste"
    assert result["totalRows"] == 3
    assert result["tables"][0]["rowCount"] == 3


def test_buscar_registros_respects_limit_and_offset(stored_dataset_id):
    result = buscar_registros(stored_dataset_id, table="fornecedores", limit=2, offset=1)
    assert result["totalRows"] == 3
    assert result["returned"] == 2
    assert [row["id_fornecedor"] for row in result["rows"]] == ["2", "3"]


def test_buscar_registros_clamps_limit_to_max(stored_dataset_id):
    result = buscar_registros(stored_dataset_id, table="fornecedores", limit=999)
    assert result["returned"] == 3


def test_buscar_registros_unknown_table_raises(stored_dataset_id):
    with pytest.raises(DatasetToolError, match="não existe"):
        buscar_registros(stored_dataset_id, table="clientes")


def test_filtrar_dados_equality_on_string_column(stored_dataset_id):
    result = filtrar_dados(
        stored_dataset_id, table="fornecedores", column="id_fornecedor", operator="=", value="2"
    )
    assert result["totalMatches"] == 1
    assert result["rows"][0]["razao_social"] == "Beta SA"


def test_filtrar_dados_contains_on_string_column(stored_dataset_id):
    result = filtrar_dados(
        stored_dataset_id,
        table="fornecedores",
        column="razao_social",
        operator="contains",
        value="alfa",
    )
    assert result["totalMatches"] == 2


def test_filtrar_dados_numeric_comparison(stored_dataset_id):
    result = filtrar_dados(
        stored_dataset_id, table="fornecedores", column="valor_total", operator=">", value="150"
    )
    assert result["totalMatches"] == 1
    assert result["rows"][0]["id_fornecedor"] == "2"


def test_filtrar_dados_invalid_operator_raises(stored_dataset_id):
    with pytest.raises(DatasetToolError, match="Operador"):
        filtrar_dados(
            stored_dataset_id, table="fornecedores", column="valor_total", operator="~=", value="1"
        )


def test_filtrar_dados_unknown_column_raises(stored_dataset_id):
    with pytest.raises(DatasetToolError, match="não existe"):
        filtrar_dados(
            stored_dataset_id, table="fornecedores", column="inexistente", operator="=", value="1"
        )


def test_calcular_estatisticas_numeric_column(stored_dataset_id):
    result = calcular_estatisticas(stored_dataset_id, table="fornecedores", column="valor_total")
    assert result["count"] == 2
    assert result["nullCount"] == 1
    assert result["sum"] == pytest.approx(350.5)
    assert result["avg"] == pytest.approx(175.25)
    assert result["min"] == pytest.approx(100.0)
    assert result["max"] == pytest.approx(250.5)


def test_calcular_estatisticas_text_column(stored_dataset_id):
    result = calcular_estatisticas(stored_dataset_id, table="fornecedores", column="razao_social")
    assert result["count"] == 3
    assert result["distinctCount"] == 3
    assert result["topValues"][0]["count"] == 1
```

- [ ] **Step 4: Rodar os testes e confirmar que falham (import error — as funções não existem)**

Run: `cd backend && .venv/Scripts/pytest tests/test_dataset_tools.py -v`
Expected: FAIL — `ImportError: cannot import name 'DatasetToolError' from 'services.dataset_service'`

- [ ] **Step 5: Implementar as 5 tools em `backend/services/dataset_service.py`**

Trocar a linha de imports (linha 28, `from typing import BinaryIO`) por:

```python
from collections import Counter
from typing import Any, BinaryIO
```

(mantendo a posição do `from dataclasses import dataclass, field` e `from datetime import datetime, timezone` logo abaixo, como já está.)

Logo depois da classe `DatasetIngestionError` (linhas 52-54 atuais), adicionar:

```python
class DatasetToolError(Exception):
    """Erro de execução de uma tool do agente, com mensagem pronta para ser
    devolvida ao modelo (e, em último caso, ao usuário)."""
```

No fim do arquivo (depois de `store = _DatasetStore()`), adicionar:

```python


# --- tools do agente (consultas sobre um dataset já carregado) -------------

MAX_TOOL_ROWS = 50
_FILTER_OPERATORS = ("=", "!=", ">", "<", ">=", "<=", "contains")


def _get_dataset_or_raise(dataset_id: str) -> Dataset:
    dataset = store.get_dataset(dataset_id)
    if dataset is None:
        raise DatasetToolError("Dataset não encontrado.")
    return dataset


def _find_table(dataset: Dataset, table_ref: str) -> DatasetTable:
    for table in dataset.tables:
        if table.id == table_ref or table.name == table_ref:
            return table
    available = ", ".join(table.name for table in dataset.tables)
    raise DatasetToolError(
        f"Tabela '{table_ref}' não existe neste dataset. Tabelas disponíveis: {available}."
    )


def _find_column(table: DatasetTable, column_ref: str) -> DatasetColumn:
    for column in table.columns:
        if column.name == column_ref:
            return column
    available = ", ".join(column.name for column in table.columns)
    raise DatasetToolError(
        f"Coluna '{column_ref}' não existe na tabela '{table.name}'. Colunas disponíveis: {available}."
    )


def _column_info(column: DatasetColumn) -> dict[str, Any]:
    return {
        "name": column.name,
        "dataType": column.dataType,
        "description": column.description,
        "nullable": column.nullable,
        "nullCount": column.nullCount,
    }


def listar_colunas(dataset_id: str, table: str | None = None) -> dict[str, Any]:
    """Lista as colunas de uma tabela do dataset, ou de todas as tabelas se
    `table` for None."""
    dataset = _get_dataset_or_raise(dataset_id)

    if table is not None:
        found = _find_table(dataset, table)
        return {"table": found.name, "columns": [_column_info(column) for column in found.columns]}

    return {
        "tables": [
            {"table": t.name, "columns": [_column_info(column) for column in t.columns]}
            for t in dataset.tables
        ]
    }


def obter_resumo(dataset_id: str) -> dict[str, Any]:
    """Resumo do dataset: nome, tabelas, totais de linhas/colunas e descrição
    textual gerada na ingestão."""
    dataset = _get_dataset_or_raise(dataset_id)
    return {
        "datasetName": dataset.name,
        "summary": dataset.summary,
        "totalRows": dataset.totalRows,
        "totalColumns": dataset.totalColumns,
        "tables": [
            {
                "table": t.name,
                "rowCount": t.rowCount,
                "columnCount": t.columnCount,
                "description": t.description,
            }
            for t in dataset.tables
        ],
    }


def buscar_registros(
    dataset_id: str, table: str, limit: int = 10, offset: int = 0
) -> dict[str, Any]:
    """Amostra de linhas de uma tabela (limit entre 1 e 50, offset >= 0)."""
    dataset = _get_dataset_or_raise(dataset_id)
    found = _find_table(dataset, table)

    safe_limit = max(1, min(limit, MAX_TOOL_ROWS))
    safe_offset = max(0, offset)

    rows = store.rows_by_table(dataset_id).get(found.id, [])
    page = rows[safe_offset : safe_offset + safe_limit]

    return {
        "table": found.name,
        "totalRows": len(rows),
        "returned": len(page),
        "rows": page,
    }


def _coerce_filter_value(raw: str, data_type: DatasetColumnType) -> CellValue:
    if data_type in ("number", "currency"):
        parsed = parse_number(raw)
        return raw if parsed is None else parsed
    return raw


def _matches(cell: CellValue, operator: str, target: CellValue) -> bool:
    if operator == "contains":
        return isinstance(cell, str) and isinstance(target, str) and target.lower() in cell.lower()
    if cell is None:
        return False
    try:
        if operator == "=":
            return cell == target
        if operator == "!=":
            return cell != target
        if operator == ">":
            return cell > target
        if operator == "<":
            return cell < target
        if operator == ">=":
            return cell >= target
        if operator == "<=":
            return cell <= target
    except TypeError:
        return False
    return False


def filtrar_dados(
    dataset_id: str, table: str, column: str, operator: str, value: str
) -> dict[str, Any]:
    """Linhas de uma tabela cuja `column` satisfaz `operator` em relação a
    `value`. Devolve no máximo 50 linhas, mas informa o total de acertos."""
    if operator not in _FILTER_OPERATORS:
        raise DatasetToolError(
            f"Operador '{operator}' inválido. Use um de: {', '.join(_FILTER_OPERATORS)}."
        )

    dataset = _get_dataset_or_raise(dataset_id)
    found_table = _find_table(dataset, table)
    found_column = _find_column(found_table, column)

    target = _coerce_filter_value(value, found_column.dataType)
    rows = store.rows_by_table(dataset_id).get(found_table.id, [])
    matches = [row for row in rows if _matches(row.get(column), operator, target)]

    return {
        "table": found_table.name,
        "column": column,
        "operator": operator,
        "value": value,
        "totalMatches": len(matches),
        "returned": len(matches[:MAX_TOOL_ROWS]),
        "rows": matches[:MAX_TOOL_ROWS],
    }


def calcular_estatisticas(dataset_id: str, table: str, column: str) -> dict[str, Any]:
    """Estatísticas de uma coluna: numérica/moeda devolve
    count/sum/avg/min/max/nullCount; texto devolve distinctCount e os 5
    valores mais frequentes (topValues)."""
    dataset = _get_dataset_or_raise(dataset_id)
    found_table = _find_table(dataset, table)
    found_column = _find_column(found_table, column)

    rows = store.rows_by_table(dataset_id).get(found_table.id, [])
    raw_values = [row.get(column) for row in rows]
    values = [value for value in raw_values if value is not None]
    null_count = len(raw_values) - len(values)

    if found_column.dataType in ("number", "currency"):
        numeric = [value for value in values if isinstance(value, (int, float))]
        total = sum(numeric)
        return {
            "table": found_table.name,
            "column": column,
            "count": len(numeric),
            "nullCount": null_count,
            "sum": total,
            "avg": total / len(numeric) if numeric else None,
            "min": min(numeric) if numeric else None,
            "max": max(numeric) if numeric else None,
        }

    counts = Counter(str(value) for value in values)
    top_values = [{"value": value, "count": count} for value, count in counts.most_common(5)]
    return {
        "table": found_table.name,
        "column": column,
        "count": len(values),
        "nullCount": null_count,
        "distinctCount": len(counts),
        "topValues": top_values,
    }
```

- [ ] **Step 6: Rodar os testes de novo e confirmar que passam**

Run: `cd backend && .venv/Scripts/pytest tests/test_dataset_tools.py -v`
Expected: PASS — 15 testes verdes.

- [ ] **Step 7: Commit**

```bash
git add backend/services/dataset_service.py backend/tests/conftest.py backend/tests/test_dataset_tools.py backend/pytest.ini backend/requirements.txt
git commit -m "Add dataset query tools for the AI agent (listar_colunas, obter_resumo, buscar_registros, filtrar_dados, calcular_estatisticas)"
```

---

## Task 2: `GeminiAgentService` — loop de function calling

**Files:**
- Modify: `backend/services/agent_service.py` (reescrita completa — `MockAgentService` é removida)
- Create: `backend/tests/test_agent_service.py`
- Modify: `backend/requirements.txt`

**Interfaces:**
- Consumes (da Task 1): `DatasetToolError`, `listar_colunas`, `obter_resumo`, `buscar_registros`, `filtrar_dados`, `calcular_estatisticas` de `services.dataset_service`; fixture `stored_dataset_id` de `tests/conftest.py`.
- Consumes (já existentes): `AgentAnalyzeResponse`, `DatasetContext`, `ErrorQueryResult`, `TextQueryResult` de `schemas/models.py`.
- Produces: `class GeminiAgentService(AgentService)` com `analyze(question, dataset_context=None) -> AgentAnalyzeResponse` (assinatura idêntica à interface `AgentService` já usada por `routes/analyze.py` — nenhuma rota muda); `agent_service: AgentService = GeminiAgentService()` no fim do módulo, mesmo nome que `routes/analyze.py` já importa (`from services.agent_service import agent_service`).

- [ ] **Step 1: Adicionar `google-genai` ao `requirements.txt`**

`backend/requirements.txt` fica:

```text
fastapi>=0.115,<1.0
uvicorn[standard]>=0.30,<1.0
python-multipart>=0.0.9,<1.0
pytest>=8.0,<9.0
google-genai>=1.0,<2.0
```

```bash
cd backend && .venv/Scripts/pip install -r requirements.txt
```

- [ ] **Step 2: Escrever os testes em `backend/tests/test_agent_service.py` (vão falhar — `GeminiAgentService` ainda não existe)**

```python
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
```

- [ ] **Step 3: Rodar os testes e confirmar que falham**

Run: `cd backend && .venv/Scripts/pytest tests/test_agent_service.py -v`
Expected: FAIL — `ImportError: cannot import name 'GeminiAgentService' from 'services.agent_service'`

- [ ] **Step 4: Reescrever `backend/services/agent_service.py` por completo**

```python
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
```

- [ ] **Step 5: Rodar os testes e confirmar que passam**

Run: `cd backend && .venv/Scripts/pytest tests/test_agent_service.py -v`
Expected: PASS — 12 testes verdes.

- [ ] **Step 6: Rodar a suíte inteira (Task 1 + Task 2 juntas) para garantir que nada quebrou**

Run: `cd backend && .venv/Scripts/pytest -v`
Expected: PASS — 27 testes verdes no total.

- [ ] **Step 7: Commit**

```bash
git add backend/services/agent_service.py backend/tests/test_agent_service.py backend/requirements.txt
git commit -m "Replace MockAgentService with GeminiAgentService (real function-calling agent)"
```

---

## Task 3: Configuração, `.env`, docs e verificação manual de ponta a ponta

**Files:**
- Modify: `backend/main.py`
- Modify: `backend/requirements.txt`
- Create: `backend/.env.example`
- Modify: `backend/README.md`

**Interfaces:**
- Consumes: nada de código novo — só liga o que as Tasks 1 e 2 já produziram ao carregamento de `.env`.
- Produces: nada consumido por outra task (é a última).

- [ ] **Step 1: Adicionar `python-dotenv` ao `requirements.txt`**

`backend/requirements.txt` fica:

```text
fastapi>=0.115,<1.0
uvicorn[standard]>=0.30,<1.0
python-multipart>=0.0.9,<1.0
pytest>=8.0,<9.0
google-genai>=1.0,<2.0
python-dotenv>=1.0,<2.0
```

```bash
cd backend && .venv/Scripts/pip install -r requirements.txt
```

- [ ] **Step 2: Carregar `backend/.env` automaticamente em `backend/main.py`**

Trocar o topo do arquivo (linhas 10-19 atuais):

```python
from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routes import analyze, datasets, health
```

por:

```python
from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Precisa rodar antes do `from routes import ...` abaixo: routes.analyze já
# importa o GeminiAgentService, que lê GEMINI_MODEL do ambiente na
# construção do módulo.
load_dotenv()

from routes import analyze, datasets, health
```

- [ ] **Step 3: Criar `backend/.env.example`**

```text
# Copie este arquivo para backend/.env e preencha os valores antes de rodar
# `uvicorn main:app --reload`. Nunca coloque a chave direto no código.

# Chave da API Gemini (gere em https://aistudio.google.com/apikey).
# Obrigatória para /api/analyze e /api/datasets/{id}/questions.
GEMINI_API_KEY=

# Modelo Gemini usado pelo agente. Opcional — usa um Flash compatível com o
# free tier por padrão. Confira o nome exato disponível na sua conta em
# https://aistudio.google.com.
GEMINI_MODEL=gemini-3.6-flash

# Origens permitidas por CORS, separadas por vírgula. Opcional — já existia
# antes deste agente.
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

- [ ] **Step 4: Atualizar `backend/README.md`**

Substituir a seção final `## Agente de IA (mock)` por:

```markdown
## Agente de IA (Gemini)

`services/agent_service.py` define a interface `AgentService` (método `analyze`) e
`GeminiAgentService`, que usa a API Gemini (`google-genai`, Interactions API) com
function calling sobre 5 ferramentas de consulta implementadas em
`services/dataset_service.py`:

| Tool | Parâmetros | Devolve |
| --- | --- | --- |
| `listar_colunas` | `table?` | colunas (nome, tipo, descrição, nulos) de uma tabela ou de todas |
| `obter_resumo` | — | nome do dataset, tabelas, total de linhas/colunas, resumo |
| `buscar_registros` | `table, limit=10, offset=0` | amostra de linhas (máx. 50) |
| `filtrar_dados` | `table, column, operator, value` | linhas que batem o filtro (`=,!=,>,<,>=,<=,contains`) |
| `calcular_estatisticas` | `table, column` | numérico: count/sum/avg/min/max/nullCount · texto: distinct/top-values |

Fluxo: a pergunta vai para `client.interactions.create(...)`; se o modelo pedir uma
tool (`step.type == "function_call"`), o `GeminiAgentService` executa a função
correspondente em `dataset_service.py` e devolve o resultado via
`function_result`, repetindo até o modelo responder com texto (limite de 5
idas e voltas). O agente só responde com base no que as tools devolverem —
nunca usa conhecimento geral do modelo — e diz explicitamente quando a
pergunta não tem relação com os dados carregados.

Configuração (`backend/.env`, veja `.env.example`):

| Variável | Obrigatória | Padrão | Descrição |
| --- | --- | --- | --- |
| `GEMINI_API_KEY` | sim | — | chave da API Gemini |
| `GEMINI_MODEL` | não | `gemini-3.6-flash` | modelo Flash usado pelo agente |

Erros (chave ausente, dataset não carregado, limite de uso, falha de
comunicação, ferramenta inexistente, erro de execução de ferramenta,
resposta inválida do modelo) nunca geram uma exceção HTTP nova: viram um
`QueryResult` do tipo `error`, no mesmo formato que qualquer outra resposta
de pergunta — sem stack trace nem detalhe interno exposto ao front-end.

Rotas e outros serviços só conhecem a interface `AgentService` — trocar a
implementação (outro provedor de LLM, por exemplo) é apontar a variável
`agent_service` para uma nova classe, sem tocar nas rotas.

## Testes

```bash
cd backend
.venv\Scripts\pytest -v
```
```

- [ ] **Step 5: Gerar um ZIP de teste mínimo**

Criar um script local (não versionado) só para o teste manual:

```bash
cd backend
python -c "
import zipfile
with zipfile.ZipFile('sample.zip', 'w') as zf:
    zf.writestr('fornecedores.csv', 'id_fornecedor,razao_social,valor_total\n1,Alfa Ltda,100.00\n2,Beta SA,250.50\n3,Alfa Filial,\n')
"
```

- [ ] **Step 6: Rodar o servidor com a chave real e verificar de ponta a ponta**

Peça ao usuário a `GEMINI_API_KEY` (ele vai gerar em https://aistudio.google.com/apikey)
antes deste passo; coloque em `backend/.env` (nunca no código nem em texto
plano fora do `.env`, que já está no `.gitignore` da raiz do projeto).

```bash
cd backend && .venv/Scripts/uvicorn main:app --reload
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
- a primeira pergunta devolve `data.type == "text"` com um valor que bate com
  os dados do `sample.zip` (soma de 100.00 + 250.50 = 350.50, ignorando a
  linha vazia);
- a segunda pergunta **não inventa uma resposta sobre futebol** — devolve
  texto dizendo que o dataset não tem esse assunto, mencionando as tabelas
  reais (`fornecedores`);
- os logs do `uvicorn --reload` não mostram nenhuma chave ou stack trace
  vazando na resposta HTTP (só no console do servidor, se algo falhar).

Depois de confirmar, apagar o `sample.zip` de teste (não deve ser commitado):

```bash
rm backend/sample.zip
```

- [ ] **Step 7: Commit**

```bash
git add backend/main.py backend/requirements.txt backend/.env.example backend/README.md
git commit -m "Wire up .env loading, docs and manual verification for the Gemini agent"
```
