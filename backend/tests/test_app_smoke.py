"""Teste de fumaça HTTP sem credencial real da Groq."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_app_answers_question_with_safe_error_when_api_key_is_missing(
    monkeypatch, stored_dataset_id
):
    # Importar o app antes de remover a variável cobre o comportamento real de
    # load_dotenv(), sem permitir uma chamada externa durante o teste.
    import main

    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    client = TestClient(main.app)
    response = client.post(
        f"/api/datasets/{stored_dataset_id}/questions",
        json={"question": "Quantos fornecedores existem?"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["type"] == "error"
