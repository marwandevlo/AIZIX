# AIZIX Bot Dashboard v2.0 (Python-first)

Paper-trading simulation: **FastAPI**, **Jinja2** templates, and **static** CSS/JS (no React, no live exchange execution).

## Setup

### Windows (recommended)

From `apps/api` in **PowerShell**:

```powershell
# If running scripts is blocked:
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

.\setup.ps1
.\.venv\Scripts\Activate.ps1
```

`setup.ps1` creates `.venv` and installs `fastapi`, `uvicorn`, `python-dotenv`, `jinja2`, `pydantic-settings`, `python-multipart`.

If **Python is missing** (only the Microsoft Store stub appears):

```powershell
winget install Python.Python.3.12
# Or install from https://www.python.org/downloads/ (check "Add python.exe to PATH")
```

Optional: `.\setup.ps1 -InstallPython` tries `winget` for you.

### Manual (any OS)

```bash
cd apps/api
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

## Run

```powershell
cd apps/api
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8000
```

Or one step after setup:

```powershell
.\run-dev.ps1
```

Open **http://localhost:8000** (full Jinja dashboard), **http://localhost:8000/dashboard** (quick HTML check), and **http://localhost:8000/api/health** (JSON).

## Layout

| Path | Purpose |
|------|---------|
| `app/main.py` | FastAPI app, `GET /`, `/api/*`, static mount |
| `app/core/config.py` | Settings (`pydantic-settings`) |
| `app/modules/*.py` | Mock market, signals, paper book, risk, backtest, trailing, compounding, mood |
| `templates/index.html` | Aurora-style dashboard (3 tabs) |
| `static/css/style.css` | Dark futuristic UI |
| `static/js/dashboard.js` | API polling, i18n EN/AR, Web Audio chime |
| `static/sounds/` | Optional assets (Web Audio used by default) |

## API (JSON)

| Method | Path |
|--------|------|
| GET | `/api/health` |
| GET | `/api/market` |
| GET | `/api/signals` |
| GET | `/api/positions` |
| GET | `/api/portfolio` |
| GET | `/api/compounding` |
| POST | `/api/bot/start` |
| POST | `/api/bot/pause` |
| POST | `/api/bot/stop` |
| POST | `/api/bot/emergency-stop` |
| POST | `/api/paper-trade/execute` |
| POST | `/api/paper-trade/close-all` |
| POST | `/api/backtest/run` |
| POST | `/api/backtest/apply-best-settings` |
| POST | `/api/dashboard/preferences` |

## Disclaimer

Simulation only. Not investment advice. No broker connectivity.
