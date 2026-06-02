"""Consumidor assíncrono de eventos de domínio (ADR 0003).

Assina `decision.approved` no *topic exchange* `arquiteto.decisor` e reage de
forma desacoplada — o publicador (decisions-service) não sabe que este serviço
existe. A fila é durável e usa *manual ack*, garantindo entrega ao menos uma vez
(*at-least-once*): se o processamento falhar, a mensagem retorna à fila.
"""
from __future__ import annotations

import json
import logging
import os

import pika

logger = logging.getLogger("notification.consumer")

AMQP_URL = os.getenv("AMQP_URL", "")
EXCHANGE = "arquiteto.decisor"
QUEUE = "notifications.decision-approved"
ROUTING_KEY = "decision.approved"


def _handle(payload: dict) -> None:
    """Ação de negócio: aqui dispararíamos e-mail/Slack/webhook ao time dono."""
    logger.info(
        "🔔 Decisão aprovada — sistema=%s título=%r (v%s)",
        payload.get("system_id"),
        payload.get("title"),
        payload.get("version"),
    )


def start_consuming() -> None:
    """Loop bloqueante de consumo. Deve rodar em thread/processo dedicado."""
    if not AMQP_URL:
        logger.info("AMQP_URL ausente; consumidor inativo em modo local")
        return

    connection = pika.BlockingConnection(pika.URLParameters(AMQP_URL))
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    channel.queue_declare(queue=QUEUE, durable=True)
    channel.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key=ROUTING_KEY)
    channel.basic_qos(prefetch_count=10)  # bulkhead: limita mensagens em voo

    def _callback(ch, method, _properties, body):
        try:
            _handle(json.loads(body))
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:  # pragma: no cover
            logger.exception("Falha ao processar mensagem; devolvendo à fila")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    channel.basic_consume(queue=QUEUE, on_message_callback=_callback)
    logger.info("Consumidor pronto, aguardando eventos %r", ROUTING_KEY)
    channel.start_consuming()
