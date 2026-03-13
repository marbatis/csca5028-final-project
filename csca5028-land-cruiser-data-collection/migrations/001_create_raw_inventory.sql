CREATE TABLE IF NOT EXISTS raw_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    external_id TEXT NOT NULL,
    make_name TEXT NOT NULL,
    model_name TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    UNIQUE(source, external_id, model_year)
);
