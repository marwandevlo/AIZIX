"""Structured paper-trading performance metrics (DB-backed, verifiable)."""

from __future__ import annotations

import datetime as dt
from collections import defaultdict
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import TradeRecord
from app.modules.paper_trader import ClosedTrade, PaperTrader

DISCLAIMER = "Paper trading results. Not financial advice. Live trading disabled."


def _parse_closed_at(closed_at: str) -> dt.datetime:
    try:
        s = closed_at.replace("Z", "+00:00")
        d = dt.datetime.fromisoformat(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return d.astimezone(dt.timezone.utc)
    except Exception:
        return dt.datetime.now(dt.timezone.utc)


def _trade_from_db(row: TradeRecord) -> dict[str, Any]:
    return {
        "id": row.id,
        "closed_at": row.closed_at,
        "symbol": row.symbol,
        "side": row.side,
        "entry": row.entry_price,
        "exit": row.exit_price,
        "pnl_usd": float(row.pnl_usd),
        "pnl_pct": float(row.pnl_pct),
        "confidence_pct": float(row.confidence_pct) if row.confidence_pct is not None else None,
        "risk_level": row.risk_level,
        "reason": row.reason,
    }


def _trade_from_closed(t: ClosedTrade) -> dict[str, Any]:
    return {
        "id": t.id,
        "closed_at": t.closed_at,
        "symbol": t.symbol,
        "side": t.side,
        "entry": t.entry_price,
        "exit": t.exit_price,
        "pnl_usd": float(t.pnl_usd),
        "pnl_pct": float(t.pnl_pct),
        "confidence_pct": t.confidence_pct,
        "risk_level": t.risk_level,
        "reason": t.reason,
    }


def _canonical_trades(db: Session, user_id: int, paper: PaperTrader) -> tuple[bool, list[dict[str, Any]]]:
    rows = (
        db.query(TradeRecord)
        .filter(TradeRecord.user_id == user_id, TradeRecord.paper.is_(True))
        .order_by(TradeRecord.id.asc())
        .all()
    )
    if rows:
        return True, [_trade_from_db(r) for r in rows]
    return False, [_trade_from_closed(t) for t in paper.closed_trades_ordered()]


def _profit_factor(pnls: list[float]) -> float | None:
    gp = sum(p for p in pnls if p > 0)
    gl = -sum(p for p in pnls if p < 0)
    if gl <= 1e-12:
        return None
    return round(gp / gl, 4)


def build_performance_payload(
    *,
    db: Session,
    user_id: int,
    starting_equity_usd: float,
    paper: PaperTrader,
) -> dict[str, Any]:
    from_db, trades = _canonical_trades(db, user_id, paper)
    trades.sort(key=lambda r: (_parse_closed_at(str(r["closed_at"])).timestamp(), r.get("id") or 0))

    n = len(trades)
    st = paper.stats()
    session_daily = float(st.get("daily_profit_usd") or 0.0)

    if n == 0:
        return {
            "schema_version": 1,
            "disclaimer": DISCLAIMER,
            "source": "paper_trades",
            "data_scope": "empty",
            "metrics": {
                "total_trades": 0,
                "win_rate_pct": None,
                "profit_factor": None,
                "max_drawdown_pct": 0.0,
                "average_trade_return_pct": None,
                "best_trade_usd": None,
                "worst_trade_usd": None,
                "daily_pnl_usd": 0.0,
                "session_paper_accum_usd": round(session_daily, 4),
                "total_pnl_usd": 0.0,
            },
            "equity": {
                "starting_equity_usd": round(starting_equity_usd, 2),
                "values": [round(starting_equity_usd, 4)],
            },
            "trades": [],
            "daily": [],
        }

    pnls_usd = [float(t["pnl_usd"]) for t in trades]
    pnls_pct = [float(t["pnl_pct"]) for t in trades]
    wins = sum(1 for p in pnls_usd if p >= 0)
    losses = n - wins
    win_rate = round(100.0 * wins / n, 2) if n else None

    equity_vals: list[float] = []
    dd_series: list[float] = []
    peak = float(starting_equity_usd)
    eq = float(starting_equity_usd)
    max_dd = 0.0
    for p in pnls_usd:
        eq += p
        peak = max(peak, eq)
        dd = (peak - eq) / peak * 100 if peak > 1e-12 else 0.0
        max_dd = max(max_dd, dd)
        equity_vals.append(round(eq, 4))
        dd_series.append(round(dd, 4))

    today_utc = dt.datetime.now(dt.timezone.utc).date()
    daily_pnl_today = 0.0
    for t in trades:
        d = _parse_closed_at(str(t["closed_at"])).date()
        if d == today_utc:
            daily_pnl_today += float(t["pnl_usd"])

    by_day: dict[dt.date, dict[str, Any]] = defaultdict(
        lambda: {"trades": 0, "wins": 0, "losses": 0, "net_pnl_usd": 0.0}
    )
    dd_by_day: dict[dt.date, float] = {}
    eq_run = float(starting_equity_usd)
    peak_run = eq_run
    for t in trades:
        d = _parse_closed_at(str(t["closed_at"])).date()
        pnl = float(t["pnl_usd"])
        eq_run += pnl
        peak_run = max(peak_run, eq_run)
        dd = (peak_run - eq_run) / peak_run * 100 if peak_run > 1e-12 else 0.0
        dd_by_day[d] = dd
        row = by_day[d]
        row["trades"] += 1
        row["net_pnl_usd"] += pnl
        if pnl >= 0:
            row["wins"] += 1
        else:
            row["losses"] += 1

    daily_rows: list[dict[str, Any]] = []
    for d in sorted(by_day.keys()):
        agg = by_day[d]
        daily_rows.append(
            {
                "date": d.isoformat(),
                "trades": agg["trades"],
                "wins": agg["wins"],
                "losses": agg["losses"],
                "net_pnl_usd": round(agg["net_pnl_usd"], 4),
                "drawdown_pct": round(dd_by_day.get(d, 0.0), 4),
            }
        )

    trade_rows = []
    for t in reversed(trades):
        trade_rows.append(
            {
                "time": t["closed_at"],
                "symbol": t["symbol"],
                "side": str(t["side"]).upper(),
                "entry": round(float(t["entry"]), 6),
                "exit": round(float(t["exit"]), 6),
                "pnl_usd": round(float(t["pnl_usd"]), 4),
                "pnl_pct": round(float(t["pnl_pct"]), 4),
                "confidence_pct": round(float(t["confidence_pct"]), 2)
                if t.get("confidence_pct") is not None
                else None,
                "risk_level": t.get("risk_level"),
                "reason": t.get("reason"),
            }
        )

    total_pnl = sum(pnls_usd)
    best_usd = max(pnls_usd)
    worst_usd = min(pnls_usd)
    avg_pct = round(sum(pnls_pct) / n, 4) if n else None

    return {
        "schema_version": 1,
        "disclaimer": DISCLAIMER,
        "source": "paper_trades",
        "data_scope": "persisted_sql" if from_db else "session_memory",
        "metrics": {
            "total_trades": n,
            "win_rate_pct": win_rate,
            "profit_factor": _profit_factor(pnls_usd),
            "max_drawdown_pct": round(max_dd, 4),
            "average_trade_return_pct": avg_pct,
            "best_trade_usd": round(best_usd, 4),
            "worst_trade_usd": round(worst_usd, 4),
            "daily_pnl_usd": round(daily_pnl_today, 4),
            "session_paper_accum_usd": round(session_daily, 4),
            "total_pnl_usd": round(total_pnl, 4),
        },
        "equity": {
            "starting_equity_usd": round(starting_equity_usd, 2),
            "values": [round(starting_equity_usd, 4)] + equity_vals,
            "drawdown_pct": [0.0] + dd_series,
        },
        "trades": trade_rows,
        "daily": daily_rows,
    }
