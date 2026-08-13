# Migração do agente de IA: Gemini → Groq (GPT-OSS)

Data: 2026-08-13

## Objetivo

Substituir `GeminiAgentService` por `GroqAgentService`, mantendo a interface `AgentService`
inalterada, o contrato HTTP inalterado, e reaproveitando integralmente as tools de
`dataset_service.py` já implementadas, testadas e corrigidas (Tasks 1-3 do agente Gemini, mais os
fixes da revisão final e do bug de rate-limit).

## Contexto

Esta é uma continuação do trabalho no branch `worktree-gemini-agent` (não mergeado em `main`).
Nada muda na arquitetura geral — só a implementação interna de `AgentService` e sua dependência
externa (SDK, variáveis de ambiente, tratamento de erros específico do provedor).

## O que é reaproveitado sem mudanças

- `backend/services/dataset_service.py` — as 5 tools (`listar_colunas`, `obter_resumo`,
  `buscar_registros`, `filtrar_dados`, `calcular_estatisticas`) e `DatasetToolError`. Nenhuma
  mudança: são agnósticas de provedor de LLM.
- `backend/routes/analyze.py`, `backend/schemas/models.py` — contrato HTTP e schemas Pydantic,
  intocados.
- `backend/main.py` — o `load_dotenv()` já genérico (não é específico do Gemini) continua igual.
- Padrão de erro: todo erro vira `AgentAnalyzeResponse(status="error", result=ErrorQueryResult(...))`,
  nunca uma exceção HTTP nova; nenhum stack trace no corpo da resposta.
- Escopo da resposta: `TextQueryResult` (`answer` + `detail` opcional) — mesma decisão do agente
  Gemini, mantida aqui.

## SDK Groq — verificado contra a documentação oficial

O SDK `groq` é compatível com o padrão OpenAI de chat completions, mais estável e previsível que a
API do Gemini usada anteriormente (que teve duas mudanças de formato só nesta sessão):

```python
from groq import Groq
client = Groq(api_key=api_key)

response = client.chat.completions.create(
    model=model,
    messages=messages,   # lista de {"role": ..., "content": ...}
    tools=TOOL_DECLARATIONS,   # mesmo formato JSON Schema já usado no Gemini
    tool_choice="auto",
)

message = response.choices[0].message
tool_calls = message.tool_calls   # lista; cada item tem .id, .function.name, .function.arguments (string JSON)
```

Resultado de uma tool volta como mensagem no formato:

```python
{"tool_call_id": tool_call.id, "role": "tool", "name": function_name, "content": json.dumps(output)}
```

`openai/gpt-oss-20b` suporta tool calling (confirmado na doc oficial: "Yes ✅"), mas não faz
*parallel tool calling* — na prática o modelo pede uma tool por vez, mas o código trata
`tool_calls` como lista de qualquer forma (é o formato genérico da API, e não custa nada ser
robusto a isso).

### Erros do SDK (classes públicas e estáveis, ao contrário do módulo privado do Gemini)

| Classe | Quando |
| --- | --- |
| `groq.AuthenticationError` | chave inválida (401) |
| `groq.RateLimitError` | limite de uso (429) |
| `groq.APITimeoutError` | timeout da requisição |
| `groq.APIConnectionError` | erro de rede/conexão (classe-base de `APITimeoutError` também) |
| `groq.NotFoundError` | modelo inexistente/indisponível (404) |
| `groq.APIStatusError` / `groq.APIError` | base genérica para os demais casos HTTP |

## Ciclo de function calling

Loop manual, máximo de 5 iterações (mesmo limite do agente Gemini), usando uma lista `messages`
acumulada (sem necessidade de um ID de conversa como o `previous_interaction_id` do Gemini):

1. Monta `messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}, {"role": "user", "content": pergunta}]`.
2. Chama `client.chat.completions.create(model=..., messages=messages, tools=TOOL_DECLARATIONS, tool_choice="auto")`.
3. Se `message.tool_calls` não é vazio: adiciona a mensagem do assistente a `messages`; para cada
   `tool_call`, faz `json.loads(tool_call.function.arguments)`, executa a tool correspondente
   (try/except captura `DatasetToolError`, `TypeError` de parâmetros inválidos, e
   `json.JSONDecodeError` de argumentos malformados), adiciona `{"role": "tool", ...}` com o
   resultado (ou erro) a `messages`; volta ao passo 2.
4. Se `message.tool_calls` é vazio: `message.content` é a resposta final →
   `TextQueryResult(answer=texto)`. Se `content` vier vazio/`None`, é erro (`_InvalidModelResponseError`).
5. Estourar o limite de iterações → mesmo erro genérico do passo 4.

## Grounding

Mesma regra da `system_instruction` do agente Gemini, adaptada: responder só com base no que as
tools devolverem sobre este dataset; nunca usar conhecimento geral do modelo; avisar quando a
pergunta não tem relação com os dados carregados; nunca inventar valores.

## Registro de tools permitidas

Mesma estratégia do agente Gemini: um dicionário `nome -> callable` fechado por `dataset_id`,
construído por requisição. Qualquer `tool_call.function.name` fora desse dicionário vira
`{"error": "Ferramenta '<nome>' não existe."}` devolvido ao modelo — nunca uma função arbitrária é
executada.

## Tratamento de erros

9 categorias (uma a mais que o agente Gemini — timeout é separado de falha de comunicação, por
pedido explícito):

| Caso | Tratamento |
| --- | --- |
| `GROQ_API_KEY` ausente | erro imediato, sem chamar a API |
| Dataset não carregado | erro imediato, sem chamar a API |
| Timeout | `groq.APITimeoutError` → mensagem específica de timeout |
| Falha de comunicação | `groq.APIConnectionError` (outros) → mensagem genérica de indisponibilidade |
| Limite da API | `groq.RateLimitError` → mensagem de limite atingido |
| Modelo indisponível | `groq.NotFoundError` → mensagem de modelo indisponível/mal configurado |
| Ferramenta inexistente | tratado dentro do loop, devolvido ao modelo |
| Erro de execução de ferramenta | `DatasetToolError`/`TypeError`/`JSONDecodeError` devolvido ao modelo |
| Resposta inesperada/vazia | `content` vazio ou limite de iterações → erro genérico |

Nenhum stack trace, chave ou dado sensível no corpo da resposta; detalhe completo só via
`logger.exception(...)`.

## Configuração

| Variável | Obrigatória | Default | Descrição |
| --- | --- | --- | --- |
| `GROQ_API_KEY` | sim | — | chave da API Groq (console.groq.com), lida via `os.getenv`, nunca hardcoded |
| `GROQ_MODEL` | não | `openai/gpt-oss-20b` | modelo usado |

`GEMINI_API_KEY`/`GEMINI_MODEL` removidas do `.env.example`.

## Arquivos tocados

- `backend/services/agent_service.py` — reescrito: `GroqAgentService` substitui `GeminiAgentService`
  (removida por completo, junto com as exceções internas específicas do Gemini). Interface
  `AgentService` (a classe abstrata) permanece idêntica.
- `backend/requirements.txt` — remove `google-genai`, adiciona `groq`. `python-dotenv` e `pytest`
  continuam (não são específicos de provedor).
- `backend/.env.example` — troca as variáveis Gemini pelas Groq.
- `backend/README.md` — seção "Agente de IA" atualizada para Groq.
- `backend/tests/test_agent_service.py` — reescrito para testar `GroqAgentService` com um cliente
  Groq falso (mesmo estilo `FakeClient` do agente Gemini, adaptado ao formato
  `chat.completions.create`/`tool_calls`).

Nenhuma mudança em `routes/`, `schemas/models.py`, `main.py` ou `dataset_service.py`.

## Testes / verificação

- Suíte pytest reaproveita os testes de `dataset_service.py` sem alteração (Task 1 do agente
  Gemini). Só os testes do agente são reescritos.
- Verificação manual de ponta a ponta com uma `GROQ_API_KEY` real, mesmo roteiro usado para o
  Gemini (pergunta dentro do escopo do dataset, pergunta fora do escopo).
