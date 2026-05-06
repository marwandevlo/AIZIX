from __future__ import annotations

from collections import deque
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import TradeRecord
from app.modules.compounding import wallet_balances
from app.modules.paper_trader import PaperTrader
from app.modules.risk_manager import RiskManager


def build_portfolio_payload(
    *,
    db: Session,
    user_id: int,
    dash: Any,
    paper: PaperTrader,
    risk: RiskManager,
    signal_history: deque,
    last_signal_snapshot: dict[str, Any] | None,
    market: Any,
) -> dict[str, Any]:
    m = market.snapshot()
    paper.refresh_trailing(m.prices)
    st = paper.stats()
    wallets = wallet_balances(dash.total_balance_usd, dash.compounding_enabled)
    positions: list[dict[str, Any]] = []
    unrealized_usd = 0.0
    gross_notional = 0.0
    for p in paper.open_positions:
        badge = "TRAIL" if p.stop_mode == "TRAIL" else "OPEN"
        mark = float(m.prices.get(p.symbol, p.entry_price))
        mk = paper.mark_at(p, mark)
        unrealized_usd += mk["pnl_usd"]
        gross_notional += abs(p.entry_price * p.qty)
        side_u = p.side.upper()
        pos_type = "Long" if p.side == "buy" else "Short"
        positions.append(
            {
                "id": p.id,
                "pair": p.symbol,
                "side": side_u,
                "type": pos_type,
                "qty": p.qty,
                "size": p.qty,
                "entry": p.entry_price,
                "current_price": mk["current_price"],
                "pnl_usd": mk["pnl_usd"],
                "pnl_pct": mk["pnl_pct"],
                "sl": round(p.sl_price, 6),
                "tp": round(p.tp_price, 6),
                "trailing_sl": round(p.stop_price, 6),
                "stop_badge": badge,
            }
        )
    portfolio_value = dash.total_balance_usd + st["total_profit_usd"] + unrealized_usd
    dash.peak_portfolio_usd = max(dash.peak_portfolio_usd, portfolio_value)
    dd_pct = (
        (dash.peak_portfolio_usd - portfolio_value) / dash.peak_portfolio_usd * 100
        if dash.peak_portfolio_usd > 1e-9
        else 0.0
    )
    risk_exposure_pct = (gross_notional / portfolio_value) * 100 if portfolio_value > 1e-9 else 0.0

    primary_ai: dict[str, Any] | None = None
    if last_signal_snapshot:
        for row in last_signal_snapshot.get("signals", []):
            if row.get("pair") == dash.pair:
                primary_ai = {
                    "pair": row["pair"],
                    "action": row["action"],
                    "confidence_pct": row["confidence_pct"],
                    "risk_level": row.get("risk_level"),
                    "risk_score": row.get("risk_score"),
                    "reason": row.get("reason"),
                    "stance": row.get("stance"),
                }
                break

    db_trades = (
        db.query(TradeRecord)
        .filter(TradeRecord.user_id == user_id)
        .order_by(TradeRecord.id.desc())
        .limit(40)
        .all()
    )
    recent_trades = [
        {
            "symbol": t.symbol,
            "side": t.side,
            "qty": t.qty,
            "entry": t.entry_price,
            "exit": t.exit_price,
            "pnl_usd": t.pnl_usd,
            "pnl_pct": t.pnl_pct,
            "closed_at": t.closed_at,
            "reason": getattr(t, "reason", None) or "—",
        }
        for t in db_trades
    ]
    if not recent_trades:
        recent_trades = [
            {
                "symbol": t.symbol,
                "side": t.side,
                "qty": t.qty,
                "entry": t.entry_price,
                "exit": t.exit_price,
                "pnl_usd": t.pnl_usd,
                "pnl_pct": t.pnl_pct,
                "closed_at": t.closed_at,
                "reason": (getattr(t, "reason", None) or "").strip() or "—",
            }
            for t in paper.recent_closed(25)
        ]

    signal_history_list = list(signal_history)[-80:]

    return {
        "balance_usd": dash.total_balance_usd,
        "portfolio_value_usd": round(portfolio_value, 2),
        "daily_profit_usd": st["daily_profit_usd"],
        "total_profit_usd": st["total_profit_usd"],
        "win_rate_pct": st["win_rate_pct"],
        "drawdown_pct": round(dd_pct, 3),
        "risk_exposure_pct": round(min(risk_exposure_pct, 999.0), 3),
        "safety_wallet_usd": wallets["safety_balance"],
        "trading_wallet_usd": wallets["trading_balance"],
        "total_usd": wallets["total"],
        "open_positions": st["open_positions"],
        "bot_status": dash.status,
        "risk_level": dash.risk_level,
        "strategy": dash.strategy,
        "trading_mode": dash.trading_mode,
        "max_open_trades": dash.max_open_trades,
        "capital_usage_pct": dash.capital_usage_pct,
        "max_daily_loss_pct": dash.max_daily_loss_pct,
        "risk_controller": risk.status(),
        "selected_pair": dash.pair,
        "sl_pct": dash.sl_pct,
        "tp_pct": dash.tp_pct,
        "trail_pct": dash.trail_pct,
        "confidence_threshold": dash.confidence_threshold,
        "sound_on": dash.sound_on,
        "lang": dash.lang,
        "speed": dash.speed,
        "compounding_enabled": dash.compounding_enabled,
        "positions": positions,
        "recent_trades": recent_trades,
        "signal_history": signal_history_list,
        "primary_ai": primary_ai,
    }
