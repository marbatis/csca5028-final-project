from pathlib import Path
import sys

from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from collector.db import SessionLocal


def main() -> None:
    with SessionLocal() as session:
        total_rows = session.execute(
            text("SELECT COUNT(*) FROM raw_inventory")
        ).scalar_one()

        distinct_years = session.execute(
            text("SELECT COUNT(DISTINCT model_year) FROM raw_inventory")
        ).scalar_one()

        per_year_rows = session.execute(
            text(
                """
                SELECT model_year, COUNT(*) AS row_count
                FROM raw_inventory
                GROUP BY model_year
                ORDER BY model_year
                """
            )
        ).all()

        top_models = session.execute(
            text(
                """
                SELECT model_name, COUNT(*) AS row_count
                FROM raw_inventory
                GROUP BY model_name
                ORDER BY row_count DESC, model_name ASC
                LIMIT 3
                """
            )
        ).all()

        year_bounds = session.execute(
            text("SELECT MIN(model_year), MAX(model_year) FROM raw_inventory")
        ).one()

        per_source_rows = session.execute(
            text(
                """
                SELECT source, COUNT(*) AS row_count
                FROM raw_inventory
                GROUP BY source
                ORDER BY source
                """
            )
        ).all()

    avg_per_year = (total_rows / distinct_years) if distinct_years else 0.0

    print("Analysis summary")
    print(f"- Total records in raw_inventory: {total_rows}")
    print(f"- Distinct years covered: {distinct_years}")
    print(f"- Year range with data: {year_bounds[0]} to {year_bounds[1]}")
    print(f"- Average Land Cruiser records per year: {avg_per_year:.2f}")
    print("- Records by year:")
    for row in per_year_rows:
        print(f"  - {row.model_year}: {row.row_count}")

    print("- Top model names:")
    for row in top_models:
        print(f"  - {row.model_name}: {row.row_count}")

    print("- Records by source:")
    for row in per_source_rows:
        print(f"  - {row.source}: {row.row_count}")


if __name__ == "__main__":
    main()
