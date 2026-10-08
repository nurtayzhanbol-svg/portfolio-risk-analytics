import math
import statistics

import pandas as pd
import pytest

from app import risk

# One asset, four days: +10%, -10%, +6.06%
PRICES = pd.DataFrame({"AAA": [100.0, 110.0, 99.0, 105.0]})
VALUES = PRICES["AAA"]
RETURNS = [0.1, -0.1, 105 / 99 - 1]


def test_portfolio_values_sums_shares_times_price():
    prices = pd.DataFrame({"A": [10.0, 12.0], "B": [20.0, 18.0]})
    values = risk.portfolio_values(prices, {"A": 2, "B": 1})
    assert list(values) == [40.0, 42.0]


def test_daily_returns():
    assert list(risk.daily_returns(VALUES)) == pytest.approx(RETURNS)


def test_total_return():
    assert risk.total_return(VALUES) == pytest.approx(0.05)


def test_annualized_volatility():
    expected = statistics.stdev(RETURNS) * math.sqrt(252)
    assert risk.annualized_volatility(risk.daily_returns(VALUES)) == pytest.approx(expected)


def test_sharpe_ratio_with_zero_risk_free_rate():
    expected = statistics.mean(RETURNS) / statistics.stdev(RETURNS) * math.sqrt(252)
    assert risk.sharpe_ratio(risk.daily_returns(VALUES)) == pytest.approx(expected)


def test_sharpe_ratio_falls_when_risk_free_rate_rises():
    returns = risk.daily_returns(VALUES)
    assert risk.sharpe_ratio(returns, 0.05) < risk.sharpe_ratio(returns, 0.0)


def test_max_drawdown_is_fall_from_peak():
    # peak 110, then 99: -10%
    assert risk.max_drawdown(VALUES) == pytest.approx(-0.1)


def test_value_at_risk_95():
    # 5th percentile of [-0.1, 0.0606, 0.1] with linear interpolation
    expected = -(-0.1 + 0.1 * (RETURNS[2] + 0.1))
    assert risk.value_at_risk(risk.daily_returns(VALUES)) == pytest.approx(expected)


def test_allocation_weights_sum_to_one():
    weights = risk.allocation(pd.Series({"A": 10.0, "B": 30.0}), {"A": 3, "B": 1})
    assert weights == {"A": 0.5, "B": 0.5}


def test_portfolio_metrics_needs_three_days():
    with pytest.raises(ValueError):
        risk.portfolio_metrics(PRICES.head(2), {"AAA": 1})


def test_portfolio_metrics_ignores_days_with_missing_prices():
    prices = pd.DataFrame({"A": [1.0, 2.0, 3.0, 4.0], "B": [None, 1.0, 1.0, 1.0]})
    assert risk.portfolio_metrics(prices, {"A": 1, "B": 1})["days"] == 3
