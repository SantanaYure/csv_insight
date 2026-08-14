from __future__ import annotations

import asyncio
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from starlette.datastructures import UploadFile

from services.dataset_service import IngestedDataset
from services.dataset_upload_service import DatasetUploadService, UploadRejectedError


def test_upload_csv_endpoint_accepts_multipart_file():
    import main

    response = TestClient(main.app).post(
        "/api/datasets",
        files={"file": ("vendas.csv", b"produto,valor\nCaderno,12.50\n", "text/csv")},
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["sourceFileName"] == "vendas.csv"
    assert payload["totalRows"] == 1
    assert payload["tables"][0]["columns"][0]["name"] == "produto"


def test_upload_endpoint_rejects_unsupported_extension():
    import main

    response = TestClient(main.app).post(
        "/api/datasets",
        files={"file": ("vendas.txt", b"produto,valor\nCaderno,12.50\n", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Envie um arquivo .csv ou .zip."


def test_upload_preflight_accepts_alternative_vite_port():
    import main

    response = TestClient(main.app).options(
        "/api/datasets",
        headers={
            "Origin": "http://localhost:5174",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5174"


def test_upload_service_stops_reading_after_configured_limit():
    class RepositorySpy:
        def save(self, dataset, rows):  # pragma: no cover - não deve ser chamado
            raise AssertionError("save não deveria ser chamado")

    def ingestor_spy(*_args) -> IngestedDataset:  # pragma: no cover
        raise AssertionError("ingestor não deveria ser chamado")

    service = DatasetUploadService(RepositorySpy(), ingestor_spy, max_upload_bytes=5)
    source = UploadFile(BytesIO(b"123456"), filename="grande.csv")

    with pytest.raises(UploadRejectedError) as captured:
        asyncio.run(service.upload(source))

    assert captured.value.status_code == 413
