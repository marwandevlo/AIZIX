from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import SignalRecord, TradeRecord
from app.modules.paper_trader import ClosedTrade


def persist_closed_trade(db: Session, *, user_id: int, trade: ClosedTrade, opened_at: str | None) -> None:
    row = TradeRecord(
        user_id=user_id,
        symbol=trade.symbol,
        side=trade.side,
        qty=trade.qty,
        entry_price=trade.entry_price,
        exit_price=trade.exit_price,
        pnl_usd=trade.pnl_usd,
        pnl_pct=trade.pnl_pct,
        opened_at=opened_at,
        closed_at=trade.closed_at,
        paper=True,
        confidence_pct=getattr(trade, "confidence_pct", None),
        risk_level=getattr(trade, "risk_level", None),
        reason=getattr(trade, "reason", None),
    )
    db.add(row)
    db.commit()


def persist_signal_row(
    db: Session,
    *,
    user_id: int,
    pair: str,
    action: str,
    confidence_pct: float,
    risk_score: float | None,
    risk_level: str | None,
    reason: str | None,
    as_of: str,
) -> None:
    db.add(
        SignalRecord(
            user_id=user_id,
            pair=pair,
            action=action,
            confidence_pct=confidence_pct,
            risk_score=risk_score,
            risk_level=risk_level,
            reason=reason,
            as_of=as_of,
        )
    )
    db.commit()
