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
