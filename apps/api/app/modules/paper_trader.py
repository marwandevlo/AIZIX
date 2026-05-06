"""In-memory paper execution with trailing stop metadata."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from app.modules.risk_manager import RiskManager
from app.modules.trailing_stop import next_trail_price

Side = Literal["buy", "sell"]


@dataclass
class OpenPosition:
    id: str
    symbol: str
    side: Side
    qty: float
    entry_price: float
    opened_at: str
    sl_price: float
    tp_price: float
    trail_pct: float
    stop_price: float
    stop_mode: Literal["OPEN", "TRAIL"] = "OPEN"
    confidence_pct: float | None = None
    risk_level: str | None = None
    reason: str | None = None


@dataclass
class ClosedTrade:
    id: str
    symbol: str
    side: Side
    qty: float
    entry_price: float
    exit_price: float
    pnl_usd: float
    pnl_pct: float
    closed_at: str
    confidence_pct: float | None = None
    risk_level: str | None = None
    reason: str | None = None


@dataclass
class ExecuteResult:
    ok: bool
    message: str
    position: OpenPosition | None = None


class PaperTrader:
    def __init__(self) -> None:
        self._open: dict[str, OpenPosition] = {}
        self._closed: list[ClosedTrade] = []
        self._wins = 0
        self._losses = 0
        self._total_profit_usd = 0.0
        self._daily_profit_usd = 0.0

    @property
    def open_positions(self) -> list[OpenPosition]:
        return list(self._open.values())

    def open_count(self) -> int:
        return len(self._open)

    def stats(self) -> dict:
        denom = self._wins + self._losses
        win_rate = round(100.0 * self._wins / denom, 2) if denom else 0.0
        return {
            "total_profit_usd": round(self._total_profit_usd, 2),
            "daily_profit_usd": round(self._daily_profit_usd, 2),
            "win_rate_pct": win_rate,
            "wins": self._wins,
            "losses": self._losses,
            "closed_trades": len(self._closed),
            "open_positions": self.open_count(),
        }

    def recent_closed(self, limit: int = 25) -> list[ClosedTrade]:
        limit = max(1, min(100, limit))
        return list(self._closed[-limit:])

    def closed_trades_ordered(self) -> list[ClosedTrade]:
        """Chronological closed trades (close order matches append order)."""
        return list(self._closed)

    def _sl_tp(
        self, side: Side, entry: float, sl_pct: float, tp_pct: float
    ) -> tuple[float, float]:
        sl_pct = max(0.05, sl_pct)
        tp_pct = max(0.05, tp_pct)
        if side == "buy":
            return entry * (1 - sl_pct / 100), entry * (1 + tp_pct / 100)
        return entry * (1 + sl_pct / 100), entry * (1 - tp_pct / 100)

    def execute(
        self,
        *,
        symbol: str,
        side: Side,
        qty: float,
        price: float,
        confidence_pct: float,
        risk: RiskManager,
        sl_pct: float,
        tp_pct: float,
        trail_pct: float,
        notional_pct: float = 1.25,
        risk_level: str | None = None,
        reason: str | None = None,
    ) -> ExecuteResult:
        qty = max(0.0, float(qty))
        price = max(1e-9, float(price))
        decision = risk.can_open_trade(
            confidence_pct=confidence_pct,
            proposed_notional_pct=notional_pct,
            open_positions=self.open_count(),
        )
        if not decision.allowed:
            return ExecuteResult(False, decision.message, None)

        sl_p, tp_p = self._sl_tp(side, price, sl_pct, tp_pct)
        stop_px, mode = next_trail_price(
            side=side,
            entry=price,
            mark=price,
            trail_pct=trail_pct,
            current_trail=None,
        )

        oid = str(uuid.uuid4())
        pos = OpenPosition(
            id=oid,
            symbol=symbol,
            side=side,
            qty=qty,
            entry_price=price,
            opened_at=datetime.now(timezone.utc).isoformat(),
            sl_price=sl_p,
            tp_price=tp_p,
            trail_pct=trail_pct,
            stop_price=stop_px,
            stop_mode=mode,
            confidence_pct=float(confidence_pct),
            risk_level=risk_level,
            reason=reason,
        )
        self._open[oid] = pos
        return ExecuteResult(True, "Paper position opened (simulation).", pos)

    def _pnl_for(self, pos: OpenPosition, exit_price: float) -> tuple[float, float]:
        direction = 1.0 if pos.side == "buy" else -1.0
        pnl_usd = direction * (exit_price - pos.entry_price) * pos.qty
        notional = abs(pos.entry_price * pos.qty) or 1.0
        pnl_pct = 100.0 * pnl_usd / notional
        return pnl_usd, pnl_pct

    def mark_at(self, pos: OpenPosition, mark: float) -> dict[str, float]:
        """Unrealized P&L at mark price (paper)."""
        pnl_usd, pnl_pct = self._pnl_for(pos, mark)
        return {
            "current_price": round(mark, 6),
            "pnl_usd": round(pnl_usd, 4),
            "pnl_pct": round(pnl_pct, 4),
        }

    def close_position(self, pos_id: str, exit_price: float) -> ClosedTrade | None:
        pos = self._open.pop(pos_id, None)
        if not pos:
            return None
        pnl_usd, pnl_pct = self._pnl_for(pos, exit_price)
        self._total_profit_usd += pnl_usd
        self._daily_profit_usd += pnl_usd
        if pnl_usd >= 0:
            self._wins += 1
        else:
            self._losses += 1
        ct = ClosedTrade(
            id=str(uuid.uuid4()),
            symbol=pos.symbol,
            side=pos.side,
            qty=pos.qty,
            entry_price=pos.entry_price,
            exit_price=exit_price,
            pnl_usd=round(pnl_usd, 4),
            pnl_pct=round(pnl_pct, 4),
            closed_at=datetime.now(timezone.utc).isoformat(),
            confidence_pct=getattr(pos, "confidence_pct", None),
            risk_level=getattr(pos, "risk_level", None),
            reason=getattr(pos, "reason", None),
        )
        self._closed.append(ct)
        return ct

    def close_all(self, prices: dict[str, float], default_price: float) -> list[ClosedTrade]:
        out: list[ClosedTrade] = []
        for pid, pos in list(self._open.items()):
            px = prices.get(pos.symbol, default_price)
            ct = self.close_position(pid, px)
            if ct:
                out.append(ct)
        return out

    def refresh_trailing(self, prices: dict[str, float]) -> None:
        for pos in self._open.values():
            mark = prices.get(pos.symbol, pos.entry_price)
            stop_px, mode = next_trail_price(
                side=pos.side,
                entry=pos.entry_price,
                mark=mark,
                trail_pct=pos.trail_pct,
                current_trail=pos.stop_price,
            )
            pos.stop_price = stop_px
            pos.stop_mode = mode
