# AIZIX API (FastAPI)

Paper-trading AI engine: mock market, ETF-style 3L/3S sleeves, risk gating, compounding split, and in-memory execution. **No live exchange or Gate.io calls.**

## Setup

```bash
cd apps/api
python -m venv .venv
# Windows:
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Use `API_PORT` from `.env` if you configure a process manager to read it.

## Key modules

| File | Purpose |
|------|---------|
| `app/market_engine.py` | Mock prices, volume, volatility, trend, whale pulse, sentiment |
| `app/signal_engine.py` | BUY/SELL/HOLD + confidence, mood, reason, risk overlay |
| `app/etf_strategy.py` | BTC3L/BTC3S/ETH3L/ETH3S style recommendations |
| `app/risk_manager.py` | Daily loss cap, per-trade risk, max positions, min confidence, emergency stop |
| `app/compounding.py` | 70% trading / 30% safety wallet split |
| `app/paper_trader.py` | Simulated positions, closes, PnL, win rate |
| `app/repository.py` | Optional Supabase persistence for bot state + signal log |

## HTTP endpoints (quick test)

With the server running, open **Swagger**: `http://127.0.0.1:8000/docs`

| Method | Path | Notes |
|--------|------|--------|
| GET | `/health` | Liveness + storage backend |
| GET | `/market` | Latest `MarketSnapshot` JSON |
| GET | `/signals` | AI signal (+ short history); sets `last_signal` for paper execute |
| GET | `/bot/status` | Bot mode + balances + win rate |
| POST | `/bot/start` | Clears risk emergency flag |
| POST | `/bot/pause` | Pauses bot |
| POST | `/bot/stop` | Stops bot + emergency stop |
| GET | `/bot/compounding` | Split + toggle state |
| POST | `/bot/compounding` | Body `{"enabled": true}` |
| GET | `/compounding` | Same split as above (root alias) |
| GET | `/portfolio` | Paper stats + open legs + balances |
| POST | `/paper-trade/execute` | Body optional; defaults from last `/signals` (bot must be ACTIVE) |
| POST | `/paper-trade/close-all` | Closes all paper legs at synthetic exit |

### curl examples

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/market
curl -s http://127.0.0.1:8000/signals
curl -s http://127.0.0.1:8000/portfolio
curl -s -X POST http://127.0.0.1:8000/bot/start
curl -s -X POST http://127.0.0.1:8000/paper-trade/execute -H "Content-Type: application/json" -d "{}"
curl -s -X POST http://127.0.0.1:8000/paper-trade/close-all
```

## Disclaimer

Simulation only. Not investment advice. Past (or mocked) performance does not imply future results.
