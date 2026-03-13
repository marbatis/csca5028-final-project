# CSCA 5028 Final Project

This repository contains the complete final project submission package for:

The '87 Land Cruiser Finder: Event-Driven Data Pipeline and Web Application

## Live Web URL

https://csca5028-echo-mb-final-0313-6f06d76737c3.herokuapp.com/

## Repository Contents

1. `csca5028-webapp-echo`
   - Flask web app
   - `/echo` endpoint
   - `/health` endpoint for monitoring
   - unit and integration tests

2. `csca5028-land-cruiser-data-collection`
   - collector (external API ingestion)
   - analyzer (summary metrics)
   - optional RabbitMQ event collaboration (`producer` + `consumer`)
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

### Optional event collaboration (RabbitMQ)

```bash
cd csca5028-land-cruiser-data-collection
./scripts/run_rabbitmq_local.sh
python scripts/consume_inventory_events.py
./scripts/run_pipeline_with_events.sh
```
