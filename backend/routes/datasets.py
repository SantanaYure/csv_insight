"""Endpoints de dataset.

O contrato canônico é o que `src/services/apiDataService.ts` e o README
("Integração futura com FastAPI") já documentam:

    POST   /api/datasets                          multipart `file`
    GET    /api/datasets/{dataset_id}
    GET    /api/datasets/{dataset_id}/history
    DELETE /api/datasets/{dataset_id}/history/{message_id}

`POST /api/datasets/upload` é mantido como alias do primeiro (mesmo
handler) só para atender literalmente ao endpoint pedido na especificação;
o front-end atual nunca chama essa rota.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.responses import Response

from schemas.models import ApiEnvelope, ChatMessage, Dataset
from services.dataset_service import DatasetIngestionError, ingest_zip, store

router = APIRouter(prefix="/datasets", tags=["datasets"])

MAX_UPLOAD_BYTES = 200 * 1024 * 1024


async def _handle_upload(file: UploadFile) -> ApiEnvelope[Dataset]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado.")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo excede o tamanho máximo de 200 MB.")

    try:
        ingested = ingest_zip(file.filename, len(content), content)
    except DatasetIngestionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    store.save(ingested.dataset, ingested.rows)
    return ApiEnvelope(data=ingested.dataset)


@router.post("", response_model=ApiEnvelope[Dataset], status_code=status.HTTP_201_CREATED)
async def upload_dataset(file: UploadFile) -> ApiEnvelope[Dataset]:
    return await _handle_upload(file)


@router.post(
    "/upload", response_model=ApiEnvelope[Dataset], status_code=status.HTTP_201_CREATED
)
async def upload_dataset_alias(file: UploadFile) -> ApiEnvelope[Dataset]:
    return await _handle_upload(file)


@router.get("/{dataset_id}", response_model=ApiEnvelope[Dataset])
def get_dataset(dataset_id: str) -> ApiEnvelope[Dataset]:
    dataset = store.get_dataset(dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Conjunto de dados não encontrado.")
    return ApiEnvelope(data=dataset)


@router.get("/{dataset_id}/history", response_model=ApiEnvelope[list[ChatMessage]])
def get_history(dataset_id: str) -> ApiEnvelope[list[ChatMessage]]:
    if not store.has(dataset_id):
        raise HTTPException(status_code=404, detail="Conjunto de dados não encontrado.")
    return ApiEnvelope(data=store.history(dataset_id))


@router.delete("/{dataset_id}/history/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_history_item(dataset_id: str, message_id: str) -> Response:
    if not store.has(dataset_id):
        raise HTTPException(status_code=404, detail="Conjunto de dados não encontrado.")
    store.remove_history(dataset_id, message_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
