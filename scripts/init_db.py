"""Initialize the SQLite database and seed baseline data."""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.extensions import db
from app.risk import services

app = create_app()


def main() -> None:
    reset = "--reset" in sys.argv

    with app.app_context():
        if reset:
            db.drop_all()
        db.create_all()
        services.bootstrap_seed_data()
        print("Database initialized and seeded.")


if __name__ == "__main__":
    main()
