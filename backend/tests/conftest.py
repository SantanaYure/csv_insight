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
