"""Load daily close prices from a CSV file: python -m app.load_prices data/sample_prices.csv"""

import sys

import pandas as pd

from app import db

REQUIRED_COLUMNS = {"date", "symbol", "close"}


def read_prices(path: str) -> list[tuple]:
    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    if df[list(REQUIRED_COLUMNS)].isna().any().any():
        raise ValueError("empty values in date, symbol or close")
    if (df["close"] <= 0).any():
        raise ValueError("close prices must be positive")

    symbols = df["symbol"].str.strip().str.upper()
    dates = pd.to_datetime(df["date"]).dt.date
    return [(s, d, float(c)) for s, d, c in zip(symbols, dates, df["close"])]


def main(path: str) -> None:
    rows = read_prices(path)
    with db.connect() as conn:
        db.init_schema(conn)
        db.upsert_prices(conn, rows)
    print(f"loaded {len(rows)} prices from {path}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
