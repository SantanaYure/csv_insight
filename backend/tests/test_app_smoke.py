"""Teste de fumaça HTTP: garante que o app sobe e responde mesmo sem
`GROQ_API_KEY` configurada, exercitando a rota real (não `agent_service`
diretamente). Isso prova a alegação de que "o contrato HTTP não muda" e que
uma falha de configuração vira um `QueryResult` do tipo `error`, não uma
exceção que derrubaria o app inteiro na inicialização."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_app_answers_question_with_safe_error_when_api_key_is_missing(
    monkeypatch, stored_dataset_id
):
    # Importar `main` aqui (e não crashar) demonstra que o app é
    # import-safe. Isso precisa vir *antes* do `delenv`: `main.py` chama
    # `load_dotenv()` no import, que preenche `GROQ_API_KEY` a partir de
    # `backend/.env` se a variável ainda não estiver no ambiente — se
    # importássemos depois do `delenv`, o próprio import reintroduziria a
    # chave e o teste chamaria a API Groq de verdade.
    import main

    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    client = TestClient(main.app)

    response = client.post(
        f"/api/datasets/{stored_dataset_id}/questions",
        json={"question": "Quantos fornecedores existem?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["type"] == "error"
