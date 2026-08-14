# -*- coding: utf-8 -*-
"""Fonte do relatório em linguagem acessível (versão para Google Docs).

Reaproveita o layout de build_docx.py, mas com um conteúdo reescrito para um
público sem background técnico. Editar este arquivo é o jeito certo de
preencher a capa e as respostas pendentes da seção de perguntas.
"""

COVER = {
    "program": "InsurMinds",
    "subtitle": "Inteligência Artificial Aplicada a Seguros",
    "challenge": "Desafio 4",
    "title": "Interface Inteligente para Consulta de Arquivos CSV",
    "project_name": "CSV Insight",
    "group_name": "[a preencher]",
    "members": "[a preencher]",
    "date": "14 de agosto de 2026",
}

# Tipos de bloco: h1, h2, h3, p, bullets, numbered, table, image, flow, qa, pagebreak
BLOCKS = [
    ("h1", "1. O projeto"),
    ("p",
     "Toda empresa acumula planilhas cheias de informação útil: notas fiscais, pedidos, "
     "cadastros, sinistros. O problema raramente é a falta de dado, e sim o acesso a ele. "
     "Para tirar uma resposta simples de um arquivo desses, alguém normalmente precisa "
     "abrir uma planilha, aplicar filtros à mão ou escrever uma consulta em SQL, algo que "
     "a maior parte das pessoas de negócio não sabe fazer, e não deveria precisar aprender "
     "só para saber qual fornecedor recebeu mais em um mês."),
    ("p",
     "O CSV Insight nasceu para encurtar essa distância. A ideia é simples: a pessoa envia "
     "o arquivo e, a partir daí, pode perguntar o que quiser sobre ele, em português, do "
     "jeito que perguntaria a um colega que conhece a planilha de cor. Por trás da "
     "pergunta, uma inteligência artificial cuida de encontrar e organizar a resposta, sem "
     "que ninguém precise abrir o arquivo ou entender sua estrutura interna."),
    ("p",
     "Este relatório apresenta essa solução: o problema que ela resolve, como os dados são "
     "recebidos e organizados, o papel do agente que interpreta as perguntas, e exemplos "
     "de uso."),

    ("h1", "2. Como a solução funciona"),
    ("flow", ["O usuário envia o arquivo", "o sistema organiza os dados", "o usuário faz uma pergunta",
              "o agente interpreta a pergunta", "o agente consulta os dados", "a resposta aparece na tela"]),
    ("p",
     "Tudo começa com o envio de um arquivo compactado contendo uma ou mais planilhas em "
     "formato CSV. Assim que o envio termina, a aplicação lê esse conteúdo, organiza cada "
     "planilha como uma tabela consultável e libera automaticamente a tela de conversa, "
     "sem que o usuário precise configurar nada."),
    ("p",
     "A partir daí, a experiência lembra uma troca de mensagens comum. A pessoa escreve a "
     "pergunta como escreveria para um colega, por exemplo \"qual fornecedor recebeu o "
     "maior valor no período\". O agente lê essa pergunta, decide o que precisa verificar "
     "nos dados, faz essa verificação e devolve a resposta em texto corrido, sem termos "
     "técnicos nem fórmulas."),
    ("p",
     "Cada pergunta é independente: o usuário pode perguntar quantas vezes quiser sobre o "
     "mesmo arquivo, em qualquer ordem, sem enviar o arquivo de novo a cada consulta."),

    ("h1", "3. Arquitetura da solução"),
    ("p",
     "Por trás da conversa simples que o usuário vê, existem algumas partes conectadas "
     "entre si, cada uma com uma função clara."),
    ("image", "arquitetura_simples.png", "Como as partes da solução se conectam."),
    ("bullets", [
        "Usuário: a pessoa que envia o arquivo e faz as perguntas.",
        "Interface: a tela onde isso acontece, dividida em duas partes, uma para enviar o "
        "arquivo e outra para conversar sobre ele.",
        "Backend: a parte da aplicação que recebe o arquivo e as perguntas, organiza os "
        "dados e aciona o agente de inteligência artificial.",
        "Agente de IA: quem lê a pergunta, decide o que precisa descobrir e monta a "
        "resposta.",
        "Ferramentas de consulta: os recursos que o agente usa para efetivamente buscar "
        "informação nos dados, sem nunca inventar um resultado.",
        "Dados processados: as tabelas já organizadas e prontas para consulta, disponíveis "
        "enquanto a pessoa está usando a aplicação.",
    ]),

    ("h1", "4. Preparação dos dados"),
    ("p",
     "Quando o arquivo chega, a aplicação abre o pacote compactado e localiza cada CSV "
     "dentro dele. Se houver também um dicionário de dados, ou seja, uma planilha "
     "descrevendo o que cada coluna significa, esse dicionário é lido e usado para "
     "entender melhor o conteúdo das tabelas."),
    ("p",
     "Cada CSV se torna uma tabela própria, com colunas e linhas organizadas. Antes de "
     "ficar disponível para consulta, porém, os dados passam por uma limpeza cuidadosa: "
     "registros completamente vazios são descartados, linhas duplicadas de forma idêntica "
     "são removidas, e cada coluna é observada para identificar se contém números, datas "
     "ou texto."),
    ("p",
     "Essa limpeza foi pensada para ser conservadora. Sempre que existe qualquer dúvida "
     "sobre como converter um valor, por exemplo um número escrito de um jeito pouco "
     "comum, a aplicação prefere manter o dado como está a arriscar mudar seu significado "
     "original. A prioridade, do início ao fim desse processo, é preservar a informação "
     "tal como foi enviada."),
    ("p",
     "Terminada essa etapa, os dados ficam disponíveis para consulta durante o tempo em "
     "que a aplicação está em uso, permitindo que o usuário faça quantas perguntas quiser "
     "sem enviar o arquivo novamente."),

    ("h1", "5. O agente inteligente"),
    ("p",
     "O centro da aplicação é um agente de inteligência artificial construído com o "
     "framework Pydantic AI, responsável por interpretar as perguntas em português e "
     "decidir como respondê-las. Para gerar o texto das respostas, o agente usa o modelo "
     "GPT-OSS, executado pela Groq, um serviço especializado em rodar modelos de "
     "linguagem com respostas rápidas."),
    ("p",
     "Um agente se diferencia de uma inteligência artificial comum porque não apenas "
     "conversa: ele age. Ao receber uma pergunta, primeiro entende o que está sendo "
     "pedido, depois identifica quais informações precisa localizar, escolhe entre um "
     "conjunto de recursos de consulta o mais adequado para aquele caso, e só então usa "
     "esse recurso para buscar a resposta nos dados que foram carregados. O texto final "
     "que a pessoa lê é montado a partir do que foi efetivamente encontrado, não de uma "
     "suposição."),
    ("p",
     "Essa diferença importa: o agente não recebe o arquivo inteiro de uma vez para "
     "adivinhar uma resposta plausível. Ele consulta especificamente a parte dos dados "
     "relevante para cada pergunta, e quando não encontra informação suficiente, diz isso "
     "com clareza em vez de inventar um número."),
    ("p",
     "Nesta versão do CSV Insight, um único agente cuida de toda essa interpretação e "
     "consulta. Essa escolha foi suficiente para atender ao objetivo do projeto: mostrar "
     "como um agente pode transformar uma planilha em algo que qualquer pessoa consegue "
     "conversar."),

    ("h1", "6. Como o agente consulta os dados"),
    ("p",
     "Para responder às perguntas, o agente tem à disposição um conjunto de recursos, cada "
     "um voltado a um tipo de necessidade:"),
    ("bullets", [
        "Conhecer a estrutura das tabelas: descobrir quais colunas existem e o que cada "
        "uma representa (listar_colunas).",
        "Obter uma visão geral dos dados: saber quantas tabelas, linhas e colunas o "
        "arquivo enviado contém (obter_resumo).",
        "Localizar registros: trazer exemplos ou trechos específicos de uma tabela "
        "(buscar_registros).",
        "Aplicar filtros: selecionar apenas os registros que atendem a uma condição, como "
        "valores acima de um determinado limite (filtrar_dados).",
        "Calcular totais, médias, mínimos, máximos e frequências: obter números resumidos "
        "sobre uma coluna, como o valor total ou os itens mais comuns "
        "(calcular_estatisticas).",
    ]),
    ("p",
     "O agente escolhe entre esses recursos conforme a pergunta, podendo até combinar mais "
     "de um antes de responder. Essa divisão de tarefas é o que garante respostas "
     "fundamentadas nos dados reais, em vez de suposições genéricas."),

    ("h1", "7. Um exemplo completo"),
    ("p",
     "Para entender esse processo do começo ao fim, imagine que alguém envia um conjunto "
     "de planilhas com notas fiscais recebidas ao longo de um mês. Depois que os arquivos "
     "são processados, a pessoa pergunta: \"qual fornecedor recebeu o maior valor no "
     "período?\""),
    ("p",
     "O agente identifica quais colunas da tabela representam o fornecedor e o valor de "
     "cada nota. Em seguida, usa as ferramentas de consulta para analisar os dados "
     "carregados e chegar ao resultado. Com essa informação em mãos, monta uma resposta "
     "direta, informando o fornecedor e o valor correspondente, sem exigir que a pessoa "
     "soubesse de antemão o nome da coluna ou como fazer esse cálculo sozinha."),

    ("h1", "8. Perguntas e respostas"),
    ("p",
     "A seguir, alguns exemplos de perguntas que a aplicação é capaz de responder, "
     "cobrindo diferentes formas de explorar os dados: uma visão geral, um total, um "
     "filtro e um ranking."),
    ("qa", "Quantas tabelas esse conjunto de dados tem, e quantos registros ao todo?"),
    ("qa", "Qual foi o valor total registrado nesta base de dados?"),
    ("qa", "Quais registros têm valor acima de R$ 5.000?"),
    ("qa", "Quais são os cinco valores mais frequentes nesta coluna?"),

    ("h1", "9. Tecnologias utilizadas"),
    ("p", "A solução combina algumas tecnologias, cada uma cuidando de uma parte do processo:"),
    ("bullets", [
        "React, para construir a interface que o usuário vê e usa.",
        "FastAPI, para conectar essa interface ao processamento que acontece nos "
        "bastidores.",
        "Pandas, para preparar e organizar os dados enviados.",
        "Pydantic AI, o framework que estrutura o agente de inteligência artificial.",
        "Groq e GPT-OSS, responsáveis por interpretar as perguntas e gerar as respostas "
        "em linguagem natural.",
    ]),

    ("h1", "10. Limitações e próximos passos"),
    ("p",
     "Como todo protótipo, o CSV Insight tem um escopo definido, pensado para demonstrar "
     "bem o essencial sem se estender além do necessário. Hoje, as respostas do agente são "
     "principalmente em texto, os dados ficam disponíveis apenas durante o uso da "
     "aplicação, e um único agente cuida de toda a interpretação das perguntas."),
    ("p",
     "Esses pontos apontam caminhos naturais de evolução: apresentar respostas também em "
     "tabelas e gráficos, manter os dados guardados entre uma sessão e outra, e dividir o "
     "trabalho entre agentes especializados em diferentes tipos de análise."),

    ("h1", "11. Conclusão"),
    ("p",
     "O CSV Insight parte de um problema comum, o de planilhas cheias de dados que poucas "
     "pessoas sabem explorar, e propõe um caminho direto para resolvê-lo: enviar o "
     "arquivo e conversar com ele em português. A interface recebe e organiza os dados, o "
     "agente interpreta cada pergunta, e as ferramentas de consulta garantem que toda "
     "resposta esteja apoiada em informação real, não em suposição."),
    ("p",
     "É essa integração entre interface, processamento dos dados e agente inteligente que "
     "transforma um arquivo CSV comum em algo que qualquer pessoa consegue consultar, sem "
     "depender de conhecimento técnico para chegar à resposta que precisa."),
]
