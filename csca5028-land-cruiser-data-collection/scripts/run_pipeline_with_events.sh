#!/usr/bin/env bash
set -euo pipefail

export EVENT_COLLAB_ENABLED=1
python scripts/apply_migrations.py
python scripts/fetch_inventory.py
python scripts/analyze_data.py
