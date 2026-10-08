# How to explain this project

## 30-second pitch

"I built a small portfolio analytics backend. Prices are loaded from a CSV into PostgreSQL, users create portfolios and holdings through a FastAPI REST API, and a metrics endpoint uses pandas to compute total return, annualised volatility, Sharpe ratio, maximum drawdown, historical Value at Risk and allocation. Every formula is unit-tested against a small example I calculated by hand, and the API is tested against a real Postgres."

## Walk through `GET /portfolios/1/metrics`

1. Check the portfolio exists (404 if not) and has holdings (400 if empty).
2. Load the price history of those symbols from Postgres.
3. Pivot it into a table: one row per date, one column per symbol.
4. Drop dates where any holding has no price, then value = Σ shares × close for each day.
5. `pct_change()` gives daily returns; each metric is a one-line function of the values or returns.

## The metrics in plain words

- **Volatility:** how much daily returns jump around. × √252 converts daily to yearly because variance grows with time, so standard deviation grows with √time.
- **Sharpe ratio:** return earned per unit of risk, after subtracting what a risk-free asset would pay. Higher is better; above 1 is usually considered good.
- **Max drawdown:** the worst peak-to-bottom fall. It answers "how much could I have lost if I bought at the worst moment?"
- **VaR 95%:** "on 95% of days the loss was smaller than X". Historical method: just take the 5th percentile of past daily returns, no distribution assumption.
- **Allocation:** what share of the money is in each stock: a concentration check.

## Likely questions

**Why compute metrics on request instead of storing them?**
They depend on the current holdings, which can change at any time, and one year of data for a few symbols is computed in milliseconds. If it became slow I would cache by (portfolio, holdings version, last price date).

**Why is the API tested against a real database and not mocks?**
Most bugs in a CRUD API live in SQL: constraints, upserts, joins. A real Postgres catches them. The tests use a separate database so they never delete real data.

**How do you stop bad data getting in?**
The CSV loader checks columns, empty values and positive prices; the database also has `CHECK (close > 0)`, `CHECK (quantity > 0)` and primary keys that make re-loading the same file an update, not a duplicate.

**What is wrong with historical VaR?**
It assumes the future looks like the past window, and it says nothing about how bad losses are beyond the 5% threshold (that is what Expected Shortfall measures).

**Why buy and hold?**
To keep the model simple: quantities are constant. Supporting trades would need a transactions table and time-weighted returns.

**What would you add next?**
Transactions and time-weighted return, Expected Shortfall, a benchmark comparison (beta against an index), and real prices from a market-data API.

## Exercises for yourself

- Add Expected Shortfall (average of returns below the 5th percentile): function, test, API field.
- Add `GET /portfolios` that lists all portfolios.
- Change `sample_prices.csv` so one symbol has a missing day, and explain what `dropna()` does to the metrics.
