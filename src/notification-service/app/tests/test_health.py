"""Teste de fumaça do notification-service (sem broker: consumidor fica inativo)."""
from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["service"] == "notification-service"
