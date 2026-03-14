# CSCA 5028 Final Project

This repository contains the complete final project submission package for:

The '87 Land Cruiser Finder: Event-Driven Data Pipeline and Web Application

## Live Web URL

https://csca5028-echo-mb-final-0313-6f06d76737c3.herokuapp.com/

## Repository Contents

1. `csca5028-webapp-echo`
   - Flask web app
   - reporting UI (filters, summary cards, inventory table)
   - REST endpoints: `/api/v1/inventory`, `/api/v1/summary`
   - monitoring endpoints: `/health`, `/metrics`
   - unit + integration tests (including mock usage)
   - CI/CD workflows (`.github/workflows/ci.yml`, `.github/workflows/cd.yml`)

2. `csca5028-land-cruiser-data-collection`
   - collector (multi-source external API ingestion)
   - analyzer (summary metrics)
   - optional RabbitMQ event collaboration (`producer` + `consumer`)
   - scheduled collection support (loop mode + cron/Heroku Scheduler command)
   - schema migration and data scripts

3. `csca5028_final_project_submission`
   - final project report (Markdown + DOCX)
   - submission field references

## Quick Start

### Web app

```bash
cd csca5028-webapp-echo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m flask --app src.app run
```

### Data pipeline

```bash
cd csca5028-land-cruiser-data-collection
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./scripts/run_pipeline.sh
```

### Scheduled collector (frequent runs)

```bash
cd csca5028-land-cruiser-data-collection
MODE=loop COLLECT_INTERVAL_MINUTES=60 ./scripts/run_collector.sh
```

### Optional event collaboration (RabbitMQ)

```bash
cd csca5028-land-cruiser-data-collection
./scripts/run_rabbitmq_local.sh
python scripts/consume_inventory_events.py
./scripts/run_pipeline_with_events.sh
```
