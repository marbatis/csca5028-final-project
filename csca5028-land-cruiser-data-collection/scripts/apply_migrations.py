from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from collector.db import engine
from collector.models import Base


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Schema ensured via SQLAlchemy metadata")
