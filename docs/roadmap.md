# AIZIX — Product roadmap

Roadmap is directional; dates are not commitments.

## Phase 0 — Foundation (current)

- Monorepo: Next.js dashboard + FastAPI API.
- Supabase schema for profiles, bots, paper trades, wallets, signals.
- Paper trading only; mock ETF-style signal payloads.
- Risk manager (daily loss cap, capital %, max open trades, emergency stop).
- Compounding split: **70% trading wallet / 30% safety wallet** (configurable later).

## Phase 1 — Accounts & persistence

- Supabase Auth (email/OAuth) wired to `profiles`.
- Persist `bot_settings`, `paper_trades`, and `wallets` from API.
- Server-side validation of risk limits before “start bot.”

## Phase 2 — Signals & analytics

- Historical signal log and performance attribution.
- Analytics page: win rate, drawdown, exposure by synthetic “ETF” basket.
- Whale activity: curated on-chain / exchange **aggregates** (no wash trading advice).

## Phase 3 — Execution (still sandbox-first)

- Exchange paper accounts or vendor sandbox APIs.
- Slippage and fee modeling in backtests.
- Audit logs and kill switch UX.

## Phase 4 — Live trading (gated)

- Compliance review, region checks, explicit user acknowledgements.
- Optional Gate.io or other venues behind feature flags and API key vault.
- Real-time monitoring and alerting (Datadog/PagerDuty class tools).

## Open questions

- Which jurisdictions and product disclaimers apply to “ETF-style” crypto products?
- Custody vs. non-custodial wallet story for “safety wallet.”
- Tiering: retail vs. pro dashboards.
