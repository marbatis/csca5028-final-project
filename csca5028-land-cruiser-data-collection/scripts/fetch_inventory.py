from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from collector.db import SessionLocal
from collector.eventing import publish_collection_completed

SOURCE_NHTSA_VPIC = "NHTSA_vPIC_MODELS"
SOURCE_NHTSA_RECALLS = "NHTSA_RECALLS"
SOURCE_FUEL_ECONOMY = "FUEL_ECONOMY_MENU"
SOURCE_BAT_LISTINGS = "BAT_LISTINGS"
SOURCE_CLASSICCARS_LISTINGS = "CLASSICCARS_LISTINGS"

VPIC_URL_TEMPLATE = (
    "https://vpic.nhtsa.dot.gov/api/vehicles/"
    "GetModelsForMakeYear/make/toyota/modelyear/{year}?format=json"
)
RECALLS_URL_TEMPLATE = (
    "https://api.nhtsa.gov/recalls/recallsByVehicle?"
    "make=TOYOTA&model=LAND%20CRUISER&modelYear={year}"
)
FUEL_MODEL_MENU_TEMPLATE = (
    "https://www.fueleconomy.gov/ws/rest/vehicle/menu/model?year={year}&make=Toyota"
)
BAT_AUCTIONS_SEARCH_TEMPLATE = "https://bringatrailer.com/auctions/?search={year}+toyota+land+cruiser"
CLASSICCARS_SEARCH_TEMPLATE = "https://www.classiccars.com/listings/find/{year}/toyota/land-cruiser"
CLASSICCARS_BASE_URL = "https://www.classiccars.com"

BAT_LISTING_PATTERN = re.compile(
    r'"title":"(?P<title>[^"]+)","url":"(?P<url>https:[\\\/]+bringatrailer\.com[\\\/]+listing[\\\/]+[^"]+)"'
    r'.*?"year":"(?P<year>[0-9]{4})","id":(?P<id>[0-9]+)',
    re.S,
)
CLASSICCARS_JSONLD_PATTERN = re.compile(
    r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>',
    re.S,
)

DEFAULT_YEAR_START = 1980
DEFAULT_YEAR_END = 1990
REQUEST_TIMEOUT_SECONDS = 30
REQUEST_HEADERS = {"User-Agent": "csca5028-land-cruiser-finder/1.0"}


def configured_year_range() -> tuple[int, int]:
    year_start = int(os.getenv("YEAR_START", str(DEFAULT_YEAR_START)))
    year_end = int(os.getenv("YEAR_END", str(DEFAULT_YEAR_END)))
    if year_end < year_start:
        raise ValueError("YEAR_END must be >= YEAR_START")
    return year_start, year_end


def get_json(url: str) -> dict[str, Any]:
    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS, headers=REQUEST_HEADERS)
    response.raise_for_status()
    return response.json()


def get_text(url: str) -> str:
    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS, headers=REQUEST_HEADERS)
    response.raise_for_status()
    return response.text


def decode_json_escaped(value: str) -> str:
    try:
        return json.loads(f'"{value}"')
    except Exception:
        return value


def fetch_bat_listing_records_for_year(year: int) -> list[dict[str, Any]]:
    html = get_text(BAT_AUCTIONS_SEARCH_TEMPLATE.format(year=year))
    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for match in BAT_LISTING_PATTERN.finditer(html):
        listing_year = int(match.group("year"))
        if listing_year != year:
            continue

        title = decode_json_escaped(match.group("title")).strip()
        if "LAND CRUISER" not in title.upper():
            continue

        listing_id = match.group("id").strip()
        if not listing_id or listing_id in seen_ids:
            continue
        seen_ids.add(listing_id)

        listing_url = match.group("url").replace("\\/", "/").strip()
        payload = {
            "marketplace": "Bring a Trailer",
            "title": title,
            "url": listing_url,
            "year": listing_year,
            "listing_id": listing_id,
        }
        records.append(
            {
                "source": SOURCE_BAT_LISTINGS,
                "external_id": f"BAT-{listing_id}",
                "make_name": "TOYOTA",
                "model_name": title,
                "model_year": listing_year,
                "payload_json": json.dumps(payload, ensure_ascii=True),
            }
        )
    return records


def fetch_classiccars_listing_records_for_year(year: int) -> list[dict[str, Any]]:
    html = get_text(CLASSICCARS_SEARCH_TEMPLATE.format(year=year))
    blocks = CLASSICCARS_JSONLD_PATTERN.findall(html)
    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for block in blocks:
        try:
            payload = json.loads(block)
        except json.JSONDecodeError:
            continue

        model_year_raw = str(payload.get("modelDate", "")).strip()
        if model_year_raw != str(year):
            continue

        manufacturer = str(payload.get("manufacturer", "")).strip().upper()
        model = str(payload.get("model", "")).strip().upper()
        name = str(payload.get("name", "")).strip()
        if "TOYOTA" not in manufacturer or "LAND CRUISER" not in f"{model} {name}".upper():
            continue

        listing_id = str(payload.get("sku", "")).strip()
        if not listing_id or listing_id in seen_ids:
            continue
        seen_ids.add(listing_id)

        offers = payload.get("offers", {})
        listing_url = ""
        if isinstance(offers, dict):
            listing_url = str(offers.get("url", "")).strip()
        if listing_url.startswith("/"):
            listing_url = f"{CLASSICCARS_BASE_URL}{listing_url}"
        if not listing_url:
            continue

        normalized_payload = {
            "marketplace": "ClassicCars.com",
            "title": name,
            "url": listing_url,
            "year": year,
            "listing_id": listing_id,
            "price": offers.get("price") if isinstance(offers, dict) else None,
            "price_currency": offers.get("priceCurrency") if isinstance(offers, dict) else None,
        }
        records.append(
            {
                "source": SOURCE_CLASSICCARS_LISTINGS,
                "external_id": listing_id,
                "make_name": "TOYOTA",
                "model_name": name or "Toyota Land Cruiser",
                "model_year": year,
                "payload_json": json.dumps(normalized_payload, ensure_ascii=True),
            }
        )
    return records


def fetch_vpic_records_for_year(year: int) -> list[dict[str, Any]]:
    payload = get_json(VPIC_URL_TEMPLATE.format(year=year))
    results = payload.get("Results", [])
    records: list[dict[str, Any]] = []
    for row in results:
        model_name = str(row.get("Model_Name", "")).strip()
        if "LAND CRUISER" not in model_name.upper():
            continue
        external_id = str(row.get("Model_ID", "")).strip()
        if not external_id:
            continue
        records.append(
            {
                "source": SOURCE_NHTSA_VPIC,
                "external_id": external_id,
                "make_name": str(row.get("Make_Name", "TOYOTA")).strip() or "TOYOTA",
                "model_name": model_name,
                "model_year": year,
                "payload_json": json.dumps(row, ensure_ascii=True),
            }
        )
    return records


def fetch_recall_records_for_year(year: int) -> list[dict[str, Any]]:
    payload = get_json(RECALLS_URL_TEMPLATE.format(year=year))
    results = payload.get("results", [])
    records: list[dict[str, Any]] = []
    for row in results:
        campaign_number = str(row.get("NHTSACampaignNumber", "")).strip()
        if not campaign_number:
            continue
        model_name = str(row.get("Model", "LAND CRUISER")).strip() or "LAND CRUISER"
        records.append(
            {
                "source": SOURCE_NHTSA_RECALLS,
                "external_id": campaign_number,
                "make_name": str(row.get("Make", "TOYOTA")).strip() or "TOYOTA",
                "model_name": model_name,
                "model_year": year,
                "payload_json": json.dumps(row, ensure_ascii=True),
            }
        )
    return records


def fetch_fuel_economy_records_for_year(year: int) -> list[dict[str, Any]]:
    xml_text = get_text(FUEL_MODEL_MENU_TEMPLATE.format(year=year))
    root = ET.fromstring(xml_text)
    records: list[dict[str, Any]] = []
    for menu_item in root.findall(".//menuItem"):
        model_name = (menu_item.findtext("text") or "").strip()
        if "CRUISER" not in model_name.upper():
            continue
        external_id = (menu_item.findtext("value") or model_name).strip()
        if not external_id:
            continue
        payload = {"text": model_name, "value": external_id, "model_year": year}
        records.append(
            {
                "source": SOURCE_FUEL_ECONOMY,
                "external_id": external_id,
                "make_name": "TOYOTA",
                "model_name": model_name,
                "model_year": year,
                "payload_json": json.dumps(payload, ensure_ascii=True),
            }
        )
    return records


def fetch_all_source_records_for_year(year: int) -> list[dict[str, Any]]:
    per_source_fetchers = (
        (SOURCE_CLASSICCARS_LISTINGS, fetch_classiccars_listing_records_for_year),
        (SOURCE_BAT_LISTINGS, fetch_bat_listing_records_for_year),
        (SOURCE_NHTSA_VPIC, fetch_vpic_records_for_year),
        (SOURCE_NHTSA_RECALLS, fetch_recall_records_for_year),
        (SOURCE_FUEL_ECONOMY, fetch_fuel_economy_records_for_year),
    )

    records: list[dict[str, Any]] = []
    for source_name, fetcher in per_source_fetchers:
        try:
            fetched = fetcher(year)
            records.extend(fetched)
            print(f"Year {year}: fetched {len(fetched)} records from {source_name}")
        except Exception as exc:
            # Keep pipeline resilient if a single source is unavailable.
            print(f"Year {year}: source {source_name} failed ({exc})")
    return records


def save_records(records: list[dict[str, Any]]) -> int:
    inserted = 0
    now = datetime.now(timezone.utc).isoformat()

    exists_sql = text(
        """
        SELECT 1
        FROM raw_inventory
        WHERE source = :source
          AND external_id = :external_id
          AND model_year = :model_year
        LIMIT 1
        """
    )

    insert_sql = text(
        """
        INSERT INTO raw_inventory
        (source, external_id, make_name, model_name, model_year, payload_json, fetched_at)
        VALUES
        (:source, :external_id, :make_name, :model_name, :model_year, :payload_json, :fetched_at)
        """
    )

    with SessionLocal.begin() as session:
        for rec in records:
            params = {
                "source": rec["source"],
                "external_id": rec["external_id"],
                "make_name": rec["make_name"],
                "model_name": rec["model_name"],
                "model_year": int(rec["model_year"]),
                "payload_json": rec["payload_json"],
                "fetched_at": now,
            }

            exists = session.execute(
                exists_sql,
                {
                    "source": params["source"],
                    "external_id": params["external_id"],
                    "model_year": params["model_year"],
                },
            ).first()
            if exists:
                continue

            session.execute(insert_sql, params)
            inserted += 1
    return inserted


def run_collection(year_start: int, year_end: int) -> dict[str, Any]:
    all_records: list[dict[str, Any]] = []
    for year in range(year_start, year_end + 1):
        all_records.extend(fetch_all_source_records_for_year(year))

    inserted_count = save_records(all_records)
    source_counts = Counter(rec["source"] for rec in all_records)

    print(f"Fetched records (all sources, all years): {len(all_records)}")
    print(f"Inserted records: {inserted_count}")
    print("Records by source:")
    for source_name, count in sorted(source_counts.items()):
        print(f"- {source_name}: {count}")

    return {
        "year_start": year_start,
        "year_end": year_end,
        "fetched_count": len(all_records),
        "inserted_count": inserted_count,
        "source_counts": dict(source_counts),
    }


def main() -> None:
    started_at = datetime.now(timezone.utc).isoformat()
    year_start, year_end = configured_year_range()
    run_summary = run_collection(year_start, year_end)
    publish_collection_completed(
        {
            "event_type": "inventory.collection.completed",
            "started_at": started_at,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            **run_summary,
        }
    )


if __name__ == "__main__":
    main()
