from datetime import date

import psycopg
import pytest
from fastapi.testclient import TestClient

from app import config, db

TEST_DB = "portfolio_test"
SAMPLE_PRICES = [
    ("AAA", date(2025, 1, 1), 100.0),
    ("AAA", date(2025, 1, 2), 110.0),
    ("AAA", date(2025, 1, 3), 99.0),
    ("AAA", date(2025, 1, 6), 105.0),
    *[("BBB", date(2025, 1, d), 50.0) for d in (1, 2, 3, 6)],
]


def create_test_database() -> str | None:
    """Create a separate database so tests never touch the app's data."""
    try:
        with psycopg.connect(config.DATABASE_URL, autocommit=True, connect_timeout=2) as conn:
            if not conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (TEST_DB,)).fetchone():
                conn.execute(f"CREATE DATABASE {TEST_DB}")
    except psycopg.OperationalError:
        return None
    return config.DATABASE_URL.rsplit("/", 1)[0] + "/" + TEST_DB


TEST_DATABASE_URL = create_test_database()


@pytest.fixture
def client(monkeypatch):
    if TEST_DATABASE_URL is None:
        pytest.skip("PostgreSQL is not running: docker compose up -d postgres")
    monkeypatch.setattr(config, "DATABASE_URL", TEST_DATABASE_URL)
    with db.connect() as conn:
        db.init_schema(conn)
        conn.execute("TRUNCATE holdings, portfolios, prices RESTART IDENTITY")
        db.upsert_prices(conn, SAMPLE_PRICES)

    from app.api import app

    with TestClient(app) as c:
        yield c
