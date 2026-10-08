from datetime import date

import pytest

from app.load_prices import read_prices


def write(tmp_path, text):
    path = tmp_path / "prices.csv"
    path.write_text(text)
    return path


def test_read_prices_normalises_symbol_and_date(tmp_path):
    path = write(tmp_path, "date,symbol,close\n2025-01-02, aapl ,190.5\n")
    assert read_prices(path) == [("AAPL", date(2025, 1, 2), 190.5)]


def test_read_prices_rejects_missing_column(tmp_path):
    with pytest.raises(ValueError, match="missing columns"):
        read_prices(write(tmp_path, "date,close\n2025-01-02,190.5\n"))


def test_read_prices_rejects_non_positive_price(tmp_path):
    with pytest.raises(ValueError, match="positive"):
        read_prices(write(tmp_path, "date,symbol,close\n2025-01-02,AAPL,0\n"))
