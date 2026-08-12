"""Schemas Pydantic que espelham os tipos usados pelo front-end.

Fonte de verdade: `src/types/dataset.ts`, `src/types/query.ts`,
`src/types/message.ts` e `src/types/api.ts`. Os nomes de campo usam
camelCase de propósito, para que o JSON produzido bata exatamente com o
que `src/services/apiDataService.ts` já espera (nenhuma tradução é feita
no front-end).
"""

from __future__ import annotations

from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, Field

# --- dataset.ts -------------------------------------------------------

DatasetStatus = Literal["processing", "ready", "error"]

DatasetColumnType = Literal["string", "number", "date", "boolean", "currency", "unknown"]


class DatasetColumn(BaseModel):
    name: str
    label: str | None = None
    dataType: DatasetColumnType
    description: str | None = None
    nullable: bool
    nullCount: int | None = None


class DatasetTable(BaseModel):
    id: str
    name: str
    fileName: str
    description: str | None = None
    rowCount: int
    columnCount: int
    columns: list[DatasetColumn]
    preview: list[dict[str, Any]]


class Dataset(BaseModel):
    id: str
    name: str
    uploadedAt: str
    status: DatasetStatus
    totalRows: int
    totalColumns: int
    tables: list[DatasetTable]
    sourceFileName: str | None = None
    sourceFileSize: int | None = None
    dictionaryFileName: str | None = None
    summary: str | None = None


# --- query.ts -----------------------------------------------------------

ChartType = Literal["bar", "line", "pie", "area"]


class ChartSpec(BaseModel):
    type: ChartType
    title: str
    xKey: str
    yKey: str
    data: list[dict[str, Any]]
    yLabel: str | None = None
    valueFormat: Literal["number", "currency"] | None = None
    highlightKey: str | None = None
    caption: str | None = None


class TableColumnSpec(BaseModel):
    key: str
    label: str
    dataType: Literal["string", "number", "currency", "date"] | None = None
    align: Literal["left", "right"] | None = None


class TextQueryResult(BaseModel):
    type: Literal["text"] = "text"
    answer: str
    detail: str | None = None


class TableQueryResult(BaseModel):
    type: Literal["table"] = "table"
    answer: str | None = None
    title: str | None = None
    columns: list[TableColumnSpec]
    rows: list[dict[str, Any]]


class ChartQueryResult(BaseModel):
    type: Literal["chart"] = "chart"
    answer: str | None = None
    chart: ChartSpec


class CombinedTable(BaseModel):
    answer: str | None = None
    title: str | None = None
    columns: list[TableColumnSpec]
    rows: list[dict[str, Any]]


class CombinedChart(BaseModel):
    answer: str | None = None
    chart: ChartSpec


class CombinedQueryResult(BaseModel):
    type: Literal["combined"] = "combined"
    answer: str
    table: CombinedTable | None = None
    chart: CombinedChart | None = None


class ErrorQueryResult(BaseModel):
    type: Literal["error"] = "error"
    title: str
    message: str
    suggestion: str | None = None


QueryResult = (
    TextQueryResult | TableQueryResult | ChartQueryResult | CombinedQueryResult | ErrorQueryResult
)


# --- message.ts -----------------------------------------------------------

ChatRole = Literal["user", "assistant", "system"]
ChatMessageStatus = Literal["sending", "processing", "complete", "error"]


class ChatMessage(BaseModel):
    id: str
    role: ChatRole
    content: str
    createdAt: str
    status: ChatMessageStatus | None = None
    result: QueryResult | None = None
    question: str | None = None
    durationMs: int | None = None


# --- api.ts -----------------------------------------------------------

T = TypeVar("T")


class ApiEnvelope(BaseModel, Generic[T]):
    """Envelope padrão das respostas de sucesso.

    `status` é redundante para o front-end atual (`apiDataService.ts` só lê
    `data`), mas mantém compatibilidade com o formato `{status, data}`
    também descrito nos requisitos do backend.
    """

    status: Literal["success"] = "success"
    data: T
    message: str | None = None


class AskQuestionRequest(BaseModel):
    question: str = Field(min_length=1)


class AnalyzeRequest(BaseModel):
    """Corpo do endpoint genérico `POST /analyze` (fora do path de um dataset)."""

    datasetId: str
    question: str = Field(min_length=1)


# --- agente (interno, não é o contrato HTTP) ---------------------------


class DatasetContext(BaseModel):
    """Resumo do dataset repassado ao AgentService — não expõe as linhas
    inteiras, só o suficiente para o agente (mock ou real) se orientar."""

    datasetId: str
    datasetName: str
    tables: list[str]
    totalRows: int
    totalColumns: int


class AgentAnalyzeResponse(BaseModel):
    """Retorno da interface pública do `AgentService`. Não é o contrato
    HTTP: as rotas extraem `result` e o embrulham em `ApiEnvelope`."""

    status: Literal["success", "error"] = "success"
    source: str
    result: QueryResult
