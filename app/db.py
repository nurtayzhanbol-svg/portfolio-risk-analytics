import psycopg
from psycopg.rows import dict_row

from app import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS prices (
    symbol TEXT NOT NULL,
    date   DATE NOT NULL,
    close  DOUBLE PRECISION NOT NULL CHECK (close > 0),
    PRIMARY KEY (symbol, date)
);
CREATE TABLE IF NOT EXISTS portfolios (
    id         SERIAL PRIMARY KEY,
    name       TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS holdings (
    portfolio_id INTEGER NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    symbol       TEXT NOT NULL,
    quantity     DOUBLE PRECISION NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (portfolio_id, symbol)
);
"""


def connect() -> psycopg.Connection:
    return psycopg.connect(config.DATABASE_URL, row_factory=dict_row, autocommit=True)


def init_schema(conn) -> None:
    conn.execute(SCHEMA)


# Prices

def upsert_prices(conn, rows: list[tuple]) -> None:
    """rows: (symbol, date, close). Loading the same file twice updates instead of duplicating."""
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO prices (symbol, date, close) VALUES (%s, %s, %s)
            ON CONFLICT (symbol, date) DO UPDATE SET close = EXCLUDED.close
            """,
            rows,
        )


def symbol_exists(conn, symbol: str) -> bool:
    return conn.execute("SELECT 1 FROM prices WHERE symbol = %s LIMIT 1", (symbol,)).fetchone() is not None


def latest_prices(conn) -> list[dict]:
    return conn.execute(
        "SELECT DISTINCT ON (symbol) symbol, date, close FROM prices ORDER BY symbol, date DESC"
    ).fetchall()


def price_history(conn, symbols: list[str]) -> list[dict]:
    return conn.execute(
        "SELECT symbol, date, close FROM prices WHERE symbol = ANY(%s) ORDER BY date",
        (symbols,),
    ).fetchall()


# Portfolios and holdings

def create_portfolio(conn, name: str) -> dict:
    return conn.execute(
        "INSERT INTO portfolios (name) VALUES (%s) RETURNING id, name", (name,)
    ).fetchone()


def get_portfolio(conn, portfolio_id: int) -> dict | None:
    return conn.execute(
        "SELECT id, name FROM portfolios WHERE id = %s", (portfolio_id,)
    ).fetchone()


def holdings(conn, portfolio_id: int) -> list[dict]:
    return conn.execute(
        "SELECT symbol, quantity FROM holdings WHERE portfolio_id = %s ORDER BY symbol",
        (portfolio_id,),
    ).fetchall()


def upsert_holding(conn, portfolio_id: int, symbol: str, quantity: float) -> None:
    conn.execute(
        """
        INSERT INTO holdings (portfolio_id, symbol, quantity) VALUES (%s, %s, %s)
        ON CONFLICT (portfolio_id, symbol) DO UPDATE SET quantity = EXCLUDED.quantity
        """,
        (portfolio_id, symbol, quantity),
    )


def delete_holding(conn, portfolio_id: int, symbol: str) -> bool:
    cur = conn.execute(
        "DELETE FROM holdings WHERE portfolio_id = %s AND symbol = %s", (portfolio_id, symbol)
    )
    return cur.rowcount == 1
