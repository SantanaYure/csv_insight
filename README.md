# CSV Insight

Aplicação frontend que permite carregar um pacote ZIP com arquivos CSV e consultar esses dados
em linguagem natural — sem escrever SQL. A interface implementa o design criado no Claude Design
("CSV Insight"), preservando tokens, espaçamentos, componentes, estados e comportamento
responsivo.

Por padrão (`VITE_USE_MOCKS=true`) tudo funciona com **dados mockados**, calculados no navegador.
Um backend FastAPI (pasta [`backend/`](backend/)) já implementa o mesmo contrato consumido por
`src/services/apiDataService.ts` — para usá-lo, veja [`backend/README.md`](backend/README.md) e
ajuste `VITE_USE_MOCKS=false` no `.env` do front-end.

---

## Stack

| Camada | Tecnologia |
| --- | --- |
| Build | Vite 8 |
| UI | React 18 + TypeScript (strict) |
| Design system | Chakra UI 2 (`extendTheme`, tokens semânticos, dark mode) |
| Rotas | React Router 6 |
| Formulários | React Hook Form + Zod |
| Gráficos | Recharts |
| Leitura do ZIP | fflate |
| Leitura dos CSVs | papaparse |
| Ícones | lucide-react |

Não são usados Tailwind, Material UI, Styled Components nem qualquer CSS framework externo:
todo o estilo vem do tema do Chakra.

---

## Instalação

```bash
npm install
```

## Execução

```bash
npm run dev
```

A aplicação sobe em `http://localhost:5173` (ou na próxima porta livre).

Outros scripts:

```bash
npm run build
```

```bash
npm run lint
```

```bash
npm run preview
```

---

## Formato do arquivo ZIP

A aplicação **começa vazia**: não há nenhum conjunto de dados pré-cadastrado. Tudo que aparece
no resumo, na consulta e no histórico vem do ZIP que você envia em `/upload`.

```
dados.zip
├─ notas_fiscais.csv
├─ itens.csv
├─ fornecedores.csv
└─ dicionario_dados.csv   (opcional)
```

Regras de leitura:

- todo `.csv` do pacote vira uma tabela consultável (diretórios, `__MACOSX/` e arquivos ocultos
  são ignorados; arquivos que não sejam CSV, como um `README.txt`, também);
- o dicionário é reconhecido pelo nome (`dicionario…` ou `dictionary…`) e define **tipo** e
  **descrição** de cada coluna;
- sem dicionário, os tipos são inferidos dos próprios valores;
- números aceitam `1234.56`, `1.234,56` e `1234,56`; sequências longas de dígitos
  (chave de acesso, CNPJ sem máscara) permanecem como texto, sem perda de precisão.

### Dicionário de dados

Cabeçalho esperado — os nomes com acento ou em inglês também são aceitos:

```csv
arquivo,coluna,tipo,descricao,chave,referencia,formato
notas_fiscais.csv,valor_total,decimal,Valor total da nota fiscal,,,BRL
notas_fiscais.csv,id_fornecedor,string,Identificador do fornecedor,FK,fornecedores.id_fornecedor,
```

Mapeamento de tipos: `formato=BRL` → moeda · `datetime|date` → data ·
`integer|decimal|float` → número · `boolean` → booleano · `string|text` → texto.

---

## Consultas

As respostas são **calculadas sobre as linhas carregadas** — não existe nenhum resultado fixo no
código. O motor identifica o papel de cada tabela (notas, itens, fornecedores) pelos nomes e
tipos das colunas e responde a perguntas como:

| Pergunta | Tipo de resposta |
| --- | --- |
| Qual foi o valor total das compras? | `text` |
| Quais foram os maiores fornecedores? | `table` (resolve o FK para a razão social) |
| Qual foi o total gasto em cada mês? | `chart` (barras; linhas acima de 6 meses) |
| Qual produto teve a maior quantidade comprada? | `combined` |
| Quais produtos tiveram o maior valor gasto? | `table` |
| Como foi distribuído o valor por forma de pagamento? | `chart` (pizza) |
| Quanto foi pago em tributos aproximados? | `text` |
| Qual foi o ticket médio por nota? | `text` |
| Qual o item mais caro? | `table` |
| Quantas notas / quantos itens existem? | `text` |

As perguntas sugeridas na sidebar e no estado vazio são geradas a partir das colunas que o
conjunto realmente possui. Perguntas fora do alcance do motor recebem uma resposta do tipo
`error` listando os assuntos e as tabelas disponíveis.

---

## Serviço de dados

O seletor fica em [`src/services/index.ts`](src/services/index.ts):

```ts
export const dataService: DataService =
  import.meta.env.VITE_USE_MOCKS === 'true' ? mockDataService : apiDataService;
```

Com `VITE_USE_MOCKS=true` (padrão) tudo roda no navegador: o ZIP é descompactado com `fflate`,
os CSVs são interpretados com `papaparse` e as consultas são calculadas localmente. O conjunto
fica no `sessionStorage` (limite de 4 MB; acima disso permanece só em memória), de modo que um
recarregamento da página não perde os dados da sessão.

**Nenhum componente chama `fetch` diretamente.** Todo acesso a dados passa pela interface
`DataService`.

---

## Variáveis de ambiente

Copie `.env.example` para `.env`:

```bash
cp .env.example .env
```

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `VITE_USE_MOCKS` | `true` | `true` usa os mocks; qualquer outro valor usa o backend real. |
| `VITE_API_URL` | `http://localhost:8000/api` | URL base da API. |

---

## Estrutura

```
src/
├── app/            App, router e providers
├── pages/          Uma página por rota + a tela de processamento
├── layouts/        PublicLayout e ApplicationLayout
├── components/
│   ├── common/     Header, sidebar, drawer, badges, cards, diálogos
│   ├── home/       Mockup da aplicação exibido no hero
│   ├── upload/     Dropzone, card de arquivo, progresso, etapas
│   ├── dataset/    Estatísticas, acordeão de tabelas, colunas, preview
│   ├── query/      Chat, mensagens, input, sugestões, loading
│   ├── results/    Text, Table, Chart, Combined, Error + utilidades
│   └── workspace/  Abas + painéis Consulta / Dados / Histórico
├── services/
│   ├── ingestion/  Leitura do ZIP, parse de CSV, dicionário e tipos
│   ├── query/      Papéis das tabelas e motor de respostas
│   ├── datasetStore.ts     Conjunto e histórico da sessão
│   ├── DataService.ts      Contrato
│   ├── mockDataService.ts  Implementação local (no navegador)
│   └── apiDataService.ts   Implementação HTTP
├── types/          dataset, query, message, api
├── hooks/          useDataset, useUploadDataset, useQueryDataset, useHistory
├── theme/          colors, semanticTokens, typography, components
└── utils/          formatação de moeda, número, data, tamanho e ids
```

---

## Rotas

O fluxo é enxuto de propósito: duas telas depois da home, espelhando as duas
interfaces do desafio — **A** (carga) e **B** (consulta).

| Rota | Página | Layout |
| --- | --- | --- |
| `/` | `HomePage` | `PublicLayout` |
| `/upload` | `UploadPage` — Interface A: carga do ZIP + processamento | `PublicLayout` |
| `/datasets/:datasetId` | `WorkspacePage` — Interface B: dataset carregado | `ApplicationLayout` |
| `/not-found` | `NotFoundPage` | `PublicLayout` |
| `*` | redireciona para `/not-found` | — |

`WorkspacePage` não tem sub-rotas: **Consulta**, **Dados** e **Histórico** são
painéis alternados pelo controle segmentado no topo do conteúdo, guardados em
`?panel=chat|data|history` (mais `&table=` para expandir uma tabela específica
e `&q=` para preencher uma pergunta vinda da sidebar). Isso mantém tudo
deep-linkável sem multiplicar telas — trocar de painel não perde a posição de
rolagem nem dispara uma navegação de página inteira. `/datasets/:id/query` e
`/datasets/:id/history` continuam funcionando como redirecionamentos, para
não quebrar links antigos.

No mobile, o controle segmentado ocupa a largura toda (alvos de toque de
44px) e a sidebar vira um drawer acionado pelo menu no header; no desktop a
sidebar fica fixa ao lado do conteúdo e as abas ficam grudadas (`sticky`)
logo abaixo do header ao rolar a página.

O `datasetId` é gerado no momento do upload. Ao final do processamento a aplicação navega para
`/datasets/{id}`. Acessar uma rota de dataset sem nenhum conjunto carregado redireciona para
`/upload` com um aviso — nunca há dados sem envio prévio.

---

## Design system

### Cores

Distribuição 60% branco e cinza-claro · 30% preto e cinza-escuro · 10% amarelo. O amarelo fica
reservado a botões primários, estados ativos, badges, foco, gráficos e indicadores — nunca como
grande área de fundo.

| Token | Claro | Escuro |
| --- | --- | --- |
| `background.page` | `#FAFAFA` | `#111111` |
| `background.surface` | `#FFFFFF` | `#1F1F1F` |
| `background.subtle` | `#F5F5F5` | `#2A2A2A` |
| `text.primary` | `#111111` | `#FFFFFF` |
| `text.secondary` | `#444444` | `#D4D4D4` |
| `text.muted` | `#7A7A7A` | `#A3A3A3` |
| `border.default` | `#E5E5E5` | `#2D2D2D` |
| `border.strong` | `#D9D9D9` | `#3A3A3A` |
| `brand.primary` | `#FFCA28` | `#FFCA28` |
| `brand.primaryHover` | `#F5B800` | `#FFD84D` |
| `brand.primaryActive` | `#D99D00` | `#F5B800` |
| `brand.soft` | `#FFF3BF` | `#3A3115` |
| `brand.tint` | `#FFFBEA` | `#221E13` |
| `brand.textOnPrimary` | `#111111` | `#111111` |

Também existem `chat.userBg` / `chat.userText`, `chart.grid` / `chart.axis` e a família
`feedback.success | warning | error | info`.

### Tipografia

Inter, com fallback `system-ui, sans-serif`, pesos 400/500/600/700. A escala vive em
`theme/typography.ts` e é exposta como `sizes` do `Heading`:

| Token | Desktop | Tablet | Mobile | Peso |
| --- | --- | --- | --- | --- |
| `display` | 48px | 36px | 32px | 700 |
| `h1` | 36px | 30px | 28px | 700 |
| `h2` | 28px | 24px | 22px | 700 |
| `subtitle` | 20px | 20px | 18px | 600 |
| Texto | 16px | 16px | 16px | 400 |
| Texto pequeno | 14px | 14px | 14px | 400/500 |
| Legenda | 12px | 12px | 12px | 500 |

### Forma e espaçamento

- Cards 14px · botões e inputs 10px · badges 999px.
- Sombra de card em uma camada: `0 1px 2px rgba(17,17,17,.05)`; no escuro a elevação vem da cor
  do card.
- Escala de 4px. Padding interno de cards 20–28px, gap entre cards 16px, entre seções 52–64px.
- Gutter da página: 18px no mobile, 28px no tablet, 40px no desktop.

### Breakpoints

`base` < 480px · `sm` 480px · `md` 768px · `lg` 1024px (sidebar fixa) · `xl` 1280px.

### Acessibilidade

- Nenhum controle abaixo de 44×44px.
- Anel de foco de 2px em amarelo com offset de 2px.
- Enter envia a pergunta; Shift+Enter quebra a linha; Esc fecha drawer e modal.
- Texto sobre amarelo sempre em `#111111`; erros nunca só por cor (sempre ícone + texto).
- Um único `h1` por tela, ícones com `aria-label` e tooltip, estados de carregamento com
  `role="status"`.

### Tema claro e escuro

`ThemeToggle` usa `useColorMode` do Chakra e a preferência fica em `localStorage`.

---

## Integração com o backend FastAPI

1. Suba o backend (veja [`backend/README.md`](backend/README.md) para detalhes):

   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

2. Ajuste o `.env` do front-end:

   ```
   VITE_USE_MOCKS=false
   VITE_API_URL=http://localhost:8000/api
   ```

3. Endpoints implementados em `backend/routes/`, consumidos por
   [`src/services/apiDataService.ts`](src/services/apiDataService.ts):

   | Método | Endpoint | Corpo | Resposta |
   | --- | --- | --- | --- |
   | `POST` | `/datasets` | `multipart/form-data` com o campo `file` | `{ "data": Dataset }` |
   | `GET` | `/datasets/{datasetId}` | — | `{ "data": Dataset }` |
   | `POST` | `/datasets/{datasetId}/questions` | `{ "question": string }` | `{ "data": QueryResult }` |
   | `GET` | `/datasets/{datasetId}/history` | — | `{ "data": ChatMessage[] }` |
   | `DELETE` | `/datasets/{datasetId}/history/{messageId}` | — | `204` |

4. Os contratos de `Dataset`, `QueryResult` e `ChatMessage` estão em [`src/types`](src/types) e
   têm um schema Pydantic equivalente em [`backend/schemas/models.py`](backend/schemas/models.py).
   Erros devolvidos com `detail` ou `message` são convertidos em `ApiError` e exibidos como
   resultado do tipo `error` na conversa.

Como todo acesso passa pela interface `DataService`, trocar mock por API real não exige nenhuma
alteração em páginas ou componentes.
