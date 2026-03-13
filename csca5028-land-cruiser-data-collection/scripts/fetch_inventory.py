import json
from datetime import datetime, timezone
from pathlib import Path
import sys

import requests
from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from collector.db import SessionLocal
from collector.eventing import publish_collection_completed

SOURCE_NAME = "NHTSA_vPIC"
API_URL_TEMPLATE = (
    "https://vpic.nhtsa.dot.gov/api/vehicles/"
    "GetModelsForMakeYear/make/toyota/modelyear/{year}?format=json"
)
YEAR_START = 1980
YEAR_END = 1990


def fetch_records_for_year(year: int) -> list[dict]:
    response = requests.get(API_URL_TEMPLATE.format(year=year), timeout=30)
    response.raise_for_status()

    payload = response.json()
    results = payload.get("Results", [])

    # Keep project-relevant records (Land Cruiser variants) for focused data collection.
    filtered = []
    for row in results:
        if "LAND CRUISER" in (row.get("Model_Name", "").upper()):
            row_copy = dict(row)
            row_copy["_model_year"] = year
            filtered.append(row_copy)

    return filtered


def save_records(records: list[dict]) -> int:
    inserted = 0
    now = datetime.now(timezone.utc).isoformat()

    insert_sql = text(
        """
        INSERT OR IGNORE INTO raw_inventory
        (source, external_id, make_name, model_name, model_year, payload_json, fetched_at)
        VALUES
        (:source, :external_id, :make_name, :model_name, :model_year, :payload_json, :fetched_at)
        """
    )

    with SessionLocal.begin() as session:
        for rec in records:
            params = {
                "source": SOURCE_NAME,
                "external_id": str(rec.get("Model_ID", "")),
                "make_name": str(rec.get("Make_Name", "")),
                "model_name": str(rec.get("Model_Name", "")),
                "model_year": int(rec.get("_model_year", 1987)),
                "payload_json": json.dumps(rec, ensure_ascii=True),
                "fetched_at": now,
            }
            result = session.execute(insert_sql, params)
            inserted += result.rowcount

    return inserted


if __name__ == "__main__":
    started_at = datetime.now(timezone.utc).isoformat()
    records = []
    for year in range(YEAR_START, YEAR_END + 1):
        year_records = fetch_records_for_year(year)
        records.extend(year_records)
        print(f"Year {year}: fetched {len(year_records)} Land Cruiser records")

    inserted_count = save_records(records)
    print(f"Fetched records (all years): {len(records)}")
    print(f"Inserted records: {inserted_count}")

    publish_collection_completed(
        {
            "event_type": "inventory.collection.completed",
            "source": SOURCE_NAME,
            "started_at": started_at,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "year_start": YEAR_START,
            "year_end": YEAR_END,
            "fetched_count": len(records),
            "inserted_count": inserted_count,
        }
    )
