"""Publicação de eventos de domínio (comunicação assíncrona — ADR 0003).

Quando uma decisão é aceita, publicamos `decision.approved` num *topic exchange*
do RabbitMQ. O decisions-service não conhece nem espera os consumidores: o
acoplamento é apenas pelo contrato do evento (publish/subscribe).

A publicação é tolerante a falhas: se o broker estiver indisponível, o fluxo
HTTP principal não quebra — o evento é apenas registrado como perdido (em
produção isso seria tratado pelo padrão *transactional outbox*).
"""
from __future__ import annotations

import json
import logging
import os

import pika

logger = logging.getLogger("decisions.events")

AMQP_URL = os.getenv("AMQP_URL", "")
EXCHANGE = "arquiteto.decisor"
ROUTING_KEY = "decision.approved"


def publish_decision_approved(payload: dict) -> bool:
    """Publica o evento. Retorna True se entregue ao broker, False caso contrário."""
    if not AMQP_URL:
        logger.info("AMQP_URL ausente; evento %s suprimido em modo local", ROUTING_KEY)
        return False

    try:
        connection = pika.BlockingConnection(pika.URLParameters(AMQP_URL))
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
        channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=ROUTING_KEY,
            body=json.dumps(payload).encode("utf-8"),
            properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
        )
        connection.close()
        return True
    except Exception as exc:  # pragma: no cover - depende de broker externo
        logger.warning("Falha ao publicar %s: %s", ROUTING_KEY, exc)
        return False
