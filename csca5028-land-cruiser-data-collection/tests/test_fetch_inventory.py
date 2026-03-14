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


def test_fetch_bat_listing_records_for_year_filters_model_and_year(monkeypatch) -> None:
    html = """
    {"title":"1987 Toyota Land Cruiser FJ60","url":"https:\\/\\/bringatrailer.com\\/listing\\/1987-toyota-land-cruiser-fj60-195\\/","year":"1987","id":108767828}
    {"title":"1987 Porsche 911 Carrera","url":"https:\\/\\/bringatrailer.com\\/listing\\/1987-porsche-911\\/","year":"1987","id":108700000}
    {"title":"1990 Toyota Land Cruiser","url":"https:\\/\\/bringatrailer.com\\/listing\\/1990-toyota-land-cruiser\\/","year":"1990","id":108799999}
    """

    monkeypatch.setattr(fetch_inventory, "get_text", lambda _: html)
    rows = fetch_inventory.fetch_bat_listing_records_for_year(1987)

    assert len(rows) == 1
    assert rows[0]["source"] == fetch_inventory.SOURCE_BAT_LISTINGS
    assert rows[0]["external_id"] == "BAT-108767828"
    assert rows[0]["model_year"] == 1987
    assert "bringatrailer.com/listing/1987-toyota-land-cruiser-fj60-195/" in rows[0]["payload_json"]


def test_fetch_classiccars_listing_records_for_year_parses_jsonld(monkeypatch) -> None:
    html = """
    <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"car","name":"1987 Toyota Land Cruiser","modelDate":"1987","manufacturer":"Toyota","model":"Land Cruiser","sku":"CC-2048805","offers":{"url":"/listings/view/2048805/1987-toyota-land-cruiser-for-sale-in-palm-coast-florida-32137","price":"38000","priceCurrency":"USD"}}
    </script>
    <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"car","name":"1987 Porsche 911","modelDate":"1987","manufacturer":"Porsche","model":"911","sku":"CC-1111111","offers":{"url":"/listings/view/1111111/1987-porsche-911","price":"100000","priceCurrency":"USD"}}
    </script>
    """

    monkeypatch.setattr(fetch_inventory, "get_text", lambda _: html)
    rows = fetch_inventory.fetch_classiccars_listing_records_for_year(1987)

    assert len(rows) == 1
    assert rows[0]["source"] == fetch_inventory.SOURCE_CLASSICCARS_LISTINGS
    assert rows[0]["external_id"] == "CC-2048805"
    assert rows[0]["model_year"] == 1987
    assert "https://www.classiccars.com/listings/view/2048805/" in rows[0]["payload_json"]


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
