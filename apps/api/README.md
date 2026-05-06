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

## Deploy (Render / Railway)

**Deploy root must be `apps/api`** (the folder that contains `app/`, `static/`, `templates/`, and `requirements-production.txt`). If the platform builds from the monorepo root, set **Root Directory** / **`rootDir`** to `apps/api` so paths resolve correctly (see `BASE_DIR` in `app/main.py`).

**`LIVE_TRADING_ENABLED`** defaults to **`false`** in application settings and must stay **`false`** for this codebase (simulation only; no live order routing).

### Render (exact steps)

1. Push your repository to GitHub or GitLab (Render needs access).
2. In the Render dashboard: **New** → **Blueprint** (or **Web Service** if you prefer manual setup).
3. Connect the repository and select the branch to deploy.
4. **Blueprint file:** if you use Infrastructure as Code, point Render at **`apps/api/render.yaml`** (this repo’s blueprint lives next to the API). Alternatively, copy the service definition from that file into a `render.yaml` at the repository root—either way, keep **`rootDir: apps/api`** so build and start commands run inside `apps/api`.
5. Confirm the generated **Web Service** matches:
   - **Runtime:** Python  
   - **Build command:** `pip install -r requirements-production.txt`  
   - **Start command:** `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`  
   - **Health check path:** `/api/health`
6. In **Environment**, add variables from [`.env.example`](./.env.example) at minimum: `DATABASE_URL`, `JWT_SECRET_KEY` or `SECRET_KEY`, `PAPER_TRADING=true`, `LIVE_TRADING_ENABLED=false`, `REQUIRE_AUTH`, `CORS_ORIGINS`, and any market/auth keys you use.
7. **Create** / deploy and wait for the first build. Open the service URL and verify **`GET /api/health`**.

Reference: [`render.yaml`](./render.yaml) in this directory.

### Railway (exact steps)

1. Push your repository to GitHub (or connect GitLab if your Railway workflow supports it).
2. In Railway: **New Project** → **Deploy from GitHub repo** → select this repository.
3. **Critical:** open the service → **Settings** → set **Root Directory** to **`apps/api`**. This ensures Railway runs builds from the same folder as `railway.json`, `requirements-production.txt`, `app/`, `static/`, and `templates/`.
4. Under **Build** / **Deploy**, confirm config-as-code picks up **`railway.json`** in `apps/api` (or set **Config file path** to `apps/api/railway.json` if the repo root is not `apps/api`). That file sets:
   - **Build:** `pip install -r requirements-production.txt`  
   - **Start:** `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add a **PostgreSQL** (or other) database plugin if needed and copy **`DATABASE_URL`** (or your SQLAlchemy URL) into the service variables.
6. In **Variables**, set at least: `DATABASE_URL`, `JWT_SECRET_KEY` or `SECRET_KEY`, `PAPER_TRADING=true`, **`LIVE_TRADING_ENABLED=false`** (default), `REQUIRE_AUTH`, `CORS_ORIGINS`, and other keys from [`.env.example`](./.env.example) as required.
7. **Deploy** and open the generated URL; verify **`GET /api/health`**.

Reference: [`railway.json`](./railway.json) in this directory.

### Environment

Copy variables from [`.env.example`](./.env.example). Minimum for production:

| Variable | Notes |
|----------|--------|
| `DATABASE_URL` | PostgreSQL connection string (e.g. Supabase, Neon, Railway Postgres). SQLite is fine for smoke tests only. |
| `JWT_SECRET_KEY` or `SECRET_KEY` | Long random string for JWT signing. |
| `PAPER_TRADING` | Should remain `true` for this codebase (simulation only). |
| `LIVE_TRADING_ENABLED` | Defaults to **`false`**; keep **`false`** — no live order routing is implemented. |
| `REQUIRE_AUTH` | `true` for SaaS; set `false` only for internal demos. |
| `CORS_ORIGINS` | Comma-separated origins for your deployed frontend. |
| `USE_BINANCE_MARKET` or `BINANCE_PUBLIC_DATA` | `true` to use Binance public REST for market data. |

### Build & start (manual / non-IaC)

- **Install:** `pip install -r requirements-production.txt`
- **Start:** `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`  
  Render and Railway inject **`PORT`**; locally use `--port 8000` if `$PORT` is unset.

A **`Procfile`** is included for platforms that read it (`web:` → uvicorn on `$PORT`).

### Health check

Configure your platform’s HTTP health check to **`GET /api/health`**. The handler returns **503** if the database cannot be reached (useful for orchestrators); **200** when the DB responds.

### Static files & templates

The app mounts **`/static`** from `apps/api/static` and loads Jinja templates from `apps/api/templates`. Deploy with working directory at **`apps/api`** (or equivalent) so those paths exist next to the `app` package.

## Disclaimer

Simulation only. Not investment advice. No broker connectivity.
