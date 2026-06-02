"""Testes de fumaça do gateway: health e rate limiting (sem upstreams reais)."""
import importlib
import os

from fastapi.testclient import TestClient


def _fresh_client(limit: int):
    os.environ["RATE_LIMIT_PER_MINUTE"] = str(limit)
    import app.main as main
    import app.rate_limit as rl

    importlib.reload(rl)
    importlib.reload(main)
    return TestClient(main.app)


def test_health():
    client = _fresh_client(120)
    assert client.get("/health").json()["service"] == "api-gateway"


def test_rate_limit_returns_429():
    client = _fresh_client(3)
    for _ in range(3):
        assert client.get("/health").status_code == 200
    # A quarta requisição na mesma janela deve ser barrada.
    assert client.get("/health").status_code == 429
