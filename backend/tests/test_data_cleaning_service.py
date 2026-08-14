from __future__ import annotations

import io
import zipfile

import pandas as pd

import services.dataset_service as dataset_service
from services.data_cleaning_service import DataCleaningService
from services.dataset_service import ingest_file, ingest_zip


def test_clean_removes_only_structural_noise_and_reports_nulls():
    frame = pd.DataFrame(
        {
            " Nome  ": [" Ana ", "Ana", "  ", None],
            "valor": ["1,50", "1,50", "2,50", None],
            "vazio": ["", "", "", ""],
        }
    )

    result = DataCleaningService().clean(frame)

    assert list(result.dataframe.columns) == ["Nome", "valor"]
    assert result.dataframe.to_dict(orient="records") == [
        {"Nome": "Ana", "valor": 1.5},
        {"Nome": None, "valor": 2.5},
    ]
    assert result.report.original_rows == 4
    assert result.report.final_rows == 2
    assert result.report.empty_rows_removed == 1
    assert result.report.duplicates_removed == 1
    assert result.report.removed_columns == ["vazio"]
    assert result.report.null_values == {"Nome": 1, "valor": 0}
    assert result.report.converted_numeric_columns == ["valor"]


def test_clean_normalizes_clear_dates_but_preserves_inconsistent_columns():
    frame = pd.DataFrame(
        {
            "data": ["01/02/2026", "2026-03-04"],
            "misturada": ["10", "indisponivel"],
            "categoria": ["A", "B"],
        }
    )

    result = DataCleaningService().clean(frame)

    assert result.dataframe["data"].tolist() == ["2026-02-01", "2026-03-04"]
    assert result.report.detected_types == {
        "data": "date",
        "misturada": "mixed",
        "categoria": "string",
    }
    assert result.report.inconsistent_columns == {"misturada": ["number", "string"]}
    assert result.report.normalized_date_columns == ["data"]
    assert result.report.converted_numeric_columns == []
    assert result.dataframe["misturada"].tolist() == ["10", "indisponivel"]


def test_ingest_applies_cleaning_before_building_dataset_and_store_rows():
    csv_content = (
        " Cliente  ; valor ; data; coluna_vazia\n"
        " Ana ; 1,50 ; 01/02/2026;\n"
        "Ana;1,50;01/02/2026;\n"
        "Bruno; 2,50 ; 03/02/2026;\n"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("clientes.csv", csv_content)

    ingested = ingest_zip("dados.zip", len(buffer.getvalue()), buffer.getvalue())

    report = ingested.dataset.cleaningReport["clientes"]
    assert report.originalRows == 3
    assert report.finalRows == 2
    assert report.duplicatesRemoved == 1
    assert report.removedColumns == ["coluna_vazia"]
    assert ingested.dataset.tables[0].rowCount == 2
    assert ingested.rows["clientes"][0]["Cliente"] == "Ana"
    assert ingested.rows["clientes"][0]["valor"] == 1.5
    assert ingested.rows["clientes"][0]["data"] == "2026-02-01"


def test_ingest_file_accepts_a_standalone_csv_with_arbitrary_columns():
    csv_content = (
        "Produto;Quantidade;Preço unitário\n"
        "Café;2;12,50\n"
        "Caderno;3;8,00\n"
    ).encode("utf-8")

    ingested = ingest_file("vendas.CSV", len(csv_content), csv_content)

    assert ingested.dataset.name == "Vendas"
    assert [column.name for column in ingested.dataset.tables[0].columns] == [
        "Produto",
        "Quantidade",
        "Preço unitário",
    ]
    assert ingested.dataset.tables[0].rowCount == 2
    assert ingested.rows["vendas"][0] == {
        "Produto": "Café",
        "Quantidade": 2.0,
        "Preço unitário": 12.5,
    }


def test_large_zip_path_streams_and_cleans_csv(monkeypatch):
    csv_content = (
        " Cliente ; valor ; data; vazia\n"
        " Ana ; 1,50 ; 01/02/2026;\n"
        "Ana;1,50;01/02/2026;\n"
        "Bruno; 2,50 ; 03/02/2026;\n"
    ).encode("windows-1252")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("clientes.csv", csv_content)

    monkeypatch.setattr(dataset_service, "STREAMING_ENTRY_BYTES", 1)
    monkeypatch.setattr(dataset_service, "STREAMING_TOTAL_BYTES", 1)
    ingested = ingest_zip("dados.zip", len(buffer.getvalue()), buffer.getvalue())

    table = ingested.dataset.tables[0]
    report = ingested.dataset.cleaningReport["clientes"]
    assert table.rowCount == 2
    assert [column.name for column in table.columns] == ["Cliente", "valor", "data"]
    assert report.duplicatesRemoved == 1
    assert report.removedColumns == ["vazia"]
    assert ingested.rows["clientes"] == [
        {"Cliente": "Ana", "valor": 1.5, "data": "2026-02-01"},
        {"Cliente": "Bruno", "valor": 2.5, "data": "2026-02-03"},
    ]
