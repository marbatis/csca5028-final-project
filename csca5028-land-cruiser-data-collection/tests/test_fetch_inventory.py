from scripts import fetch_inventory


def test_fetch_vpic_records_filters_non_land_cruiser(monkeypatch) -> None:
    def fake_get_json(_: str) -> dict:
        return {
            "Results": [
                {"Model_ID": 1, "Make_Name": "TOYOTA", "Model_Name": "Land Cruiser"},
                {"Model_ID": 2, "Make_Name": "TOYOTA", "Model_Name": "Camry"},
            ]
        }

    monkeypatch.setattr(fetch_inventory, "get_json", fake_get_json)
    rows = fetch_inventory.fetch_vpic_records_for_year(1987)
    assert len(rows) == 1
    assert rows[0]["source"] == fetch_inventory.SOURCE_NHTSA_VPIC
    assert rows[0]["model_name"] == "Land Cruiser"
    assert rows[0]["model_year"] == 1987


def test_fetch_fuel_economy_records_parses_xml(monkeypatch) -> None:
    xml = """
    <menuItems>
      <menuItem><text>Corolla</text><value>a</value></menuItem>
      <menuItem><text>Land Cruiser Wagon 4WD</text><value>b</value></menuItem>
    </menuItems>
    """

    monkeypatch.setattr(fetch_inventory, "get_text", lambda _: xml)
    rows = fetch_inventory.fetch_fuel_economy_records_for_year(1988)
    assert len(rows) == 1
    assert rows[0]["source"] == fetch_inventory.SOURCE_FUEL_ECONOMY
    assert rows[0]["external_id"] == "b"
    assert rows[0]["model_year"] == 1988


def test_run_collection_reports_counts(monkeypatch) -> None:
    fake_rows = [
        {
            "source": fetch_inventory.SOURCE_NHTSA_VPIC,
            "external_id": "100",
            "make_name": "TOYOTA",
            "model_name": "Land Cruiser",
            "model_year": 1987,
            "payload_json": "{}",
        }
    ]

    monkeypatch.setattr(fetch_inventory, "fetch_all_source_records_for_year", lambda _: fake_rows)
    monkeypatch.setattr(fetch_inventory, "save_records", lambda rows: len(rows))

    summary = fetch_inventory.run_collection(1987, 1988)
    assert summary["fetched_count"] == 2
    assert summary["inserted_count"] == 2
    assert summary["source_counts"][fetch_inventory.SOURCE_NHTSA_VPIC] == 2
