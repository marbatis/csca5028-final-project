#!/usr/bin/env bash
set -euo pipefail

MODE="${MODE:-once}"

if [[ "$MODE" == "loop" ]]; then
  python scripts/run_collector_loop.py
else
  python scripts/apply_migrations.py
  python scripts/fetch_inventory.py
fi
