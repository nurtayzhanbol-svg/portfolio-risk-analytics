import pytest


def create_portfolio(client, name="Test"):
    response = client.post("/portfolios", json={"name": name})
    assert response.status_code == 201
    return response.json()["id"]


def test_create_and_read_portfolio(client):
    pid = create_portfolio(client)
    client.put(f"/portfolios/{pid}/holdings/aaa", json={"quantity": 10})
    client.put(f"/portfolios/{pid}/holdings/BBB", json={"quantity": 20})

    body = client.get(f"/portfolios/{pid}").json()
    assert [h["symbol"] for h in body["holdings"]] == ["AAA", "BBB"]
    assert body["total_value"] == 10 * 105 + 20 * 50


def test_update_quantity_replaces_old_value(client):
    pid = create_portfolio(client)
    client.put(f"/portfolios/{pid}/holdings/AAA", json={"quantity": 10})
    client.put(f"/portfolios/{pid}/holdings/AAA", json={"quantity": 3})
    assert client.get(f"/portfolios/{pid}").json()["holdings"][0]["quantity"] == 3


def test_metrics(client):
    pid = create_portfolio(client)
    client.put(f"/portfolios/{pid}/holdings/AAA", json={"quantity": 10})
    client.put(f"/portfolios/{pid}/holdings/BBB", json={"quantity": 20})

    m = client.get(f"/portfolios/{pid}/metrics").json()
    assert m["days"] == 4
    assert m["total_value"] == 2050.0
    assert m["total_return"] == pytest.approx(2050 / 2000 - 1)
    assert m["allocation"]["AAA"] == pytest.approx(1050 / 2050, abs=1e-6)
    assert m["max_drawdown"] < 0


def test_unknown_portfolio_returns_404(client):
    assert client.get("/portfolios/999").status_code == 404
    assert client.get("/portfolios/999/metrics").status_code == 404


def test_unknown_symbol_returns_404(client):
    pid = create_portfolio(client)
    assert client.put(f"/portfolios/{pid}/holdings/XYZ", json={"quantity": 1}).status_code == 404


def test_quantity_must_be_positive(client):
    pid = create_portfolio(client)
    assert client.put(f"/portfolios/{pid}/holdings/AAA", json={"quantity": 0}).status_code == 422


def test_metrics_for_empty_portfolio_returns_400(client):
    pid = create_portfolio(client)
    assert client.get(f"/portfolios/{pid}/metrics").status_code == 400


def test_delete_holding(client):
    pid = create_portfolio(client)
    client.put(f"/portfolios/{pid}/holdings/AAA", json={"quantity": 1})
    assert client.delete(f"/portfolios/{pid}/holdings/AAA").status_code == 204
    assert client.delete(f"/portfolios/{pid}/holdings/AAA").status_code == 404
