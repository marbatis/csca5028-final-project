from pathlib import Path
import sys
import os
import json

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pika


def main() -> None:
    host = os.getenv("RABBITMQ_HOST", "localhost")
    queue = os.getenv("RABBITMQ_QUEUE", "inventory_events")

    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
    channel = connection.channel()
    channel.queue_declare(queue=queue, durable=True)

    def callback(ch, method, properties, body):
        payload = json.loads(body.decode("utf-8"))
        print(f"Received event: {payload}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=queue, on_message_callback=callback)
    print(f"Listening for events on queue '{queue}' at host '{host}' (CTRL+C to stop)")
    channel.start_consuming()


if __name__ == "__main__":
    main()
