"""Backend FastAPI do CSV Insight.

Substitui progressivamente os mocks descritos em `frontend/src/services/mockDataService.ts`
pelo contrato HTTP que `frontend/src/services/apiDataService.ts` já implementa (ver
README, seção "Integração futura com FastAPI"). Rodar com:

    uvicorn main:app --reload
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Precisa rodar antes do `from routes import ...` abaixo: a rota de análise
# importa o AgentService, que lê GROQ_MODEL quando o agente é construído.
load_dotenv()

from routes import analyze, datasets, health

DEFAULT_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
DEFAULT_ORIGIN_REGEX = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", DEFAULT_ORIGINS).split(",")
    if origin.strip()
]

app = FastAPI(
    title="CSV Insight API",
    description="Ingestão de CSVs ou ZIPs com CSVs e análise em linguagem natural.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=os.getenv("CORS_ORIGIN_REGEX", DEFAULT_ORIGIN_REGEX),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _error_body(message: str) -> dict[str, str]:
    # `status`/`message` seguem o formato pedido na especificação; `detail`
    # é o que `frontend/src/types/api.ts` já sabe ler no
    # front-end (`payload.detail ?? payload.message`).
    return {"status": "error", "message": message, "detail": message}


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(status_code=exc.status_code, content=_error_body(message))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    first_error = exc.errors()[0] if exc.errors() else None
    message = first_error["msg"] if first_error else "Requisição inválida."
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=_error_body(message)
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_body("Erro interno inesperado."),
    )


app.include_router(health.router)
app.include_router(datasets.router, prefix="/api")
app.include_router(analyze.router, prefix="/api")
