# CSV Insight — Backend (FastAPI)

API FastAPI para ingestão de CSVs ou ZIPs com CSVs e análise dos datasets em linguagem
natural. O processamento do ZIP/CSV e as regras de negócio permanecem no
`DatasetService`; o agente usa Pydantic AI com Groq e GPT-OSS.

## Estrutura

```
backend/
├── main.py
├── routes/
│   ├── health.py
│   ├── datasets.py
│   └── analyze.py
├── agents/
│   └── data_agent.py       Agent Pydantic AI e tools tipadas
├── services/
│   ├── data_cleaning_service.py limpeza conservadora e relatórios
│   ├── dataset_service.py  ingestão, limpeza, store em memória e consultas
│   └── agent_service.py    interface HTTP-facing e tratamento de erros
└── schemas/models.py
```

## Executar

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload
```

Preencha `GROQ_API_KEY` no `.env`. O modelo é configurável por
`GROQ_MODEL=openai/gpt-oss-20b`.

## Endpoints

O caso de uso de upload fica em `services/dataset_upload_service.py`: ele valida
a extensão, lê o corpo em blocos de 1 MB, interrompe arquivos acima de 200 MB e
persiste o dataset. As rotas HTTP apenas traduzem o resultado para o contrato da API.

| Método | Endpoint | Descrição |
| --- | --- | --- |
| `GET` | `/health` | Status da API. |
| `POST` | `/api/datasets` | Upload de CSV ou ZIP (`multipart/form-data`, campo `file`). |
| `POST` | `/api/datasets/upload` | Alias compatível do upload. |
| `GET` | `/api/datasets/{dataset_id}` | Retorna o dataset processado. |
| `GET` | `/api/datasets/{dataset_id}/history` | Histórico de perguntas/respostas. |
| `DELETE` | `/api/datasets/{dataset_id}/history/{message_id}` | Remove um item do histórico. |
| `POST` | `/api/datasets/{dataset_id}/questions` | Analisa uma pergunta sobre o dataset. |
| `POST` | `/api/analyze` | Alias genérico com `{ "datasetId", "question" }`. |

As respostas de sucesso mantêm o envelope `{ "status": "success", "data": ... }`
usado pelo front-end.

## Agente Pydantic AI + Groq

`services/agent_service.py` mantém o contrato público `AgentService.analyze` e
cria um `GroqModel` para o modelo de `GROQ_MODEL`. O `agents/data_agent.py`
declara um `Agent[DatasetAgentDeps, str]`, recebe o `DatasetService` por
dependência e usa `run_sync`; o Pydantic AI controla as iterações de tool
calling e não há loop manual de function calling no projeto.

Tools disponíveis:

| Tool | Parâmetros | Devolve |
| --- | --- | --- |
| `listar_colunas` | `table?` | Colunas, tipos, descrições e nulos. |
| `obter_resumo` | — | Nome, tabelas e totais do dataset. |
| `buscar_registros` | `table, limit=10, offset=0` | Amostra paginada, máximo de 10 linhas compactadas. |
| `filtrar_dados` | `table, column, operator, value` | Linhas que atendem ao filtro. |
| `calcular_estatisticas` | `table, column` | Estatísticas numéricas ou frequências de texto. |

As tools apenas delegam ao `DatasetService`, nunca recebem o ZIP bruto e não
enviam o dataset inteiro automaticamente. As linhas retornadas para a LLM são
limitadas a 10 registros e aproximadamente 7.000 caracteres; quando há mais
dados, a resposta informa que existe conteúdo adicional para evitar estourar
o limite de tokens da Groq.

Erros de chave ausente, dataset ausente, rate limit, timeout, falha de
comunicação, falha de tool e resposta inválida viram `ErrorQueryResult` sem
stack trace no contrato HTTP.

## Exemplo de chamada

```bash
curl -X POST http://localhost:8000/api/datasets/DS_ID/questions `
  -H "Content-Type: application/json" `
  -d '{"question":"Qual é o total de linhas?"}'
```

Resposta esperada:

```json
{
  "status": "success",
  "data": {
    "type": "text",
    "answer": "..."
  }
}
```

## Testes

```bash
cd backend
.venv\Scripts\pytest -v
```

Os testes unitários usam um agente fake para validar o contrato do serviço e
um dataset em memória para validar as tools sem fazer chamadas reais à Groq.
