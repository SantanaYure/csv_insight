"""Endpoint de análise/pergunta sobre um dataset.

Canônico (usado por `apiDataService.ts`): `POST /api/datasets/{id}/questions`.
`POST /api/analyze` é um alias genérico (dataset_id no corpo) pedido
explicitamente na especificação do backend; internamente chama a mesma
lógica. Ambos delegam a análise em si para `AgentService` — esta rota só
conhece a interface pública (`analyze_service.analyze`), nunca a
implementação mock.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from schemas.models import (
    AgentAnalyzeResponse,
    AnalyzeRequest,
    ApiEnvelope,
    AskQuestionRequest,
    ChatMessage,
    DatasetContext,
    QueryResult,
)
from services.agent_service import agent_service
from services.dataset_service import generate_id, store

router = APIRouter(tags=["analyze"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _build_context(dataset_id: str) -> DatasetContext | None:
    dataset = store.get_dataset(dataset_id)
    if dataset is None:
        return None
    return DatasetContext(
        datasetId=dataset.id,
        datasetName=dataset.name,
        tables=[table.name for table in dataset.tables],
        totalRows=dataset.totalRows,
        totalColumns=dataset.totalColumns,
    )


def _ask(dataset_id: str, question: str) -> QueryResult:
    if not store.has(dataset_id):
        raise HTTPException(status_code=404, detail="Conjunto de dados não encontrado.")

    context = _build_context(dataset_id)
    started = time.perf_counter()
    agent_response: AgentAnalyzeResponse = agent_service.analyze(question, dataset_context=context)
    duration_ms = int((time.perf_counter() - started) * 1000)

    result = agent_response.result
    message = ChatMessage(
        id=generate_id("history"),
        role="assistant",
        content=question,
        question=question,
        createdAt=_now_iso(),
        status="error" if result.type == "error" else "complete",
        durationMs=duration_ms,
        result=result,
    )
    store.add_history(dataset_id, message)
    return result


@router.post("/datasets/{dataset_id}/questions", response_model=ApiEnvelope[QueryResult])
def ask_question(dataset_id: str, payload: AskQuestionRequest) -> ApiEnvelope[QueryResult]:
    result = _ask(dataset_id, payload.question)
    return ApiEnvelope(data=result)


@router.post("/analyze", response_model=ApiEnvelope[QueryResult])
def analyze(payload: AnalyzeRequest) -> ApiEnvelope[QueryResult]:
    result = _ask(payload.datasetId, payload.question)
    return ApiEnvelope(data=result)
