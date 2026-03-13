#!/usr/bin/env bash
set -euo pipefail

python scripts/apply_migrations.py
python scripts/fetch_inventory.py
