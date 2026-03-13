from pathlib import Path
import sys

from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from collector.db import SessionLocal


if __name__ == "__main__":
    with SessionLocal() as session:
        rows = session.execute(
            text(
                """
                SELECT id, source, external_id, make_name, model_name, model_year, fetched_at
                FROM raw_inventory
                ORDER BY id DESC
                LIMIT 10
                """
            )
        ).all()

    for row in rows:
        print(row)
