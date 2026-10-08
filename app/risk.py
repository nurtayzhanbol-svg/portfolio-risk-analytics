"""Portfolio return and risk calculations with pandas.

`prices` is a DataFrame of daily closes: index = date, one column per symbol.
`quantities` maps symbol -> number of shares held (buy and hold, constant over the period).
"""

import math

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def portfolio_values(prices: pd.DataFrame, quantities: dict[str, float]) -> pd.Series:
    """Daily portfolio value: sum of shares x close price."""
    return (prices[list(quantities)] * pd.Series(quantities)).sum(axis=1)


def daily_returns(values: pd.Series) -> pd.Series:
    return values.pct_change().dropna()


def total_return(values: pd.Series) -> float:
    return values.iloc[-1] / values.iloc[0] - 1


def annualized_volatility(returns: pd.Series) -> float:
    return returns.std() * math.sqrt(TRADING_DAYS)


def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Annualised Sharpe ratio; risk_free_rate is a yearly rate, e.g. 0.03 for 3%."""
    excess = returns - risk_free_rate / TRADING_DAYS
    return excess.mean() / returns.std() * math.sqrt(TRADING_DAYS)


def max_drawdown(values: pd.Series) -> float:
    """Largest fall from a previous peak, as a negative fraction (-0.2 = -20%)."""
    return (values / values.cummax() - 1).min()


def value_at_risk(returns: pd.Series, confidence: float = 0.95) -> float:
    """Historical one-day VaR: the daily loss exceeded on only (1 - confidence) of days."""
    return -np.percentile(returns, (1 - confidence) * 100)


def allocation(latest_prices: pd.Series, quantities: dict[str, float]) -> dict[str, float]:
    """Share of total portfolio value held in each symbol."""
    values = {symbol: qty * latest_prices[symbol] for symbol, qty in quantities.items()}
    total = sum(values.values())
    return {symbol: value / total for symbol, value in values.items()}


def portfolio_metrics(prices: pd.DataFrame, quantities: dict[str, float], risk_free_rate: float = 0.0) -> dict:
    prices = prices[list(quantities)].dropna()
    if len(prices) < 3:
        raise ValueError("need at least 3 days of prices for every holding")

    values = portfolio_values(prices, quantities)
    returns = daily_returns(values)
    return {
        "start_date": str(prices.index[0]),
        "end_date": str(prices.index[-1]),
        "days": len(prices),
        "total_value": round(float(values.iloc[-1]), 2),
        "total_return": round(float(total_return(values)), 6),
        "annualized_volatility": round(float(annualized_volatility(returns)), 6),
        "sharpe_ratio": round(float(sharpe_ratio(returns, risk_free_rate)), 4),
        "max_drawdown": round(float(max_drawdown(values)), 6),
        "value_at_risk_95": round(float(value_at_risk(returns)), 6),
        "allocation": {s: round(float(w), 6) for s, w in allocation(prices.iloc[-1], quantities).items()},
    }
