from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON_BIN = sys.executable


def run_command(script_path: Path) -> None:
    subprocess.run([PYTHON_BIN, str(script_path)], cwd=PROJECT_ROOT, check=True)


def main() -> None:
    interval_minutes = int(
        __import__("os").getenv("COLLECT_INTERVAL_MINUTES", "60").strip() or "60"
    )
    max_runs_raw = __import__("os").getenv("COLLECT_MAX_RUNS", "").strip()
    max_runs = int(max_runs_raw) if max_runs_raw else None

    run_count = 0
    while True:
        run_count += 1
        print(f"[collector-loop] Run {run_count} started")
        run_command(PROJECT_ROOT / "scripts" / "apply_migrations.py")
        run_command(PROJECT_ROOT / "scripts" / "fetch_inventory.py")
        print(f"[collector-loop] Run {run_count} completed")

        if max_runs is not None and run_count >= max_runs:
            print("[collector-loop] Max runs reached. Exiting.")
            return

        sleep_seconds = interval_minutes * 60
        print(f"[collector-loop] Sleeping {sleep_seconds} seconds")
        time.sleep(sleep_seconds)


if __name__ == "__main__":
    main()
