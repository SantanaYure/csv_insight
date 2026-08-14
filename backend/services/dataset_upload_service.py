"""Caso de uso de upload de datasets.

Mantém validação, limite de leitura e persistência fora da camada HTTP. A rota
conhece somente este serviço e traduz erros de aplicação para respostas HTTP.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from schemas.models import Dataset
from services.dataset_service import (
    DatasetIngestionError,
    IngestedDataset,
    ingest_file,
    store,
)

MAX_UPLOAD_BYTES = 200 * 1024 * 1024
READ_CHUNK_BYTES = 1024 * 1024


class UploadSource(Protocol):
    filename: str | None

    async def read(self, size: int = -1) -> bytes: ...

    async def close(self) -> None: ...


class DatasetRepository(Protocol):
    def save(self, dataset: Dataset, rows: dict) -> None: ...


class UploadRejectedError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


class DatasetUploadService:
    def __init__(
        self,
        repository: DatasetRepository,
        ingestor: Callable[[str, int, bytes], IngestedDataset] = ingest_file,
        max_upload_bytes: int = MAX_UPLOAD_BYTES,
    ) -> None:
        self._repository = repository
        self._ingestor = ingestor
        self._max_upload_bytes = max_upload_bytes

    async def upload(self, source: UploadSource) -> Dataset:
        try:
            file_name = (source.filename or "").strip()
            if not file_name:
                raise UploadRejectedError("Nenhum arquivo enviado.")
            if not file_name.lower().endswith((".csv", ".zip")):
                raise UploadRejectedError("Envie um arquivo .csv ou .zip.")

            content = await self._read_with_limit(source)
            try:
                ingested = self._ingestor(file_name, len(content), content)
            except DatasetIngestionError as exc:
                raise UploadRejectedError(str(exc)) from exc

            self._repository.save(ingested.dataset, ingested.rows)
            return ingested.dataset
        finally:
            await source.close()

    async def _read_with_limit(self, source: UploadSource) -> bytes:
        content = bytearray()
        while chunk := await source.read(READ_CHUNK_BYTES):
            content.extend(chunk)
            if len(content) > self._max_upload_bytes:
                raise UploadRejectedError(
                    "Arquivo excede o tamanho máximo de 200 MB.", status_code=413
                )
        return bytes(content)


dataset_upload_service = DatasetUploadService(store)
