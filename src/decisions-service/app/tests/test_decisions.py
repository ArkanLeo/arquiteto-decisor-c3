"""Testes de fumaça do decisions-service.

O catálogo (chamada síncrona) e o broker (publicação assíncrona) são
substituídos por dublês, isolando o serviço de dependências externas. O
TestClient roda como context manager para disparar o startup (criação de
tabelas) antes das requisições.
"""
import pytest
from fastapi.testclient import TestClient

import app.main as main
from app.db import Base, engine


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(main, "system_exists", lambda system_id: True)
    monkeypatch.setattr(main, "publish_decision_approved", lambda payload: True)
    # Schema limpo a cada teste, garantindo isolamento e re-execução.
    Base.metadata.drop_all(engine)
    with TestClient(main.app) as c:  # o startup recria as tabelas
        yield c


def test_health(client):
    assert client.get("/health").json()["service"] == "decisions-service"


def test_create_and_approve_decision(client):
    created = client.post(
        "/decisions",
        json={"system_id": "sys-1", "title": "Adotar Circuit Breaker", "decision": "Sim"},
    )
    assert created.status_code == 201
    decision_id = created.json()["id"]
    assert created.json()["status"] == "proposed"

    approved = client.post(f"/decisions/{decision_id}/approve")
    assert approved.status_code == 200
    assert approved.json()["status"] == "accepted"


def test_create_rejects_unknown_system(client, monkeypatch):
    monkeypatch.setattr(main, "system_exists", lambda system_id: False)
    resp = client.post(
        "/decisions",
        json={"system_id": "ghost", "title": "Decisão órfã"},
    )
    assert resp.status_code == 422
