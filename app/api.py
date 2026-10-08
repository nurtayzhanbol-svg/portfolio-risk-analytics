from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app import db, risk


@asynccontextmanager
async def lifespan(app: FastAPI):
    with db.connect() as conn:
        db.init_schema(conn)
    yield


app = FastAPI(title="Portfolio Risk Analytics Engine", lifespan=lifespan)


class PortfolioIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class HoldingIn(BaseModel):
    quantity: float = Field(gt=0)


def portfolio_or_404(conn, portfolio_id: int) -> dict:
    portfolio = db.get_portfolio(conn, portfolio_id)
    if portfolio is None:
        raise HTTPException(404, f"portfolio {portfolio_id} not found")
    return portfolio


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/symbols")
def symbols() -> list[dict]:
    """Every symbol with its latest close price."""
    with db.connect() as conn:
        return db.latest_prices(conn)


@app.post("/portfolios", status_code=201)
def create_portfolio(body: PortfolioIn) -> dict:
    with db.connect() as conn:
        return db.create_portfolio(conn, body.name)


@app.get("/portfolios/{portfolio_id}")
def get_portfolio(portfolio_id: int) -> dict:
    with db.connect() as conn:
        portfolio = portfolio_or_404(conn, portfolio_id)
        holdings = db.holdings(conn, portfolio_id)
        latest = {r["symbol"]: r["close"] for r in db.latest_prices(conn)}

    items = [
        {**h, "price": latest[h["symbol"]], "value": round(h["quantity"] * latest[h["symbol"]], 2)}
        for h in holdings
    ]
    return {**portfolio, "holdings": items, "total_value": round(sum(i["value"] for i in items), 2)}


@app.put("/portfolios/{portfolio_id}/holdings/{symbol}")
def set_holding(portfolio_id: int, symbol: str, body: HoldingIn) -> dict:
    """Add a holding or change its quantity."""
    symbol = symbol.upper()
    with db.connect() as conn:
        portfolio_or_404(conn, portfolio_id)
        if not db.symbol_exists(conn, symbol):
            raise HTTPException(404, f"no prices for {symbol}")
        db.upsert_holding(conn, portfolio_id, symbol, body.quantity)
    return {"symbol": symbol, "quantity": body.quantity}


@app.delete("/portfolios/{portfolio_id}/holdings/{symbol}", status_code=204)
def remove_holding(portfolio_id: int, symbol: str) -> None:
    with db.connect() as conn:
        portfolio_or_404(conn, portfolio_id)
        if not db.delete_holding(conn, portfolio_id, symbol.upper()):
            raise HTTPException(404, f"{symbol.upper()} is not in portfolio {portfolio_id}")


@app.get("/portfolios/{portfolio_id}/metrics")
def metrics(portfolio_id: int, risk_free_rate: float = Query(0.0, ge=0, le=1)) -> dict:
    with db.connect() as conn:
        portfolio_or_404(conn, portfolio_id)
        holdings = db.holdings(conn, portfolio_id)
        if not holdings:
            raise HTTPException(400, "portfolio has no holdings")
        quantities = {h["symbol"]: h["quantity"] for h in holdings}
        rows = db.price_history(conn, list(quantities))

    prices = pd.DataFrame(rows).pivot(index="date", columns="symbol", values="close")
    try:
        result = risk.portfolio_metrics(prices, quantities, risk_free_rate)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"portfolio_id": portfolio_id, **result}
