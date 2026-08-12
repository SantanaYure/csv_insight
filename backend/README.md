# CSV Insight — Backend (FastAPI)

API que substitui os mocks descritos em [`../src/services/mockDataService.ts`](../src/services/mockDataService.ts),
reaproveitando as regras de ingestão de ZIP/CSV e os contratos já definidos no front-end
(`src/types`) como fonte de verdade.

## Estrutura

```
backend/
├── main.py                  App FastAPI, CORS, tratamento de erros, /docs
├── routes/
│   ├── health.py             GET /health
│   ├── datasets.py           POST /api/datasets, GET/DELETE de dataset e histórico
│   └── analyze.py            POST /api/datasets/{id}/questions, POST /api/analyze
├── services/
│   ├── dataset_service.py    Ingestão do ZIP (porta de src/services/ingestion/*) + store em memória
│   └── agent_service.py      Interface AgentService + implementação mockada
├── schemas/
│   └── models.py              Schemas Pydantic espelhando src/types/*.ts
└── requirements.txt
```

## Executar

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows (PowerShell: .venv\Scripts\Activate.ps1)
pip install -r requirements.txt
uvicorn main:app --reload
```

A API sobe em `http://localhost:8000`. Documentação interativa em `http://localhost:8000/docs`.

## Endpoints

| Método | Endpoint | Descrição |
| --- | --- | --- |
| `GET` | `/health` | Status da API. |
| `POST` | `/api/datasets` | Upload do ZIP (`multipart/form-data`, campo `file`). Contrato canônico usado por `apiDataService.ts`. |
| `POST` | `/api/datasets/upload` | Alias do endpoint acima (mesmo handler), para compatibilidade literal com a especificação. |
| `GET` | `/api/datasets/{dataset_id}` | Retorna o dataset processado. |
| `GET` | `/api/datasets/{dataset_id}/history` | Histórico de perguntas/respostas do dataset. |
| `DELETE` | `/api/datasets/{dataset_id}/history/{message_id}` | Remove um item do histórico. |
| `POST` | `/api/datasets/{dataset_id}/questions` | Faz uma pergunta sobre o dataset (contrato canônico). |
| `POST` | `/api/analyze` | Alias genérico de `.../questions`, recebendo `{ "datasetId", "question" }` no corpo. |

Todas as respostas de sucesso seguem `{ "status": "success", "data": ... }`; erros seguem
`{ "status": "error", "message": "...", "detail": "..." }` (o campo `detail` é o que
`apiDataService.ts` já sabe interpretar).

## Armazenamento

Não há banco de dados: os datasets ficam em memória, no processo do backend (equivalente ao
`datasetStore.ts` do front-end, que guarda os dados na sessão do navegador). O ZIP nunca é escrito
em disco — é lido inteiramente em memória com `zipfile`, o que elimina path traversal por
construção; mesmo assim, nomes de entrada com `..` ou caminho absoluto são descartados, e há
limites de tamanho (200 MB descomprimido no total, 40 arquivos CSV) para mitigar zip bombs.

## Agente de IA (mock)

`services/agent_service.py` define a interface `AgentService` (método `analyze`) e uma
implementação mockada, `MockAgentService`, que devolve respostas previsíveis sem chamar nenhum
modelo. Rotas e outros serviços só conhecem a interface — trocar o mock por um agente real é
implementar uma nova classe e apontar a variável `agent_service` para ela, sem tocar nas rotas.
