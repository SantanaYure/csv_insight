# Agente de IA real (Gemini) no `AgentService`

Data: 2026-08-12

## Objetivo

Substituir `MockAgentService` por uma implementação real usando a API Gemini
(`google-genai`), mantendo intacta a interface `AgentService` (`analyze`) e o
contrato HTTP já consumido pelo front-end (`POST /api/datasets/{id}/questions`
e `POST /api/analyze`).

## Arquitetura

```
routes/analyze.py  (inalterado)
        ↓
services/agent_service.py
  AgentService (interface, inalterada)
  GeminiAgentService  ← substitui MockAgentService (removida)
        ↓ function calling
services/dataset_service.py
  + listar_colunas / obter_resumo / buscar_registros / filtrar_dados / calcular_estatisticas
  (funções puras sobre o `store` já existente — nenhuma lógica nova de parsing/ingestão)
```

Nenhuma rota, schema ou contrato HTTP muda. `agent_service` (variável de módulo)
passa a apontar para `GeminiAgentService()`.

## Escopo da resposta (decisão confirmada)

- v1 do `GeminiAgentService` sempre devolve `TextQueryResult` (`answer` +
  `detail` opcional). Os tipos `table`/`chart`/`combined` continuam existindo
  no schema para uso futuro, mas não são produzidos pelo agente Gemini nesta
  entrega — evita risco de o modelo gerar JSON estruturado inválido.

## Tools expostas ao Gemini

Implementadas como funções puras em `dataset_service.py`, recebendo
`dataset_id` explícito. `GeminiAgentService` cria wrappers por-requisição que
fixam o `dataset_id` do `DatasetContext` atual antes de expor ao modelo — o
Gemini nunca escolhe *qual* dataset acessar, só *como* consultar o atual.

| Tool | Parâmetros | Retorno |
| --- | --- | --- |
| `listar_colunas` | `table?: str` | colunas (nome, tipo, descrição, nulos) de uma tabela ou de todas |
| `obter_resumo` | — | nome do dataset, tabelas, totais de linhas/colunas, resumo textual |
| `buscar_registros` | `table: str, limit=10, offset=0` | amostra de linhas (limit máx. 50) |
| `filtrar_dados` | `table, column, operator, value` | linhas que batem o filtro (`=,!=,>,<,>=,<=,contains`) |
| `calcular_estatisticas` | `table, column` | numérico: count/sum/avg/min/max/nullCount · texto: distinct/top-values |

Erros de ferramenta (tabela/coluna inexistente, operador inválido) levantam
uma exceção própria (`DatasetToolError`), capturada pelo `GeminiAgentService`
e devolvida ao modelo como conteúdo de erro na `function_response` (o modelo
pode se corrigir, ex.: pedir `listar_colunas` de novo com nome certo).

## Ciclo de function calling

O SDK `google-genai` atual expõe a **Interactions API**
(`client.interactions.create(...)`), não o `generate_content()`/`types.Tool`
mais antigo. Loop manual, máximo de 5 iterações:

1. Chama `client.interactions.create(model=..., input=pergunta_ou_resultados,
   tools=TOOL_DECLARATIONS, system_instruction=..., previous_interaction_id=...)`.
   As 5 tools são declaradas como dicts JSON simples
   (`{"type": "function", "name", "description", "parameters"}`), sem
   introspecção automática de funções Python.
2. Percorre `interaction.steps`: cada step com `.type == "function_call"` tem
   `.name` e `.arguments` (já um dict) e `.id` (usado como `call_id` na
   resposta). Executa a função correspondente (try/except captura erro de
   execução e nome de ferramenta desconhecida) e monta um item
   `{"type": "function_result", "name": step.name, "call_id": step.id,
   "result": [{"type": "text", "text": json.dumps(saida)}]}`.
3. Se houve pelo menos um `function_call`: a próxima chamada usa
   `input=<lista de function_result>` e `previous_interaction_id=interaction.id`,
   volta ao passo 1.
4. Se não houve nenhum `function_call`: `interaction.output_text` é a
   resposta final → `TextQueryResult(answer=texto, detail=None)`.
5. Estourar o limite de iterações, ou `output_text` vazio/ausente → erro
   tratado (item abaixo).

Erros da API são exceções `google.genai.errors.APIError` (e subclasses
`ClientError`/`ServerError`), com atributo `.code` (int, código HTTP) — usado
para distinguir rate limit (429) de outras falhas de comunicação.

## Grounding — só responder com base nos dados carregados

Regra central da `system_instruction` (reforça o requisito original "responder
com base exclusivamente nos dados disponíveis"):

> Responda apenas com base no que as ferramentas devolverem sobre este
> dataset. Nunca use conhecimento geral do mundo (mesmo que "saiba" a
> resposta de outro contexto). Se a pergunta não tem relação com as
> tabelas/colunas carregadas, diga isso claramente e informe que assuntos o
> dataset cobre (usando `obter_resumo`/`listar_colunas`).

Distinção de tipo de resposta:

- **Pergunta fora do escopo do dataset** (ex.: "qual foi o resultado do jogo
  de ontem?", quando o CSV é de notas fiscais) → **não é erro de sistema**.
  É uma resposta válida `TextQueryResult` dizendo que não há dados sobre o
  assunto neste conjunto, e o que o dataset cobre.
- **Falha real** (API fora do ar, chave ausente, limite excedido, etc.) →
  `ErrorQueryResult`, reservado só para esses casos.

## Tratamento de erros

Todo erro vira `AgentAnalyzeResponse(status="error", result=ErrorQueryResult(...))`
— nunca uma exceção HTTP nova (mesmo padrão que a rota já espera de um
resultado tipo `error`). Nenhum stack trace ou dado sensível no corpo da
resposta; detalhes completos só via `logger.exception(...)` no servidor.

Casos cobertos:

| Caso | Tratamento |
| --- | --- |
| `GEMINI_API_KEY` ausente | erro imediato, sem chamar a API, mensagem orientando configurar a variável |
| Dataset não carregado (`dataset_context is None`) | erro imediato, sem chamar a API |
| Erro de comunicação com Gemini (rede/timeout) | capturado, mensagem genérica de indisponibilidade |
| Limite da API (HTTP 429) | capturado, mensagem pedindo para tentar novamente mais tarde |
| Ferramenta inexistente solicitada pelo modelo | tratado dentro do loop; se persistir, erro genérico |
| Erro durante execução de uma ferramenta | `DatasetToolError` devolvido ao modelo como `function_response` de erro; se o loop estourar por causa disso, erro genérico |
| Resposta inválida/vazia/bloqueada do modelo | erro genérico |

## Configuração

| Variável | Obrigatória | Default | Descrição |
| --- | --- | --- | --- |
| `GEMINI_API_KEY` | sim | — | chave da API Gemini, lida via `os.getenv`, nunca hardcoded |
| `GEMINI_MODEL` | não | `gemini-3.6-flash` | modelo usado (Flash, compatível com free tier); confirme o nome exato disponível na sua conta em [aistudio.google.com](https://aistudio.google.com) |

`backend/.env.example` novo, documentando as duas variáveis.

## Arquivos tocados

- `backend/services/agent_service.py` — reescrito: `GeminiAgentService`
  substitui `MockAgentService` (removida, não apenas desativada — não há
  motivo para manter código morto).
- `backend/services/dataset_service.py` — adição das 5 funções de tool e da
  exceção `DatasetToolError`. Nenhuma mudança nas funções de ingestão
  existentes.
- `backend/requirements.txt` — adiciona `google-genai` e `pytest` (testes) e
  `python-dotenv` (ver nota abaixo).
- `backend/.env.example` — novo.
- `backend/pytest.ini` — novo (`pythonpath = .`, para os testes importarem
  `services`/`schemas` do jeito que `uvicorn` já importa).
- `backend/tests/` — novo (`conftest.py` com fixture de dataset de teste,
  `test_dataset_tools.py`, `test_agent_service.py`).
- `backend/main.py` — duas linhas no topo (`from dotenv import load_dotenv;
  load_dotenv()`) para que `backend/.env` seja lido automaticamente, do
  mesmo jeito que o front-end já lê o `.env` dele. Sem isso, `GEMINI_API_KEY`
  só seria lida se exportada manualmente no shell a cada sessão — pequeno
  desvio do "nenhuma mudança em main.py" original, necessário para o
  `.env.example` funcionar de fato.
- `backend/README.md` — seção "Agente de IA (mock)" atualizada para refletir
  a implementação real.

Nenhuma mudança em `routes/` ou `schemas/models.py`.

## Testes / verificação

- Sem servidor de teste automatizado hoje no backend (não há suíte
  `pytest`); verificação será manual: subir `uvicorn`, chamar `/api/datasets`
  com um ZIP de exemplo e depois `/api/analyze` com perguntas dentro e fora
  do escopo do dataset, confirmando o comportamento de grounding.
- Usuário vai gerar a própria `GEMINI_API_KEY` e configurar localmente antes
  do teste ao vivo.
