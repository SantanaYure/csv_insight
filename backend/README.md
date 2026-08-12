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

## Agente de IA (Gemini)

`services/agent_service.py` define a interface `AgentService` (método `analyze`) e
`GeminiAgentService`, que usa a API Gemini (`google-genai`, Interactions API) com
function calling sobre 5 ferramentas de consulta implementadas em
`services/dataset_service.py`:

| Tool | Parâmetros | Devolve |
| --- | --- | --- |
| `listar_colunas` | `table?` | colunas (nome, tipo, descrição, nulos) de uma tabela ou de todas |
| `obter_resumo` | — | nome do dataset, tabelas, total de linhas/colunas, resumo |
| `buscar_registros` | `table, limit=10, offset=0` | amostra de linhas (máx. 50) |
| `filtrar_dados` | `table, column, operator, value` | linhas que batem o filtro (`=,!=,>,<,>=,<=,contains`) |
| `calcular_estatisticas` | `table, column` | numérico: count/sum/avg/min/max/nullCount · texto: distinct/top-values |

Fluxo: a pergunta vai para `client.interactions.create(...)`; se o modelo pedir uma
tool (`step.type == "function_call"`), o `GeminiAgentService` executa a função
correspondente em `dataset_service.py` e devolve o resultado via
`function_result`, repetindo até o modelo responder com texto (limite de 5
idas e voltas). O agente só responde com base no que as tools devolverem —
nunca usa conhecimento geral do modelo — e diz explicitamente quando a
pergunta não tem relação com os dados carregados.

Configuração (`backend/.env`, veja `.env.example`):

| Variável | Obrigatória | Padrão | Descrição |
| --- | --- | --- | --- |
| `GEMINI_API_KEY` | sim | — | chave da API Gemini |
| `GEMINI_MODEL` | não | `gemini-3.6-flash` | modelo Flash usado pelo agente |

Erros (chave ausente, dataset não carregado, limite de uso, falha de
comunicação, ferramenta inexistente, erro de execução de ferramenta,
resposta inválida do modelo) nunca geram uma exceção HTTP nova: viram um
`QueryResult` do tipo `error`, no mesmo formato que qualquer outra resposta
de pergunta — sem stack trace nem detalhe interno exposto ao front-end.

Rotas e outros serviços só conhecem a interface `AgentService` — trocar a
implementação (outro provedor de LLM, por exemplo) é apontar a variável
`agent_service` para uma nova classe, sem tocar nas rotas.

## Testes

```bash
cd backend
.venv\Scripts\pytest -v
```
