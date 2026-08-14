# -*- coding: utf-8 -*-
"""Fonte única de conteúdo do relatório técnico do Desafio 4 (InsurMinds / CSV Insight).

Estrutura em blocos consumida por três geradores: build_docx.py, build_pdf.py e
export_markdown.py. Editar apenas este arquivo mantém DOCX, PDF e Markdown em sincronia.
"""

COVER = {
    "program": "InsurMinds",
    "subtitle": "Inteligência Artificial Aplicada a Seguros",
    "challenge": "Desafio 4",
    "title": "Interface Inteligente para Consulta de Arquivos CSV",
    "project_name": "CSV Insight",
    "group_name": "[PENDENTE — preencher com o nome do grupo]",
    "members": "[PENDENTE — preencher com nome, e-mail e telefone de cada integrante]",
    "date": "14 de agosto de 2026",
}

# Tipos de bloco: h1, h2, h3, p, bullets, numbered, table, image, note, pagebreak
BLOCKS = [
    ("h1", "1. Introdução"),
    ("p",
     "O Desafio 4 do programa InsurMinds pede o desenvolvimento de um agente inteligente "
     "capaz de responder, em linguagem natural, perguntas sobre dados armazenados em "
     "arquivos CSV. O problema de fundo é comum a muitas organizações: os dados existem "
     "em planilhas e arquivos texto, mas boa parte dos usuários não sabe escrever SQL "
     "nem operar ferramentas de análise."),
    ("p",
     "O projeto CSV Insight resolve esse problema com duas interfaces conectadas por uma "
     "API própria: o usuário envia um arquivo .zip ou .csv, o backend processa e limpa os "
     "dados automaticamente, e a partir daí o usuário conversa com um agente que consulta "
     "esses dados sob demanda e responde em português, sem que ninguém precise escrever "
     "uma única consulta SQL."),
    ("p",
     "Este relatório descreve exclusivamente o que está implementado no código do "
     "repositório na data acima: tecnologias realmente usadas, arquitetura real, o agente "
     "e suas tools, o fluxo de processamento dos dados e o fluxo de uma pergunta até a "
     "resposta. Trechos marcados como [PENDENTE] indicam informação que depende de uma "
     "execução real da aplicação pelo grupo (por exemplo, com uma chave de API válida) e "
     "não de algo ausente no código."),

    ("h1", "2. Tecnologias utilizadas"),
    ("p",
     "A tabela a seguir lista as tecnologias efetivamente presentes no código do "
     "repositório (frontend/package.json e backend/requirements.txt), com a função de "
     "cada uma na solução."),
    ("table", {
        "header": ["Camada", "Tecnologia", "Função na solução"],
        "col_widths_frac": [0.20, 0.28, 0.52],
        "rows": [
            ["Build do front-end", "Vite 8", "Empacotamento e servidor de desenvolvimento do React."],
            ["UI", "React 18 + TypeScript", "Interface de upload (Interface A) e de consulta/chat (Interface B)."],
            ["Design system", "Chakra UI 2", "Componentes visuais, tema claro/escuro, tokens de cor e tipografia."],
            ["Formulários", "React Hook Form + Zod", "Validação do formulário de upload no front-end."],
            ["Gráficos (front-end)", "Recharts", "Biblioteca de gráficos disponível na UI para resultados do tipo chart."],
            ["API HTTP", "FastAPI", "Roteamento HTTP, validação de payload (Pydantic) e tratamento central de erros."],
            ["Servidor ASGI", "Uvicorn", "Executa a aplicação FastAPI (uvicorn main:app)."],
            ["Processamento de dados", "Pandas", "Limpeza, normalização e detecção de tipos das tabelas (DataCleaningService)."],
            ["Leitura de ZIP/CSV (backend)", "zipfile e csv (biblioteca padrão do Python)", "Leitura do pacote em memória, sem bibliotecas externas de ZIP no servidor."],
            ["Framework de agentes", "Pydantic AI (pydantic-ai-slim[groq])", "Estrutura o agente, declara as tools e controla o ciclo de tool calling."],
            ["Provedor de inferência", "Groq", "Serviço que hospeda e executa o modelo de linguagem via API."],
            ["Modelo de linguagem", "GPT-OSS (openai/gpt-oss-20b, configurável)", "Rede neural que interpreta a pergunta e gera a resposta em texto."],
            ["Validação/contratos", "Pydantic", "Schemas de Dataset, QueryResult, ChatMessage etc. (schemas/models.py)."],
            ["Testes automatizados", "pytest", "Testes unitários e de integração do backend, com agente e modelo simulados."],
            ["Comunicação HTTP (backend)", "httpx", "Cliente HTTP usado internamente pelo Pydantic AI para falar com a Groq."],
        ],
    }),
    ("p",
     "É importante não confundir três camadas distintas dessa lista, porque o enunciado "
     "do desafio trata cada uma de forma diferente:"),
    ("bullets", [
        "Framework de agentes — Pydantic AI: biblioteca Python que estrutura o agente, "
        "declara as tools tipadas, valida entradas e saídas e controla o laço de decisão "
        "sobre quando chamar uma tool. É a peça exigida pela lista de frameworks do "
        "enunciado (AutoGen, Pydantic AI, LangChain, LangFlow, LlamaIndex, CrewAI, n8n).",
        "Provedor da LLM — Groq: serviço de inferência que hospeda o modelo e expõe uma "
        "API compatível com o padrão usado pelo Pydantic AI. É o serviço que efetivamente "
        "processa a requisição e cobra (ou limita) o uso.",
        "Modelo — GPT-OSS (openai/gpt-oss-20b): a rede neural específica executada pelo "
        "provedor Groq. É configurável pela variável de ambiente GROQ_MODEL, sem precisar "
        "alterar a lógica do agente.",
    ]),
    ("p",
     "Nenhuma dessas camadas depende diretamente das outras duas no código: trocar de "
     "modelo GPT-OSS para outro hospedado na Groq, por exemplo, é só uma mudança de "
     "variável de ambiente, porque o Pydantic AI abstrai a comunicação com o provedor."),
    ("note",
     "Observação: fflate e papaparse (citadas no README do front-end) são usadas apenas no "
     "modo local de mock do navegador (VITE_USE_MOCKS=true) — quando o front-end fala com "
     "o backend real (padrão do projeto), quem lê o ZIP e os CSVs é o backend Python, com "
     "zipfile e csv da biblioteca padrão."),

    ("h1", "3. Arquitetura da solução"),
    ("p",
     "A arquitetura segue um fluxo em camadas único (não há orquestração multiagente "
     "neste desafio): o front-end fala com uma API FastAPI, que delega a análise a um "
     "serviço de agente, que por sua vez usa o Pydantic AI para decidir quais tools "
     "chamar sobre os dados já processados e guardados em memória."),
    ("image", "arquitetura.png", "Figura 1 — Arquitetura real da solução, dos componentes do repositório."),
    ("p", "Responsabilidade de cada camada:"),
    ("table", {
        "header": ["Camada", "Responsabilidade"],
        "col_widths_frac": [0.30, 0.70],
        "rows": [
            ["Front-end (React/Vite/Chakra)", "Interface A (upload do ZIP/CSV) e Interface B (chat de consulta), consumindo a API via frontend/src/services/apiDataService.ts."],
            ["FastAPI — routes/", "Tradução HTTP: recebe multipart/JSON, valida com Pydantic e devolve o envelope {status, data}. Tratamento central de exceções em main.py."],
            ["AgentService (services/agent_service.py)", "Fronteira entre a rota HTTP e o Pydantic AI: monta o modelo Groq, executa o agente e converte qualquer falha técnica em uma resposta de erro segura para o usuário."],
            ["Agente Pydantic AI (agents/data_agent.py)", "Declara as instruções do sistema, as 5 tools tipadas e as dependências do agente (DatasetAgentDeps)."],
            ["Groq / GPT-OSS", "Motor de inferência: interpreta a pergunta, decide se e quais tools chamar, e gera a resposta final em texto."],
            ["Tools", "Fronteira tipada e escopada entre o agente e os dados: cada tool só pode fazer uma operação específica sobre o dataset da requisição atual."],
            ["DatasetService (services/dataset_service.py)", "Regras de consulta: filtro, estatística, paginação e resumo sobre as linhas já processadas."],
            ["Store em memória (_DatasetStore)", "Guarda o dataset processado e o histórico de perguntas, por processo do backend, sem banco de dados."],
        ],
    }),

    ("h1", "4. Carga e processamento dos dados"),
    ("p",
     "O fluxo de ingestão começa em POST /api/datasets (multipart/form-data, campo file) "
     "e é conduzido pelo DatasetUploadService, que delega a leitura efetiva do arquivo ao "
     "módulo services/dataset_service.py."),
    ("numbered", [
        "Upload: o arquivo é lido em blocos de 1 MB; a leitura é interrompida com erro se "
        "ultrapassar 200 MB.",
        "Validação: a extensão precisa ser .csv ou .zip; qualquer outra é rejeitada antes "
        "de qualquer processamento.",
        "Leitura do ZIP inteiramente em memória (nunca extraído em disco), o que evita "
        "path traversal / zip-slip por construção. Há defesas explícitas contra zip bomb: "
        "limite de 384 MB por entrada, 512 MB de conteúdo descompactado total, taxa de "
        "compressão máxima de 100x, rejeição de entradas protegidas por senha e limite de "
        "40 arquivos CSV por pacote.",
        "Para pacotes grandes (total ≥ 64 MB ou uma entrada ≥ 32 MB), cada CSV é lido em "
        "streaming, linha a linha, em vez de manter bytes brutos, texto e DataFrame ao "
        "mesmo tempo em memória.",
        "Dicionário de dados (opcional): reconhecido pelo nome do arquivo dentro do ZIP "
        "(contendo \"dicionario\" ou \"dictionary\"); define tipo e descrição declarados "
        "por coluna e é alinhado aos nomes de coluna já normalizados pela limpeza.",
        "Limpeza conservadora (DataCleaningService, baseado em Pandas): normaliza apenas "
        "espaços nos nomes de coluna (preserva acentos, caixa e pontuação), remove linhas "
        "totalmente vazias, remove colunas totalmente vazias, remove duplicatas exatas, e "
        "só converte uma coluna para número ou data quando TODOS os valores não nulos da "
        "coluna são compatíveis com essa conversão — caso contrário, mantém a coluna como "
        "texto para não perder ou distorcer dado nenhum.",
        "Detecção de números e datas sem ambiguidade: aceita formato brasileiro "
        "(1.234,56) e internacional (1,234.56) só quando a separação em milhares bate; "
        "sequências longas de dígitos (chave de acesso, CNPJ sem máscara) permanecem "
        "como texto para preservar precisão. Datas aceitam ISO (aaaa-mm-dd) e formato BR "
        "(dd/mm/aaaa), com ou sem horário.",
        "Inferência final de tipo por coluna para exibição (string, number, currency, "
        "date, boolean, unknown): usa o dicionário de dados quando disponível; senão, "
        "infere a partir de uma amostra de até 200 valores da própria coluna.",
        "Organização em tabelas: cada CSV do pacote vira uma tabela consultável, com um "
        "id único, contagem de linhas/colunas e uma prévia de 5 linhas; um CleaningReport "
        "por tabela registra linhas originais/finais, linhas vazias e duplicadas "
        "removidas, colunas removidas, nulos por coluna e tipos detectados.",
        "Armazenamento em memória (_DatasetStore), associado a um dataset_id gerado na "
        "ingestão; a partir desse ponto a interface de consulta (Interface B) fica "
        "disponível automaticamente, sem etapa manual entre carga e consulta.",
    ]),
    ("note",
     "Cuidados de preservação de dado: a limpeza nunca converte um valor \"no escuro\" — "
     "se uma única linha de uma coluna não bater com o formato numérico ou de data "
     "esperado, a coluna inteira permanece como texto. Nomes de coluna preservam acentos "
     "e maiúsculas/minúsculas originais, e valores ausentes, duplicados e inconsistentes "
     "ficam registrados no CleaningReport de cada tabela, disponível no próprio Dataset "
     "retornado pela API."),

    ("h1", "5. Agente inteligente"),
    ("p",
     "O agente é declarado em agents/data_agent.py com o framework Pydantic AI, como "
     "Agent[DatasetAgentDeps, str] — um agente tipado, cujas dependências (dataset_id e "
     "uma instância de DatasetService) são explicitamente injetadas a cada execução, sem "
     "estado global compartilhado entre requisições."),
    ("bullets", [
        "Inicialização: create_data_agent(model) monta o Agent com output_type=str, "
        "deps_type=DatasetAgentDeps, as 5 tools decoradas com @agent.tool, retries=1 e "
        "parâmetros específicos do Groq (groq_reasoning_effort=\"low\", "
        "groq_reasoning_format=\"hidden\").",
        "Modelo: instanciado em agent_service.py como GroqModel(GROQ_MODEL, "
        "provider=GroqProvider(api_key=...)). O nome do modelo vem da variável de "
        "ambiente GROQ_MODEL (padrão openai/gpt-oss-20b).",
        "Decisão arquitetural registrada no código: o serviço usa uma subclasse "
        "_NormalizedGroqModel(GroqModel), porque o GPT-OSS às vezes devolve o nome da "
        "tool com um sufixo de canal (por exemplo, "
        "listar_colunas<|channel|>commentary). Essa subclasse normaliza o nome antes do "
        "Pydantic AI tentar localizar a tool correspondente — a correção fica restrita à "
        "fronteira com o provedor; o ciclo de execução continua inteiramente sob "
        "responsabilidade do Pydantic AI.",
        "Instruções do sistema (SYSTEM_INSTRUCTIONS): determinam que o agente responda "
        "somente com base nos dados do dataset carregado e no que as tools devolvem, "
        "nunca usando conhecimento geral e nunca inventando valores, nomes ou "
        "tendências; que escreva em português do Brasil, em frases curtas e naturais; "
        "que evite nomes técnicos de coluna e qualquer formatação Markdown na resposta; "
        "e que não presuma nenhum domínio específico (o dataset pode ser sobre qualquer "
        "assunto, não apenas notas fiscais).",
        "Como recebe perguntas: AgentService.analyze(question, dataset_context) chama "
        "agent.run_sync(question, deps=DatasetAgentDeps(dataset_id, dataset_service)).",
        "Como acessa os dados: exclusivamente pelas 5 tools, que delegam a consulta a um "
        "DatasetService recebido por dependência — o agente nunca recebe o ZIP bruto nem "
        "o dataset inteiro de uma vez.",
    ]),
    ("p", "Por que isso é um agente, e não apenas uma chamada direta a uma LLM:"),
    ("p",
     "O Pydantic AI controla um ciclo de decisão de múltiplos passos: a cada resposta do "
     "modelo, o framework verifica se há uma chamada de tool, executa essa tool, devolve "
     "o resultado ao modelo como novo contexto, e repete o processo até o modelo produzir "
     "uma resposta final em texto. A escolha de qual tool chamar (ou nenhuma), quantas "
     "vezes chamar e com quais parâmetros é feita pelo próprio modelo a cada pergunta, e "
     "não por um roteiro fixo escrito no código do projeto. Isso contrasta com uma "
     "chamada simples a uma LLM, em que o texto de entrada e saída seria fixo, sem "
     "nenhuma interação intermediária com os dados reais do dataset."),
    ("p",
     "O agente evita responder sem consultar dados porque a instrução do sistema proíbe "
     "explicitamente o uso de conhecimento geral, e porque as tools são a única fonte de "
     "dados a que ele tem acesso — não existe nenhum outro caminho, no código, para o "
     "modelo \"ver\" os dados do dataset. Quando a pergunta não tem relação com o dataset "
     "carregado ou não há dados suficientes, a instrução manda o agente dizer isso "
     "explicitamente em vez de inventar uma resposta."),

    ("h1", "6. Tools"),
    ("p",
     "As cinco tools abaixo estão registradas no agente (agents/data_agent.py) e todas "
     "delegam a execução real para o DatasetService (services/dataset_service.py) — as "
     "tools são apenas a fronteira tipada exposta ao modelo; a lógica de consulta em si "
     "vive no serviço, separada do agente."),
    ("table", {
        "header": ["Tool", "Objetivo", "Parâmetros", "Retorno", "Quando é usada"],
        "col_widths_frac": [0.14, 0.19, 0.19, 0.26, 0.22],
        "rows": [
            ["listar_colunas", "Lista as colunas de uma tabela ou de todas as tabelas do dataset.",
             "table (opcional)", "Nome, tipo, descrição e contagem de nulos de cada coluna.",
             "Quando o agente precisa saber quais colunas existem antes de filtrar ou calcular algo."],
            ["obter_resumo", "Visão geral do dataset carregado.", "— (nenhum parâmetro)",
             "Nome do dataset, tabelas, total de linhas/colunas e o resumo textual gerado na ingestão.",
             "Perguntas gerais sobre o conjunto de dados (quantas tabelas, quantas linhas no total)."],
            ["buscar_registros", "Amostra paginada de linhas de uma tabela.",
             "table, limit (máx. 10), offset",
             "Até 10 linhas compactadas, total de linhas da tabela e indicação de que há mais dados disponíveis.",
             "Perguntas que pedem exemplos, uma prévia ou os primeiros/últimos registros de uma tabela."],
            ["filtrar_dados", "Linhas que atendem a uma condição sobre uma coluna.",
             "table, column, operator (=, !=, >, <, >=, <=, contains), value",
             "Linhas que satisfazem a condição (até 10 compactadas) e o total de acertos encontrados.",
             "Perguntas de filtro, comparação e busca condicional (ex.: valores acima de um limite)."],
            ["calcular_estatisticas", "Estatísticas resumidas de uma coluna.", "table, column",
             "Coluna numérica/moeda: count, sum, avg, min, max e nullCount. Coluna texto: distinctCount e os 5 valores mais frequentes.",
             "Perguntas de agregação, totais, médias e rankings de frequência."],
        ],
    }),
    ("p",
     "Todas as tools compartilham dois limites de segurança: no máximo 10 linhas por "
     "chamada e cerca de 7.000 caracteres de payload (MAX_TOOL_ROWS e "
     "MAX_TOOL_RESULT_CHARS em dataset_service.py). Quando a consulta tem mais resultados "
     "do que isso, a tool devolve hasMore=true, e é a própria instrução do sistema que "
     "orienta o agente a pedir uma consulta mais específica em vez de tentar reproduzir o "
     "dataset inteiro — um cuidado direto para não estourar o limite de tokens da Groq."),

    ("h1", "7. Fluxo de funcionamento"),
    ("p", "Execução completa, da carga do arquivo até a resposta exibida ao usuário:"),
    ("numbered", [
        "Usuário envia um ZIP ou CSV pela Interface A (POST /api/datasets).",
        "DatasetUploadService valida extensão e tamanho, e delega a leitura a "
        "ingest_file/ingest_zip.",
        "O arquivo é processado: leitura segura do ZIP, localização do dicionário de "
        "dados (se houver), limpeza conservadora (DataCleaningService) e inferência final "
        "de tipos por coluna.",
        "O dataset processado é salvo no store em memória, associado a um dataset_id.",
        "O front-end navega para /datasets/{id} e passa a exibir a Interface B, já com o "
        "resumo do dataset.",
        "Usuário digita uma pergunta em linguagem natural no chat.",
        "O front-end chama POST /api/datasets/{id}/questions com {\"question\": \"...\"}.",
        "A rota monta um DatasetContext (nome, tabelas, totais) e chama "
        "AgentService.analyze(question, dataset_context).",
        "O AgentService obtém (ou cria, na primeira chamada) o agente Pydantic AI com o "
        "modelo Groq configurado.",
        "O agente interpreta a pergunta e decide, sozinho, se e quais tools chamar — pode "
        "encadear mais de uma chamada de tool antes de responder.",
        "A(s) tool(s) delegam a consulta ao DatasetService, que lê as linhas já "
        "processadas no store em memória e devolve um resultado compactado.",
        "O resultado da tool volta ao agente como novo contexto; o agente decide se "
        "chama outra tool ou já responde.",
        "O agente produz a resposta final em texto.",
        "O AgentService remove marcações técnicas e Markdown da resposta "
        "(humanize_answer) e a embrulha em um TextQueryResult.",
        "A rota registra a pergunta e a resposta no histórico do dataset (in-memory) e "
        "devolve {\"status\": \"success\", \"data\": {...}} ao front-end.",
        "O front-end exibe a resposta no chat e a mantém disponível na aba Histórico.",
    ]),
    ("note",
     "O fluxo acima é de um único agente (não há orquestração entre múltiplos agentes "
     "neste desafio). Além disso, na implementação atual o AgentService sempre devolve "
     "um TextQueryResult — os tipos table, chart e combined existem no contrato da API "
     "(schemas/models.py) e são usados pelo modo de mock local do front-end "
     "(VITE_USE_MOCKS=true), mas o agente real, hoje, sempre responde em texto puro."),

    ("h1", "8. Exemplos de consultas"),
    ("p",
     "No ambiente em que este relatório foi gerado não havia uma GROQ_API_KEY "
     "configurada em backend/.env, então não foi possível executar o agente real contra "
     "a API da Groq para capturar respostas de verdade. As quatro perguntas abaixo foram "
     "escolhidas para exercitar tools diferentes do agente (agregação, filtro/comparação, "
     "ranking de frequência e visão geral) e devem ser executadas pelo grupo, com uma "
     "chave de API válida e um dos datasets de exemplo do curso, antes da entrega."),
    ("note",
     "Como o agente é orientado a nunca presumir o domínio dos dados, os nomes de tabela "
     "e coluna abaixo são ilustrativos — o grupo deve trocá-los pelos nomes reais das "
     "colunas do CSV escolhido para o teste."),
    ("h3", "Pergunta 1 (agregação/estatística)"),
    ("p", "\"Qual foi o valor total da coluna [coluna de valor] em [tabela]?\""),
    ("p", "Resposta do sistema: [PENDENTE — inserir a resposta real obtida durante os testes do grupo]."),
    ("p", "Tool utilizada: calcular_estatisticas (coluna numérica/moeda: sum/avg/min/max)."),
    ("h3", "Pergunta 2 (filtro/comparação)"),
    ("p", "\"Quais registros de [tabela] têm [coluna] maior que [valor]?\""),
    ("p", "Resposta do sistema: [PENDENTE — inserir a resposta real obtida durante os testes do grupo]."),
    ("p", "Tool utilizada: filtrar_dados (operador >)."),
    ("h3", "Pergunta 3 (ranking/frequência)"),
    ("p", "\"Quais são os 5 valores mais frequentes na coluna [coluna de texto] de [tabela]?\""),
    ("p", "Resposta do sistema: [PENDENTE — inserir a resposta real obtida durante os testes do grupo]."),
    ("p", "Tool utilizada: calcular_estatisticas (coluna texto: topValues)."),
    ("h3", "Pergunta 4 (visão geral/contagem)"),
    ("p", "\"Quantas tabelas e quantas linhas esse conjunto de dados tem?\""),
    ("p", "Resposta do sistema: [PENDENTE — inserir a resposta real obtida durante os testes do grupo]."),
    ("p", "Tool utilizada: obter_resumo."),

    ("h1", "9. Tratamento de erros e limitações"),
    ("h2", "9.1 Erros na ingestão e no upload"),
    ("p",
     "Levantados por DatasetIngestionError/UploadRejectedError e traduzidos pela rota em "
     "HTTP 400 (ou 413 para arquivo grande demais), sempre com uma mensagem pronta para o "
     "usuário:"),
    ("bullets", [
        "Nenhum arquivo enviado, ou extensão diferente de .csv/.zip.",
        "Arquivo acima de 200 MB — leitura interrompida em blocos de 1 MB (HTTP 413).",
        "ZIP inválido, corrompido ou protegido por senha.",
        "Uma entrada do ZIP acima de 384 MB, taxa de compactação fora do limite de "
        "segurança (possível zip bomb) ou conteúdo descompactado total acima de 512 MB.",
        "ZIP com mais de 40 arquivos CSV.",
        "ZIP contendo apenas o dicionário de dados, sem nenhuma tabela.",
        "CSV(s) vazios ou sem cabeçalho utilizável.",
    ]),
    ("h2", "9.2 Erros na consulta ao agente"),
    ("p",
     "Tratados em AgentService.analyze, que nunca deixa uma exceção chegar à rota HTTP: "
     "todo erro vira um ErrorQueryResult devolvido com HTTP 200 e "
     "{\"data\": {\"type\": \"error\", ...}}, sem stack trace exposta ao usuário."),
    ("bullets", [
        "Pergunta vazia — erro devolvido sem sequer chamar o agente.",
        "Dataset não carregado ou dataset_id inexistente — a rota devolve HTTP 404 antes "
        "de chamar o agente.",
        "GROQ_API_KEY ausente no servidor — \"Configuração ausente\".",
        "Requisição maior que o limite de contexto do modelo (HTTP 413, ou 429 com código "
        "request_too_large/context_length_exceeded) — \"Consulta muito grande\", com "
        "sugestão de especificar tabela, coluna ou filtro.",
        "Limite de uso da API Groq atingido (HTTP 429) — \"Limite atingido\".",
        "Timeout do provedor (HTTP 408/504) ou timeout de rede (httpx) — \"Tempo esgotado\".",
        "Falha ao executar uma tool (ToolFailedError/ToolRetryError) — \"Falha na consulta\".",
        "Nome de tool inválido ou comportamento inesperado do modelo "
        "(UnexpectedModelBehavior, incluindo o sufixo <|channel|>) — \"Falha ao "
        "interpretar a consulta\".",
        "Falha genérica de comunicação com a API (ModelAPIError) ou qualquer exceção não "
        "prevista — mensagem genérica de falha.",
        "Resposta vazia ou de tipo inesperado devolvida pelo agente — \"Resposta inválida\".",
    ]),
    ("h2", "9.3 Limitações conhecidas"),
    ("bullets", [
        "O agente sempre responde em texto puro (TextQueryResult); os tipos table, chart "
        "e combined existem no contrato da API, mas não são produzidos pela implementação "
        "real do agente — apenas pelo mock local do front-end.",
        "Armazenamento somente em memória, por processo: reiniciar o backend apaga todos "
        "os datasets carregados e o histórico de perguntas; não há banco de dados.",
        "Um único agente, sem arquitetura multiagente — o enunciado sugere múltiplos "
        "agentes especializados como boa prática, mas não como requisito obrigatório, e "
        "este projeto usa um agente só.",
        "Resultados de tools limitados a 10 linhas e ~7.000 caracteres por chamada; "
        "perguntas muito amplas sobre tabelas grandes podem precisar ser refeitas de "
        "forma mais específica pelo próprio usuário.",
        "Sem autenticação ou autorização nas rotas da API.",
        "CORS liberado apenas para localhost por padrão (ajustável pela variável de "
        "ambiente CORS_ORIGINS).",
    ]),

    ("h1", "10. Conclusão"),
    ("p",
     "O CSV Insight atende aos requisitos mínimos do Desafio 4: permite o upload de um "
     "ZIP com um ou mais CSVs, processa o pacote automaticamente, disponibiliza uma "
     "interface de consulta em linguagem natural e usa um framework de agentes "
     "(Pydantic AI) para interpretar as perguntas do usuário sobre os dados carregados."),
    ("p",
     "As principais capacidades demonstradas são a ingestão segura de ZIP/CSV com "
     "limpeza conservadora dos dados, cinco tools tipadas que expõem diferentes formas de "
     "consulta (colunas, resumo, amostra, filtro e estatística) e um agente Pydantic AI + "
     "Groq que decide, a cada pergunta, quais dessas tools chamar e em que ordem. O papel "
     "do agente é justamente esse: transformar uma pergunta em linguagem natural em uma "
     "ou mais consultas estruturadas sobre os dados já carregados, sem exigir que o "
     "usuário conheça SQL ou a estrutura interna das tabelas."),
    ("p",
     "Como evoluções futuras, ficam abertas: fazer o agente realmente produzir respostas "
     "em tabela ou gráfico (hoje só em texto, apesar de o contrato da API já suportar "
     "esses formatos), persistir os datasets em um banco de dados em vez de memória, "
     "adotar uma arquitetura multiagente (por exemplo, um agente por tipo de análise) e "
     "adicionar autenticação de usuários."),
]
