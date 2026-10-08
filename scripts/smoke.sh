#!/usr/bin/env bash
# End-to-end check against a running stack (docker compose up -d --build).
set -euo pipefail
API=${API:-http://localhost:8000}

for i in $(seq 1 30); do
  curl -sf "$API/health" >/dev/null && break
  sleep 1
done

curl -sf "$API/symbols" | grep -q AAPL
PID=$(curl -sf -X POST "$API/portfolios" -H 'Content-Type: application/json' -d '{"name": "smoke"}' \
  | python3 -c 'import json, sys; print(json.load(sys.stdin)["id"])')
curl -sf -X PUT "$API/portfolios/$PID/holdings/AAPL" -H 'Content-Type: application/json' -d '{"quantity": 10}' >/dev/null
curl -sf -X PUT "$API/portfolios/$PID/holdings/NVDA" -H 'Content-Type: application/json' -d '{"quantity": 5}' >/dev/null
curl -sf "$API/portfolios/$PID" | grep -q '"total_value"'
curl -sf "$API/portfolios/$PID/metrics" | grep -q '"value_at_risk_95"'
[ "$(curl -s -o /dev/null -w '%{http_code}' "$API/portfolios/$PID/holdings/XYZ" -X PUT -H 'Content-Type: application/json' -d '{"quantity": 1}')" = 404 ]
echo "smoke test passed (portfolio $PID)"
