"""Rate limiting do gateway (janela fixa por minuto).

Usa Redis quando disponível (estado compartilhado entre réplicas do gateway —
essencial para escalabilidade horizontal, ADR 0001). Sem Redis, cai para um
contador em memória, suficiente para desenvolvimento local.
"""
from __future__ import annotations

import os
import time
from collections import defaultdict

LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
REDIS_URL = os.getenv("REDIS_URL", "")

_redis = None
if REDIS_URL:
    try:  # pragma: no cover - depende de infraestrutura
        import redis

        _redis = redis.from_url(REDIS_URL)
        _redis.ping()
    except Exception:
        _redis = None

# Fallback em memória: { client_id: (window_epoch_minute, count) }
_local: dict[str, list] = defaultdict(lambda: [0, 0])


def allow(client_id: str) -> bool:
    """Retorna True se a requisição do cliente está dentro do limite."""
    window = int(time.time() // 60)

    if _redis is not None:  # pragma: no cover
        key = f"rl:{client_id}:{window}"
        count = _redis.incr(key)
        if count == 1:
            _redis.expire(key, 60)
        return count <= LIMIT

    state = _local[client_id]
    if state[0] != window:
        state[0], state[1] = window, 0
    state[1] += 1
    return state[1] <= LIMIT
