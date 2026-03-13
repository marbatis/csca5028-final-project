from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from collector.db import engine


if __name__ == "__main__":
    migrations_dir = Path(__file__).resolve().parent.parent / "migrations"
    migration_files = sorted(migrations_dir.glob("*.sql"))

    with engine.begin() as conn:
        for migration_file in migration_files:
            sql = migration_file.read_text(encoding="utf-8")
            conn.exec_driver_sql(sql)
            print(f"Applied migration: {migration_file.name}")
