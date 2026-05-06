"""Capital protection for paper trading (no broker connectivity)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Literal

from app.core.config import Settings


@dataclass
class RiskDecision:
    allowed: bool
    code: str
    message: str


class RiskManager:
    def __init__(self, settings: Settings) -> None:
        self._max_daily_loss_pct = float(settings.max_daily_loss_pct)
        self._max_risk_per_trade_pct = float(settings.max_risk_per_trade_pct)
        self._max_open_trades = int(settings.max_open_trades)
        self._min_confidence_pct = float(settings.min_signal_confidence_pct)
        self._emergency_stop = False
        self._day = date.today()
        self._realized_pnl_pct_today = 0.0

    def configure(
        self,
        *,
        max_daily_loss_pct: float | None = None,
        max_risk_per_trade_pct: float | None = None,
        max_open_trades: int | None = None,
        min_signal_confidence_pct: float | None = None,
    ) -> None:
        if max_daily_loss_pct is not None:
            self._max_daily_loss_pct = max_daily_loss_pct
        if max_risk_per_trade_pct is not None:
            self._max_risk_per_trade_pct = max_risk_per_trade_pct
        if max_open_trades is not None:
            self._max_open_trades = max_open_trades
        if min_signal_confidence_pct is not None:
            self._min_confidence_pct = min_signal_confidence_pct

    def set_emergency_stop(self, active: bool) -> None:
        self._emergency_stop = active

    @property
    def min_signal_confidence_pct(self) -> float:
        return self._min_confidence_pct

    def _rollover(self) -> None:
        today = date.today()
        if today != self._day:
            self._day = today
            self._realized_pnl_pct_today = 0.0

    def record_close_pnl_pct(self, delta_pct: float) -> None:
        self._rollover()
        self._realized_pnl_pct_today += float(delta_pct)

    def status(self) -> dict:
        self._rollover()
        return {
            "max_daily_loss_pct": self._max_daily_loss_pct,
            "max_risk_per_trade_pct": self._max_risk_per_trade_pct,
            "max_open_trades": self._max_open_trades,
            "min_signal_confidence_pct": self._min_confidence_pct,
            "emergency_stop": self._emergency_stop,
            "paper_trading": True,
            "today_realized_pnl_pct": round(self._realized_pnl_pct_today, 4),
            "as_of": datetime.now(timezone.utc).isoformat(),
        }

    def can_open_trade(
        self,
        *,
        confidence_pct: float,
        proposed_notional_pct: float,
        open_positions: int,
    ) -> RiskDecision:
        self._rollover()
        if self._emergency_stop:
            return RiskDecision(False, "emergency_stop", "Emergency stop is active.")
        if confidence_pct < self._min_confidence_pct:
            return RiskDecision(
                False,
                "low_confidence",
                f"Confidence {confidence_pct:.1f}% is below minimum {self._min_confidence_pct:.0f}%.",
            )
        if self._realized_pnl_pct_today <= -abs(self._max_daily_loss_pct):
            return RiskDecision(
                False,
                "max_daily_loss",
                "Max daily loss budget exhausted for paper book.",
            )
        if open_positions >= self._max_open_trades:
            return RiskDecision(
                False,
                "max_open_trades",
                "Maximum concurrent open positions reached.",
            )
        if proposed_notional_pct > self._max_risk_per_trade_pct:
            return RiskDecision(
                False,
                "max_risk_per_trade",
                f"Order risk {proposed_notional_pct:.2f}% exceeds cap {self._max_risk_per_trade_pct:.2f}%.",
            )
        return RiskDecision(True, "ok", "Risk checks passed (paper).")

    def gate_action(self) -> Literal["trade", "halt"]:
        self._rollover()
        if self._emergency_stop:
            return "halt"
        if self._realized_pnl_pct_today <= -abs(self._max_daily_loss_pct):
            return "halt"
        return "trade"
