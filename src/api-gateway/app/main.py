"""api-gateway — porta de entrada única do Arquiteto Decisor (ADR 0002).

Concentra responsabilidades de borda para que os serviços de domínio fiquem
enxutos:
  • roteamento/agregação para decisions-service e catalog-service;
  • rate limiting (proteção contra abuso e sobrecarga);
  • circuit breaker por upstream (pybreaker) — para de chamar um serviço em
    falha e responde rápido (fail-fast), evitando falhas em cascata;
  • timeouts explícitos em toda chamada de saída.
"""
from __future__ import annotations

import os

import httpx
import pybreaker
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .rate_limit import allow

DECISIONS_URL = os.getenv("DECISIONS_URL", "http://localhost:8002")
CATALOG_URL = os.getenv("CATALOG_URL", "http://localhost:8001")
UPSTREAM_TIMEOUT = float(os.getenv("UPSTREAM_TIMEOUT", "3.0"))

app = FastAPI(
    title="Arquiteto Decisor — API Gateway",
    version="1.0.0",
    description="Entrada única: roteamento, rate limiting e circuit breaker.",
)

# Um disjuntor por upstream isola falhas (também é uma forma de bulkhead):
# abre após 5 falhas consecutivas e tenta recuperação após 30s.
_breakers = {
    "decisions": pybreaker.CircuitBreaker(fail_max=5, reset_timeout=30, name="decisions"),
    "catalog": pybreaker.CircuitBreaker(fail_max=5, reset_timeout=30, name="catalog"),
}
_targets = {"decisions": DECISIONS_URL, "catalog": CATALOG_URL}


@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    caller_ip = request.client.host if request.client else "anon"
    client_id = request.headers.get("x-api-key") or caller_ip
    if not allow(client_id):
        return JSONResponse(status_code=429, content={"detail": "Limite de requisições excedido"})
    return await call_next(request)


@app.get("/health", tags=["infra"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "api-gateway"}


def _forward(service: str, method: str, path: str, body: dict | None = None) -> JSONResponse:
    """Encaminha a requisição ao upstream protegido por circuit breaker + timeout."""
    breaker = _breakers[service]
    url = f"{_targets[service]}{path}"

    def _call():
        with httpx.Client(timeout=UPSTREAM_TIMEOUT) as client:
            return client.request(method, url, json=body)

    try:
        resp = breaker.call(_call)
    except pybreaker.CircuitBreakerError:
        # Disjuntor aberto: resposta imediata, sem sobrecarregar o upstream em falha.
        detail = f"{service} indisponível (circuit aberto)"
        return JSONResponse(status_code=503, content={"detail": detail})
    except httpx.HTTPError:
        return JSONResponse(status_code=502, content={"detail": f"Falha ao contatar {service}"})

    media = resp.headers.get("content-type", "")
    payload = resp.json() if media.startswith("application/json") else {"raw": resp.text}
    return JSONResponse(status_code=resp.status_code, content=payload)


# ─────────────────────────── Rotas de catálogo ────────────────────────────
@app.get("/api/systems", tags=["catalog"])
def list_systems():
    return _forward("catalog", "GET", "/systems")


@app.post("/api/systems", tags=["catalog"])
async def create_system(request: Request):
    return _forward("catalog", "POST", "/systems", await request.json())


# ─────────────────────────── Rotas de decisões ────────────────────────────
@app.get("/api/decisions", tags=["decisions"])
def list_decisions():
    return _forward("decisions", "GET", "/decisions")


@app.post("/api/decisions", tags=["decisions"])
async def create_decision(request: Request):
    return _forward("decisions", "POST", "/decisions", await request.json())


@app.post("/api/decisions/{decision_id}/approve", tags=["decisions"])
def approve_decision(decision_id: str):
    return _forward("decisions", "POST", f"/decisions/{decision_id}/approve")
