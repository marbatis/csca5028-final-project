import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "land_cruiser.sqlite3"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

database_url = os.getenv("DATABASE_URL", "").strip()
if database_url:
    # Heroku may provide postgres://; SQLAlchemy expects postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    DATABASE_URL = database_url
else:
    DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
