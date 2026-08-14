from __future__ import annotations

import pytest

from schemas.models import Dataset, DatasetColumn, DatasetTable
from services.dataset_service import (
    DatasetToolError,
    _bounded_tool_rows,
    buscar_registros,
    calcular_estatisticas,
    filtrar_dados,
    listar_colunas,
    obter_resumo,
    store,
)


def test_tool_rows_are_bounded_for_llm_context():
    rows = [{"id": str(index), "description": "x" * 1_000} for index in range(20)]

    bounded, truncated = _bounded_tool_rows(rows)

    assert truncated is True
    assert len(bounded) <= 10
    assert len(str(bounded)) < 10_000


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


def test_calcular_estatisticas_numeric_column_reports_non_numeric_values():
    # Coluna tipada number/currency, mas com uma linha cujo valor bruto não é
    # numérico (ex.: "N/A" que passou pela inferência de tipo e por
    # `coerce_value` sem ser convertido, ou veio de um dicionário de dados
    # que declarou o tipo diretamente). `calcular_estatisticas` não deve
    # descartar esse valor silenciosamente: precisa contá-lo em
    # `nonNumericCount`.
    dataset_id = "ds-test-nonnumeric"
    columns = [
        DatasetColumn(name="id", dataType="string", nullable=False, nullCount=0),
        DatasetColumn(name="valor", dataType="number", nullable=False, nullCount=0),
    ]
    table = DatasetTable(
        id="dados",
        name="dados",
        fileName="dados.csv",
        description="id e mais 1 colunas.",
        rowCount=3,
        columnCount=len(columns),
        columns=columns,
        preview=[],
    )
    dataset = Dataset(
        id=dataset_id,
        name="Dataset com valor sujo",
        uploadedAt="2026-08-12T00:00:00Z",
        status="ready",
        totalRows=3,
        totalColumns=len(columns),
        tables=[table],
        summary="Foram lidas 1 tabelas (dados), somando 2 colunas.",
    )
    rows = [
        {"id": "1", "valor": 100.0},
        {"id": "2", "valor": 200.0},
        {"id": "3", "valor": "N/A"},
    ]
    store.save(dataset, {"dados": rows})

    result = calcular_estatisticas(dataset_id, table="dados", column="valor")

    assert result["nonNumericCount"] == 1
    assert result["count"] == 2
    assert result["sum"] == pytest.approx(300.0)
    assert result["avg"] == pytest.approx(150.0)


def test_filtrar_dados_date_column_compares_chronologically_not_lexicographically():
    # "05/01/2026" (5 jan) e "15/07/2026" (15 jul) comparados com
    # ">01/06/2026" (1 jun): cronologicamente só a segunda linha é depois de
    # 1 jun/2026, mas como string "05/01/2026" > "01/06/2026" também é
    # verdadeiro (comparação lexicográfica), o que provaria o bug se a
    # coluna não fosse normalizada antes de comparar.
    dataset_id = "ds-test-dates"
    columns = [
        DatasetColumn(name="id", dataType="string", nullable=False, nullCount=0),
        DatasetColumn(name="data_emissao", dataType="date", nullable=False, nullCount=0),
    ]
    table = DatasetTable(
        id="notas",
        name="notas",
        fileName="notas.csv",
        description="id e mais 1 colunas.",
        rowCount=2,
        columnCount=len(columns),
        columns=columns,
        preview=[],
    )
    dataset = Dataset(
        id=dataset_id,
        name="Dataset de notas",
        uploadedAt="2026-08-12T00:00:00Z",
        status="ready",
        totalRows=2,
        totalColumns=len(columns),
        tables=[table],
        summary="Foram lidas 1 tabelas (notas), somando 2 colunas.",
    )
    rows = [
        {"id": "1", "data_emissao": "05/01/2026"},
        {"id": "2", "data_emissao": "15/07/2026"},
    ]
    store.save(dataset, {"notas": rows})

    result = filtrar_dados(
        dataset_id,
        table="notas",
        column="data_emissao",
        operator=">",
        value="01/06/2026",
    )

    assert result["totalMatches"] == 1
    assert result["rows"][0]["id"] == "2"
