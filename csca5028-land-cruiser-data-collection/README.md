# CSCA 5028 Final Project - Land Cruiser Finder

This repository contains the data components of the capstone project:

1. Data collector (external API ingestion)
2. Data analyzer (reporting rollups)
3. Event collaboration integration (RabbitMQ producer/consumer)

## Architecture (high level)

```text
External APIs (NHTSA vPIC, NHTSA Recalls, FuelEconomy.gov)
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

## External APIs used

- `https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeYear/make/toyota/modelyear/{year}?format=json`
- `https://api.nhtsa.gov/recalls/recallsByVehicle?make=TOYOTA&model=LAND%20CRUISER&modelYear={year}`
- `https://www.fueleconomy.gov/ws/rest/vehicle/menu/model?year={year}&make=Toyota`

## Database

- SQLite file: `data/land_cruiser.sqlite3`
- Migration: `migrations/001_create_raw_inventory.sql`
- Upsert key: `(source, external_id, model_year)`

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

## Frequent scheduled collection (local)

Run collector repeatedly (default every 60 minutes):

```bash
MODE=loop COLLECT_INTERVAL_MINUTES=60 ./scripts/run_collector.sh
```

Run exactly 3 times every 10 minutes (test mode):

```bash
MODE=loop COLLECT_INTERVAL_MINUTES=10 COLLECT_MAX_RUNS=3 ./scripts/run_collector.sh
```

## Frequent scheduled collection (cron / Heroku Scheduler)

Cron example (hourly):

```bash
0 * * * * cd /path/to/csca5028-land-cruiser-data-collection && /usr/bin/env python scripts/fetch_inventory.py
```

Heroku Scheduler command example:

```bash
python scripts/fetch_inventory.py
```

Optional environment variables:

- `YEAR_START` (default: `1980`)
- `YEAR_END` (default: `1990`)
- `EVENT_COLLAB_ENABLED=1` to publish RabbitMQ events

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
