from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, fields
from typing import Any

from fastapi import FastAPI
from app.core.config import Settings
from app.db.models import User
from app.modules.paper_trader import PaperTrader
from app.modules.risk_manager import RiskManager


@dataclass
class UserRuntime:
    dash: Any  # DashboardState — avoid circular import at runtime
    paper: PaperTrader
    risk: RiskManager
    signal_history: deque
    last_signal_snapshot: dict[str, Any] | None = None
    last_signal_persist_ts: float = 0.0


def _dash_from_prefs(user: User, settings: Settings, DashCls: type) -> Any:
    d = DashCls()
    d.total_balance_usd = float(user.balance_usd)
    d.peak_portfolio_usd = float(user.balance_usd)
    try:
        prefs = json.loads(user.prefs_json or "{}")
    except json.JSONDecodeError:
        prefs = {}
    for key in ("strategy", "trading_mode", "pair", "sl_pct", "tp_pct", "trail_pct"):
        if key in prefs and prefs[key] is not None:
            setattr(d, key, prefs[key])
    if "confidence_threshold" in prefs:
        d.confidence_threshold = float(prefs["confidence_threshold"])
    if "risk_level" in prefs and prefs["risk_level"] is not None:
        d.risk_level = int(prefs["risk_level"])
    if "max_open_trades" in prefs:
        d.max_open_trades = int(prefs["max_open_trades"])
    if "capital_usage_pct" in prefs:
        d.capital_usage_pct = float(prefs["capital_usage_pct"])
    if "compounding_enabled" in prefs:
        d.compounding_enabled = bool(prefs["compounding_enabled"])
    if "max_daily_loss_pct" in prefs:
        d.max_daily_loss_pct = float(prefs["max_daily_loss_pct"])
    if "sound_on" in prefs:
        d.sound_on = bool(prefs["sound_on"])
    if "speed" in prefs:
        d.speed = float(prefs["speed"])
    if "lang" in prefs:
        d.lang = str(prefs["lang"])[:8]
    d.max_daily_loss_pct = float(getattr(d, "max_daily_loss_pct", settings.max_daily_loss_pct))
    return d


def get_user_runtime(
    app: FastAPI,
    user: User,
    settings: Settings,
    dash_cls: type,
) -> UserRuntime:
    store: dict[int, UserRuntime] = app.state.user_runtimes
    if user.id in store:
        return store[user.id]

    dash = _dash_from_prefs(user, settings, dash_cls)
    risk = RiskManager(settings)
    risk.configure(
        min_signal_confidence_pct=dash.confidence_threshold,
        max_open_trades=dash.max_open_trades,
        max_daily_loss_pct=dash.max_daily_loss_pct,
    )
    rt = UserRuntime(
        dash=dash,
        paper=PaperTrader(),
        risk=risk,
        signal_history=deque(maxlen=200),
        last_signal_snapshot=None,
    )
    store[user.id] = rt
    return rt


def persist_dashboard_prefs(user: User, dash: Any) -> dict[str, Any]:
    keys = {f.name for f in fields(dash)}
    payload = {
        k: getattr(dash, k)
        for k in (
            "risk_level",
            "strategy",
            "trading_mode",
            "pair",
            "sl_pct",
            "tp_pct",
            "trail_pct",
            "confidence_threshold",
            "max_open_trades",
            "capital_usage_pct",
            "sound_on",
            "lang",
            "speed",
            "compounding_enabled",
            "max_daily_loss_pct",
        )
        if k in keys
    }
    user.prefs_json = json.dumps(payload)
    user.balance_usd = float(dash.total_balance_usd)
    return payload
