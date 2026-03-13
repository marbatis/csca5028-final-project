import json
import os
from typing import Any


def _is_enabled() -> bool:
    return os.getenv("EVENT_COLLAB_ENABLED", "0").strip() == "1"


def publish_collection_completed(event: dict[str, Any]) -> bool:
    """Publish a summary event after a collection run.

    Publishing is optional and controlled by EVENT_COLLAB_ENABLED=1.
    This keeps the pipeline usable in environments without RabbitMQ.
    """
    if not _is_enabled():
        return False

    try:
        import pika
    except Exception as exc:  # pragma: no cover - defensive runtime fallback
        print(f"Event publishing skipped: pika unavailable ({exc})")
        return False

    host = os.getenv("RABBITMQ_HOST", "localhost")
    queue = os.getenv("RABBITMQ_QUEUE", "inventory_events")

    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        channel = connection.channel()
        channel.queue_declare(queue=queue, durable=True)
        channel.basic_publish(
            exchange="",
            routing_key=queue,
            body=json.dumps(event, ensure_ascii=True),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        connection.close()
        print(f"Published event to queue '{queue}' on host '{host}'")
        return True
    except Exception as exc:  # pragma: no cover - network-dependent path
        print(f"Event publishing skipped: RabbitMQ unavailable ({exc})")
        return False
