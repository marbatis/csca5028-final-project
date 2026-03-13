# CSCA 5028 Final Project Report

## Project Title
The '87 Land Cruiser Finder: Collector, Analyzer, and Event-Driven Collaboration

## 1. High-level Description
This project builds a focused data product for 1987 Toyota Land Cruiser buyers and collectors. The system collects listing-related vehicle data from an external API, stores raw records in a shared database, runs analysis to produce summary insights, and exposes a deployed web interface for user interaction.

The project is intentionally split into independent components so each process can scale and evolve separately:

1. Web application (user-facing)
2. Data collector (scheduled API ingestion)
3. Data analyzer (aggregation and reporting)
4. Shared persistence layer (raw + refined data backbone)
5. Event messaging channel (RabbitMQ) for decoupled service collaboration

## 2. Whiteboard Architecture and Process Discussion

```text
User
  |
  v
Web App (Flask, stateless)
  |
  v
SQLite/Post-process views
  ^
  |
Analyzer ----------------------+
  ^                            |
  |                            |
Collector (NHTSA API pull)     |
  |                            |
  +----> RabbitMQ event -----> Consumer/Downstream services
  |
  v
raw_inventory table
```

Process flow:

1. Collector fetches Toyota model data from NHTSA vPIC and filters Land Cruiser records.
2. Collector writes raw records into `raw_inventory`.
3. Analyzer reads raw records and computes rollups such as per-year counts and average records.
4. Collector optionally publishes an `inventory.collection.completed` event to RabbitMQ.
5. Consumer services subscribe to the queue and react asynchronously (logging, notifications, future workflows).
6. Web app serves user requests and can be deployed independently.

## 3. Design Decisions and Justifications

### Decision A: Request/Response for external data fetch
The collector uses direct REST calls (`requests`) to NHTSA because collection requires explicit pull semantics and deterministic input windows by year.

### Decision B: Event Collaboration for cross-service notifications
The system adds RabbitMQ event publication after each collection run. This follows the "announce, do not directly command" model from the final topic:

1. Producer (collector) publishes completion events.
2. Broker (RabbitMQ) buffers and routes messages.
3. Consumers process events independently.

Why this decision:

1. Reduces temporal coupling between collector and downstream actions.
2. Improves extensibility (new consumers can be added without changing collector logic).
3. Improves resilience during load spikes or temporary consumer downtime.

Trade-off acknowledged:

1. Event-driven systems introduce eventual consistency and more complex debugging.
2. Correlation IDs and structured event payloads are required for traceability as the system grows.

### Decision C: SQLite for current scope
SQLite was selected for a lightweight project footprint and fast local setup. Schema migrations are explicitly versioned for repeatability and testability.

### Decision D: Stateless web app with health endpoint
The web app remains stateless and includes a health endpoint to support production monitoring and safe deployment checks.

## 4. System Requirements and Testability

| Requirement | Type | Testability Method | Evidence |
|---|---|---|---|
| System fetches external vehicle data | Functional | Run collector and verify non-empty API fetch counts | Collector logs |
| Raw data is persisted in DB | Functional | Query `raw_inventory` after collector run | DB query output |
| Analysis computes rollups | Functional | Run analyzer and verify summary metrics output | Analyzer logs |
| Web app accepts user input and responds | Functional | Integration test for `/echo` | pytest results |
| Web app exposes service health | Operational | GET `/health` returns 200 + status payload | integration test + curl |
| Collection can collaborate asynchronously | Architectural | Enable event publishing and consume queue messages | consumer output |
| Duplicate raw inserts are controlled | Data integrity | Re-run collector and confirm inserts are ignored by unique key | insert count behavior |

## 5. Deployment and Submission Artifacts

1. Deployed web URL: `https://csca5028-echo-mb-final-0313-6f06d76737c3.herokuapp.com/`
2. Report file: this report (`FINAL_PROJECT_REPORT.md`) and DOCX version
3. Source code ZIP: `csca5028-final-project-source-clean-20260313.zip`

## 6. Conclusion
The final system demonstrates a practical big-data-oriented architecture with clear process separation (collector, analyzer, web app), shared persistence, and event collaboration. The design balances implementation simplicity with scalable patterns by combining direct API retrieval for ingestion and asynchronous messaging for service-to-service collaboration.
