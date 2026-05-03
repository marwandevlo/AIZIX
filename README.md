# AIZIX

**Intelligence. Precision. Profit.**

AI-powered crypto trading SaaS focused on crypto ETF-style exposure, AI signals, risk control, compounding, safety wallet allocation, bull regime hints, and whale activity awareness. **Paper trading only** until explicitly wired to live exchanges.

## Monorepo layout

| Path | Description |
|------|-------------|
| `apps/web` | Next.js + TypeScript + Tailwind dashboard (deploy on **Vercel**) |
| `apps/api` | Python **FastAPI** trading API and AI/signal logic (deploy later on Render/Railway/Fly.io) |
| `infra/supabase` | SQL schema for Supabase Postgres |
| `docs/` | Branding and product roadmap |

## Prerequisites

- **Node.js** 20+
- **Python** 3.11+
- **Supabase** project (optional for local UI; required for auth/data)

## Quick start

### 1. Environment

From the repo root `aizix/`:

```bash
cp .env.example apps/web/.env.local
cp .env.example apps/api/.env
```

Edit values for Supabase and API URL as needed.

### 2. Frontend (`apps/web`)

```bash
cd apps/web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The dashboard uses **mock data** by default; set `NEXT_PUBLIC_API_URL` to point at the FastAPI service to load live mock responses from the API.

### 3. Backend (`apps/api`)

```bash
cd apps/api
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 4. Supabase schema

In the Supabase SQL editor (or CLI), run:

```text
infra/supabase/schema.sql
```

This creates `profiles`, `bot_settings`, `paper_trades`, `wallets`, and `signals` with Row Level Security aligned to `auth.users`.

## Scripts (optional root helpers)

Run web and API from two terminals using the commands above. A future `package.json` at the root could wrap `concurrently` for a single dev command.

## Deployment

- **Frontend:** connect `apps/web` to Vercel; set production `NEXT_PUBLIC_SUPABASE_*` and `NEXT_PUBLIC_API_URL` to your hosted API.
- **Backend:** containerize or use a Python buildpack on Render/Railway/Fly.io; set `CORS_ORIGINS` to your Vercel domain.

## Safety

No real exchange keys or live order routing are included. **Paper mode** is the default. Integrations such as Gate.io belong behind feature flags and additional compliance review.

## License

Proprietary — AIZIX. Adjust as needed for your organization.
