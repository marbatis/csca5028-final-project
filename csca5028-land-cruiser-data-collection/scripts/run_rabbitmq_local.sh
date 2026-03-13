#!/usr/bin/env bash
set -euo pipefail

docker run -d --rm \
  --name csca5028-rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  rabbitmq:4-management

echo "RabbitMQ started at amqp://localhost:5672"
echo "Management UI: http://localhost:15672 (guest/guest)"
