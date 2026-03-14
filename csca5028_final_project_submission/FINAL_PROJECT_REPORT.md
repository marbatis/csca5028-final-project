# CSCA 5028 Final Project Report

## Project Title
The '87 Land Cruiser Finder: Event-Driven Data Pipeline and Web Application

## 1. Product Overview
The project delivers a production-oriented system for collectors and buyers who want focused information about **actual Toyota Land Cruiser listing opportunities** (with strict emphasis on model year 1987 in the deployed web app). The system continuously ingests listing and vehicle-context data from external online sources, stores raw records, computes analysis rollups, and serves results through a deployed web application and REST endpoints.

The architecture intentionally separates responsibilities into independent processes:

1. Web app (stateless HTTP process)
2. Data collector (scheduled ingestion from online sources)
3. Data analyzer (aggregation/rollups)
4. Shared persistence (raw inventory database)
5. Event collaboration messaging (RabbitMQ producer/consumer)

## 2. Target Audience and Differentiation

- **Audience**: classic Land Cruiser buyers, collectors, and enthusiasts.
- **Problem solved**: manually tracking inventory signals across sources is repetitive and error-prone.
- **Differentiation**: combines focused vehicle-domain ingestion, analysis rollups, operational monitoring, and asynchronous event collaboration in one deployable pipeline.

## 3. High-Level Architecture

```text
                     +-------------------------------------------+
                     |  External Online Sources                  |
                     |  - Bring a Trailer (auction listings)     |
                     |  - ClassicCars.com (classified listings)  |
                     |  - NHTSA/FuelEconomy (context signals)    |
                     +-------------------+-----------------------+
                                    |
                                    v
                     +------------------------------+
Cron/Heroku Scheduler| Data Collector (independent) |
-------------------->| scripts/fetch_inventory.py   |
                     +--------------+---------------+
                                    |
                                    v
                     +------------------------------+
                     | SQLite raw_inventory         |
                     | (shared persistence backbone)|
                     +----+---------------------+---+
                          |                     |
                          v                     v
               +--------------------+   +------------------------+
               | Data Analyzer       |   | RabbitMQ Broker       |
               | scripts/analyze...  |   | inventory_events      |
               +--------------------+   +------------------------+
                                                 |
                                                 v
                                       Event consumer/downstream

                              +------------------------------+
User/browser <--------------->| Web App (Flask, stateless)  |
                              | /api/v1/inventory           |
                              | /api/v1/summary             |
                              | /health, /metrics           |
                              +------------------------------+
```

### Process and Trigger Discussion

1. **Collector trigger**: periodic schedule (cron or Heroku Scheduler) runs `scripts/fetch_inventory.py`.
2. **Analyzer trigger**: can run on schedule (`scripts/analyze_data.py`) after collection.
3. **Web app trigger**: user HTTP requests in real time.
4. **Event trigger**: collector publishes `inventory.collection.completed` to RabbitMQ.
5. Each process can run, fail, and scale independently.

## 4. Key Design Decisions and Trade-offs

### Decision A: Multi-source online ingestion
The collector fetches from multiple online sources (Bring a Trailer listings, ClassicCars.com listings, plus NHTSA/FuelEconomy contextual APIs) instead of a single endpoint.

- **Why**: improves coverage and resilience when one source is sparse or temporarily unavailable.
- **Trade-off**: requires source-specific parsing and normalized persistence schema.

### Decision B: Shared persistent data store
All components write/read through `raw_inventory` in SQLite with an idempotent upsert key `(source, external_id, model_year)`.

- **Why**: straightforward local setup and deterministic reproducibility for grading.
- **Trade-off**: SQLite is not ideal for high write concurrency compared to managed Postgres.

### Decision C: Event collaboration via RabbitMQ
Collector publishes completion events and consumers subscribe asynchronously.

- **Why**: decouples producer and consumers; enables extensibility and non-blocking downstream processing.
- **Trade-off**: eventual consistency and additional operational moving parts.

### Decision D: Operational observability in web tier
The app exposes health and metrics endpoints (`/health`, `/metrics`) and request counters.

- **Why**: supports production monitoring and failure detection.
- **Trade-off**: modest added implementation complexity.

### Decision E: CI/CD automation
GitHub Actions workflows are included for CI tests and CD deploy flow to Heroku (secret-gated).

- **Why**: automates quality gates and repeatable releases.
- **Trade-off**: requires secret management and platform setup.

## 5. Requirements and Testability

### User Requirements
1. User can view a web report of Land Cruiser inventory and filter by year/model text.
2. User can access API endpoints for inventory and summary.
3. User can verify the app is healthy and monitored in production.

### System Requirements
1. Collector must fetch data from external online sources (including real listing sources).
2. Collector must store normalized raw records in shared persistence.
3. Analyzer must compute rollup summaries.
4. Event collaboration messaging must be supported through a broker.
5. CI test automation must run on code changes.
6. CD path must exist for production deployment.

## 6. A-Level Rubric Traceability Matrix

| A-Level Rubric Item | Implementation Evidence |
|---|---|
| Web application basic form + reporting | `csca5028-webapp-echo/templates/index.html` (interaction form + reporting table + summary cards) |
| Data collection | `csca5028-land-cruiser-data-collection/scripts/fetch_inventory.py` |
| Data analyzer | `csca5028-land-cruiser-data-collection/scripts/analyze_data.py` |
| Unit tests | `csca5028-webapp-echo/tests/test_unit_input.py`, `csca5028-land-cruiser-data-collection/tests/test_fetch_inventory.py` |
| Data persistence | `raw_inventory` schema and migrations (`migrations/001_create_raw_inventory.sql`) |
| REST collaboration internal or API endpoint | Web app APIs: `/api/v1/inventory`, `/api/v1/summary` |
| Product environment | Heroku deployment URL (public production host) |
| Integration tests | `csca5028-webapp-echo/tests/test_integration_app.py` |
| Mock objects / test doubles | Mocked summary test in `test_integration_app.py` and monkeypatched collector tests |
| Continuous integration | `.github/workflows/ci.yml` |
| Production monitoring instrumenting | `/health` and `/metrics` in `src/app.py` |
| Event collaboration messaging | `collector/eventing.py`, `scripts/consume_inventory_events.py` |
| Continuous delivery | `.github/workflows/cd.yml` (Heroku secret-gated deploy) |

## 7. Validation Summary

- Web app tests: **13 passed**.
- Collector tests: **5 passed**.
- Multi-source collection run verified with marketplace inserts and per-source counts.
- Analyzer outputs total counts, year distribution, top models, and per-source distribution.
- Deployed app exposes reporting UI and operational endpoints.

## 8. Deployment and Submission Artifacts

1. **Deployed URL**  
   `https://csca5028-echo-mb-final-0313-6f06d76737c3.herokuapp.com/`

2. **Report file**  
   `csca5028_final_project_submission/output/doc/CSCA5028_Final_Project_Report.docx`

3. **Source code zip**  
   `csca5028-final-project-source-a-level-20260313.zip`

## 9. Conclusion
The final system demonstrates a complete, production-oriented architecture aligned to the course rubric: independent web/collector/analyzer processes, shared persistence, API exposure, monitoring instrumentation, automated tests, CI/CD workflows, and event collaboration messaging. This design is intentionally pragmatic for an academic capstone while still representing real distributed system patterns.
