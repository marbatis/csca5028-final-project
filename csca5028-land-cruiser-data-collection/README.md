# CSCA 5028 Final Project - Land Cruiser Finder

This repository contains the data components of the capstone project:

1. Data collector (external API ingestion)
2. Data analyzer (reporting rollups)
3. Event collaboration integration (RabbitMQ producer/consumer)

## Architecture (high level)

```text
External API (NHTSA vPIC)
        |
        v
Collector -----------------> RabbitMQ (inventory_events)
        |                              |
        v                              v
SQLite raw_inventory            Event Consumer / Downstream services
        |
        v
Analyzer (counts, averages, trends)
```

## External API

- `https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeYear/make/toyota/modelyear/{year}?format=json`

## Database

- SQLite file: `data/land_cruiser.sqlite3`
- Migration: `migrations/001_create_raw_inventory.sql`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run collector + analyzer (no message broker required)

```bash
./scripts/run_pipeline.sh
```

## Event collaboration (RabbitMQ)

Start RabbitMQ locally:

```bash
./scripts/run_rabbitmq_local.sh
```

Run consumer in one terminal:

```bash
python scripts/consume_inventory_events.py
```

Run pipeline with publishing enabled in another terminal:

```bash
./scripts/run_pipeline_with_events.sh
```

The collector publishes an `inventory.collection.completed` event to queue `inventory_events`.

## Analysis only

```bash
python scripts/analyze_data.py
```

## Show current records

```bash
python scripts/show_sample.py
```

