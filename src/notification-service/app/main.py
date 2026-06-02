"""notification-service — reage a eventos de domínio de forma assíncrona.

Expõe apenas um /health para o orquestrador; o trabalho real acontece no
consumidor AMQP, iniciado numa thread em segundo plano para não bloquear o
servidor HTTP.
"""
from __future__ import annotations

import logging
import threading

from fastapi import FastAPI

from .consumer import start_consuming

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Arquiteto Decisor — Notification Service",
    version="1.0.0",
    description="Consumidor de eventos que notifica os times quando uma decisão é aprovada.",
)


@app.on_event("startup")
def _launch_consumer() -> None:
    thread = threading.Thread(target=start_consuming, name="amqp-consumer", daemon=True)
    thread.start()


@app.get("/health", tags=["infra"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "notification-service"}
