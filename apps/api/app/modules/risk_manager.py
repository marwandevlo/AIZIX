from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal


@dataclass(frozen=True)
class RiskLimits:
    """Paper-trading risk envelope. Tune via bot settings / env in later phases."""

    max_daily_loss_pct: float = 3.0
    max_capital_pct_per_trade: float = 10.0
    max_open_trades: int = 3
    emergency_stop: bool = False


@dataclass
class DailyLedger:
    day: date
    realized_pnl_pct: float = 0.0
    open_trades: int = 0


class RiskManager:
    """Enforces loss caps, position sizing, concurrency, and kill switch."""

    def __init__(self, limits: RiskLimits | None = None) -> None:
        self.limits = limits or RiskLimits()
        self._ledger = DailyLedger(day=date.today())

    def _rollover_if_needed(self) -> None:
        today = date.today()
        if self._ledger.day != today:
            self._ledger = DailyLedger(day=today)

    def set_emergency_stop(self, active: bool) -> None:
        object.__setattr__(self.limits, "emergency_stop", active)

    def update_limits(
        self,
        *,
        max_daily_loss_pct: float | None = None,
        max_capital_pct_per_trade: float | None = None,
        max_open_trades: int | None = None,
    ) -> None:
        if max_daily_loss_pct is not None:
            object.__setattr__(self.limits, "max_daily_loss_pct", max_daily_loss_pct)
        if max_capital_pct_per_trade is not None:
            object.__setattr__(
                self.limits, "max_capital_pct_per_trade", max_capital_pct_per_trade
            )
        if max_open_trades is not None:
            object.__setattr__(self.limits, "max_open_trades", max_open_trades)

    def record_close_pnl_pct(self, delta_pct: float) -> None:
        self._rollover_if_needed()
        self._ledger.realized_pnl_pct += delta_pct

    def set_open_trades(self, count: int) -> None:
        self._rollover_if_needed()
        self._ledger.open_trades = max(0, count)

    def status(self) -> dict:
        self._rollover_if_needed()
        return {
            "max_daily_loss_pct": self.limits.max_daily_loss_pct,
            "max_capital_pct_per_trade": self.limits.max_capital_pct_per_trade,
            "max_open_trades": self.limits.max_open_trades,
            "emergency_stop": self.limits.emergency_stop,
            "today_realized_pnl_pct": round(self._ledger.realized_pnl_pct, 4),
            "open_trades": self._ledger.open_trades,
            "as_of": datetime.utcnow().isoformat() + "Z",
        }

    def can_open_trade(self, proposed_notional_pct: float) -> tuple[bool, str]:
        self._rollover_if_needed()
        if self.limits.emergency_stop:
            return False, "emergency_stop_active"
        if self._ledger.realized_pnl_pct <= -abs(self.limits.max_daily_loss_pct):
            return False, "max_daily_loss_breached"
        if self._ledger.open_trades >= self.limits.max_open_trades:
            return False, "max_open_trades_reached"
        if proposed_notional_pct > self.limits.max_capital_pct_per_trade:
            return False, "capital_pct_exceeded"
        return True, "ok"

    def gate_action(self) -> Literal["trade", "halt"]:
        ok, _ = self.can_open_trade(self.limits.max_capital_pct_per_trade)
        return "trade" if ok else "halt"
