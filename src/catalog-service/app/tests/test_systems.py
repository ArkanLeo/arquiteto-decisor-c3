"""Testes de fumaça do catalog-service usando SQLite local.

O TestClient é usado como context manager para disparar o evento de startup
(criação das tabelas) antes das requisições.
"""
import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app


@pytest.fixture()
def client():
    # Schema limpo a cada teste, garantindo isolamento e re-execução.
    Base.metadata.drop_all(engine)
    with TestClient(app) as c:  # o startup recria as tabelas
        yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "catalog-service"


def test_create_and_get_system(client):
    created = client.post(
        "/systems",
        json={"name": "checkout", "team": "Payments", "description": "Fluxo de pagamento"},
    )
    assert created.status_code == 201
    system_id = created.json()["id"]

    fetched = client.get(f"/systems/{system_id}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "checkout"


def test_duplicate_system_conflicts(client):
    client.post("/systems", json={"name": "billing", "team": "Finance"})
    again = client.post("/systems", json={"name": "billing", "team": "Finance"})
    assert again.status_code == 409
