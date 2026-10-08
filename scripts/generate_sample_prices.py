"""Generate data/sample_prices.csv: one simulated year of daily closes for 5 symbols.

The prices are random (geometric random walk with a fixed seed), not real market data.
"""

import csv
import math
import random
from pathlib import Path

import pandas as pd

# symbol: (start price, average daily return, daily volatility)
SYMBOLS = {
    "AAPL": (190.0, 0.0006, 0.017),
    "MSFT": (420.0, 0.0005, 0.015),
    "NVDA": (130.0, 0.0012, 0.032),
    "JPM": (200.0, 0.0004, 0.014),
    "XOM": (110.0, 0.0001, 0.016),
}
OUTPUT = Path(__file__).resolve().parent.parent / "data" / "sample_prices.csv"


def main() -> None:
    rng = random.Random(7)
    dates = pd.bdate_range("2025-01-02", periods=252)
    with OUTPUT.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "symbol", "close"])
        for symbol, (price, drift, vol) in SYMBOLS.items():
            for day in dates:
                writer.writerow([day.date().isoformat(), symbol, f"{price:.2f}"])
                price *= math.exp(rng.gauss(drift, vol))
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
