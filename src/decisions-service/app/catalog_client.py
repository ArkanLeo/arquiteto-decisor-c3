"""Cliente síncrono para o catalog-service.

Demonstra comunicação **síncrona** (REST) entre serviços de domínio. Aplica
*timeout* explícito — um dos padrões de resiliência (ADR 0002): nenhuma chamada
de saída pode bloquear indefinidamente.
"""
from __future__ import annotations

import os

import httpx

CATALOG_URL = os.getenv("CATALOG_URL", "http://localhost:8001")
TIMEOUT_SECONDS = float(os.getenv("CATALOG_TIMEOUT", "2.0"))


class CatalogUnavailable(RuntimeError):
    """Sinaliza que o catálogo não respondeu dentro do timeout."""


def system_exists(system_id: str) -> bool:
    """Valida a existência de um sistema. Falha fechada em caso de indisponibilidade."""
    try:
        resp = httpx.get(f"{CATALOG_URL}/systems/{system_id}", timeout=TIMEOUT_SECONDS)
    except httpx.HTTPError as exc:  # timeout, conexão recusada, DNS, etc.
        raise CatalogUnavailable(str(exc)) from exc
    return resp.status_code == 200
