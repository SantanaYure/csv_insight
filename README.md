# CSV Insight

LINK PARA A PÁGINA EM PRODUÇÃO: https://csv-insight-indol.vercel.app/

O CSV Insight permite enviar arquivos CSV, ou um arquivo ZIP com vários CSVs, e fazer perguntas sobre os dados em linguagem comum. Por exemplo: **"Qual foi o total de vendas?"**.

O projeto tem duas partes:

- `frontend/`: a tela que abre no navegador, feita com React e Vite;
- `backend/`: a API que processa os arquivos e consulta a inteligência artificial, feita com Python e FastAPI.

## 1. O que precisa estar instalado

Antes de começar, instale:

- [Node.js](https://nodejs.org/) `20.19` ou mais recente;
- [Python](https://www.python.org/downloads/) `3.10` ou mais recente;
- [Git](https://git-scm.com/downloads), caso queira clonar o projeto;
- uma chave da [API Groq](https://console.groq.com/keys), necessária para fazer perguntas usando o backend.

O `npm` já é instalado junto com o Node.js.

Para conferir se está tudo instalado, abra um terminal e execute:

```bash
node --version
npm --version
python --version
git --version
```

Se algum comando não for reconhecido, instale o programa correspondente e abra o terminal novamente.

## 2. Baixar o projeto

### Opção A — clonar com Git

No terminal, execute:

```bash
git clone https://github.com/SantanaYure/csv_insight.git
cd csv_insight
```

### Opção B — baixar como ZIP

1. Acesse o [repositório no GitHub](https://github.com/SantanaYure/csv_insight).
2. Clique em **Code** e depois em **Download ZIP**.
3. Extraia o arquivo ZIP.
4. Abra um terminal dentro da pasta extraída.

Todos os comandos abaixo partem da pasta principal do projeto, onde este `README.md` está localizado.

## 3. Instalar o frontend

Entre na pasta do frontend e instale as dependências:

```bash
cd frontend
npm install
cd ..
```

## 4. Instalar o backend

Primeiro, entre na pasta do backend e crie um ambiente virtual. Isso mantém as dependências Python deste projeto separadas das demais.

```bash
cd backend
python -m venv .venv
```

Ative o ambiente virtual.

No Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

No Prompt de Comando do Windows:

```bat
.venv\Scripts\activate.bat
```

No macOS ou Linux:

```bash
source .venv/bin/activate
```

Depois, instale as dependências:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cd ..
```

Quando o ambiente estiver ativo, normalmente aparecerá `(.venv)` no início da linha do terminal.

## 5. Configurar as variáveis de ambiente

O frontend e o backend possuem configurações separadas. Por isso, cada pasta precisa do seu próprio arquivo `.env`.

### Frontend

Crie `frontend/.env` a partir do arquivo de exemplo.

No Windows PowerShell:

```powershell
Copy-Item frontend/.env.example frontend/.env
```

No macOS ou Linux:

```bash
cp frontend/.env.example frontend/.env
```

O arquivo deve ficar assim:

```env
VITE_USE_MOCKS=false
VITE_API_URL=http://localhost:8000/api
```

| Variável | Para que serve |
| --- | --- |
| `VITE_USE_MOCKS` | Com `false`, o frontend usa o backend. Com `true`, processa os arquivos localmente no navegador. |
| `VITE_API_URL` | Endereço da API usada pelo frontend. Para execução local, mantenha `http://localhost:8000/api`. |

### Backend

Crie `backend/.env` a partir do arquivo de exemplo.

No Windows PowerShell:

```powershell
Copy-Item backend/.env.example backend/.env
```

No macOS ou Linux:

```bash
cp backend/.env.example backend/.env
```

Abra `backend/.env` e informe sua chave da Groq:

```env
GROQ_API_KEY=coloque_sua_chave_aqui
GROQ_MODEL=openai/gpt-oss-20b
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
CORS_ORIGIN_REGEX=^https?://(localhost|127\.0\.0\.1)(:\d+)?$
```

| Variável | Para que serve |
| --- | --- |
| `GROQ_API_KEY` | Chave de acesso à API Groq. É obrigatória para responder perguntas com inteligência artificial. |
| `GROQ_MODEL` | Modelo usado pela Groq. O valor padrão já está pronto para uso. |
| `CORS_ORIGINS` | Endereços do frontend autorizados a acessar o backend. |
| `CORS_ORIGIN_REGEX` | Permite que o Vite use outra porta local caso a porta `5173` esteja ocupada. |

Não compartilhe sua `GROQ_API_KEY` e não envie os arquivos `.env` para o GitHub.

## 6. Rodar o projeto

É necessário deixar dois terminais abertos: um para o backend e outro para o frontend.

### Terminal 1 — backend

Entre na pasta `backend`, ative o ambiente virtual e inicie a API.

Windows PowerShell:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload
```

macOS ou Linux:

```bash
cd backend
source .venv/bin/activate
python -m uvicorn main:app --reload
```

O backend ficará disponível em:

- API: [http://localhost:8000](http://localhost:8000)
- verificação de funcionamento: [http://localhost:8000/health](http://localhost:8000/health)
- documentação da API: [http://localhost:8000/docs](http://localhost:8000/docs)

### Terminal 2 — frontend

Em outro terminal, partindo da pasta principal do projeto, execute:

```bash
cd frontend
npm run dev
```

Abra no navegador o endereço exibido no terminal. Normalmente será:

[http://localhost:5173](http://localhost:5173)

Para encerrar o frontend ou o backend, volte ao terminal correspondente e pressione `Ctrl + C`.

## 7. Rodar somente o frontend, sem backend ou chave da Groq

Se quiser apenas testar a interface e o processamento local:

1. Abra `frontend/.env`.
2. Altere `VITE_USE_MOCKS=false` para `VITE_USE_MOCKS=true`.
3. Execute `npm run dev` dentro de `frontend/`.

Nesse modo, não é necessário iniciar o backend. Os dados são processados no navegador e ficam disponíveis apenas durante a sessão.

## 8. Como usar

1. Abra o frontend no navegador.
2. Acesse a tela de upload.
3. Envie um arquivo `.csv` ou `.zip` contendo um ou mais arquivos CSV.
4. Aguarde o processamento.
5. Faça perguntas sobre os dados carregados.

O dicionário de dados é opcional. Se ele não for enviado, o sistema tenta identificar os tipos das colunas automaticamente.

Os datasets do backend ficam armazenados em memória. Ao reiniciar o backend, será necessário enviar os arquivos novamente.

## 9. Verificar se tudo está correto

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

Backend, com o ambiente virtual ativo:

```bash
cd backend
python -m pytest -v
```

## Problemas comuns

### `python` não foi encontrado

No Windows, tente usar `py` no lugar de `python`. Exemplo:

```powershell
py -m venv .venv
```

### O PowerShell bloqueou a ativação do ambiente virtual

Execute o comando abaixo no mesmo terminal e tente ativar novamente:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Essa alteração vale somente para o terminal atual.

### O frontend abre, mas não consegue acessar a API

Confirme se:

- o backend está rodando em `http://localhost:8000`;
- `VITE_USE_MOCKS` está como `false`;
- `VITE_API_URL` está como `http://localhost:8000/api`;
- o frontend foi reiniciado depois de qualquer alteração no arquivo `.env`.

### A pergunta retorna erro de configuração

Confira se `GROQ_API_KEY` foi preenchida em `backend/.env` e reinicie o backend.

### Uma porta já está em uso

Encerre o programa que usa a porta ou inicie o serviço em outra porta. Exemplo para o backend:

```bash
python -m uvicorn main:app --reload --port 8001
```

Se mudar a porta do backend, atualize também `VITE_API_URL` em `frontend/.env` para o mesmo número, por exemplo `http://localhost:8001/api`, e reinicie o frontend.
