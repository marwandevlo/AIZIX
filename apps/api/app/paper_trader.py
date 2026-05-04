"""In-memory paper execution book — swap for venue + ledger integration later."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from app.risk_manager import RiskManager

Side = Literal["buy", "sell"]


@dataclass
class OpenPosition:
    id: str
    symbol: str
    side: Side
    qty: float
    entry_price: float
    opened_at: str


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
            "win_rate_pct": win_rate,
            "wins": self._wins,
            "losses": self._losses,
            "closed_trades": len(self._closed),
            "open_positions": self.open_count(),
        }

    def execute(
        self,
        *,
        symbol: str,
        side: Side,
        qty: float,
        price: float,
        confidence_pct: float,
        risk: RiskManager,
        notional_pct: float = 1.25,
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

        oid = str(uuid.uuid4())
        pos = OpenPosition(
            id=oid,
            symbol=symbol,
            side=side,
            qty=qty,
            entry_price=price,
            opened_at=datetime.now(timezone.utc).isoformat(),
        )
        self._open[oid] = pos
        return ExecuteResult(True, "Paper position opened (simulation).", pos)

    def _pnl_for(self, pos: OpenPosition, exit_price: float) -> tuple[float, float]:
        direction = 1.0 if pos.side == "buy" else -1.0
        pnl_usd = direction * (exit_price - pos.entry_price) * pos.qty
        notional = abs(pos.entry_price * pos.qty) or 1.0
        pnl_pct = 100.0 * pnl_usd / notional
        return pnl_usd, pnl_pct

    def close_position(self, pos_id: str, exit_price: float) -> ClosedTrade | None:
        pos = self._open.pop(pos_id, None)
        if not pos:
            return None
        pnl_usd, pnl_pct = self._pnl_for(pos, exit_price)
        self._total_profit_usd += pnl_usd
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
        )
        self._closed.append(ct)
        return ct

    def close_all(self, price_hint: float) -> list[ClosedTrade]:
        """Close every open leg at a single synthetic exit (paper)."""
        out: list[ClosedTrade] = []
        for pid in list(self._open.keys()):
            ct = self.close_position(pid, price_hint)
            if ct:
                out.append(ct)
        return out
