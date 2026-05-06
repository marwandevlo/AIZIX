from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import AuditLog, SignalRecord, TradeRecord
from app.modules.paper_trader import ClosedTrade


def persist_closed_trade(db: Session, *, user_id: int, trade: ClosedTrade, opened_at: str | None) -> None:
    reason = (getattr(trade, "reason", None) or "").strip() or "Paper position closed (recorded)"
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
        reason=reason,
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


def append_audit_log(
    db: Session,
    *,
    user_id: int,
    action_type: str,
    symbol: str = "",
    decision: str = "",
    confidence: float | None = None,
    risk_level: str | None = None,
    reason: str = "",
    metadata: dict[str, Any] | None = None,
    session_id: str | None = None,
) -> None:
    """Append-only audit row (insert only)."""
    rl = None if risk_level is None else str(risk_level)[:32]
    meta_s = json.dumps(metadata or {}, separators=(",", ":"), default=str)
    if len(meta_s) > 32000:
        meta_s = meta_s[:31997] + "...}"
    sid = (session_id or "").strip()[:64] or None
    db.add(
        AuditLog(
            user_id=user_id,
            session_id=sid,
            action_type=(action_type or "UNKNOWN")[:48],
            symbol=(symbol or "")[:64],
            decision=(decision or "")[:255],
            confidence=confidence,
            risk_level=rl,
            reason=reason or "",
            metadata_json=meta_s,
        )
    )
    db.commit()


def persist_signals_bundle(
    db: Session,
    *,
    user_id: int,
    as_of: str,
    signal_rows: list[dict[str, Any]],
    session_id: str | None = None,
) -> None:
    """Persist all signals from one engine snapshot + matching SIGNAL audit rows (single commit)."""
    if not signal_rows:
        return
    sid = (session_id or "").strip()[:64] or None
    for row in signal_rows:
        pair = str(row.get("pair", ""))[:32]
        action = str(row.get("action", "HOLD"))[:8]
        conf = float(row.get("confidence_pct", 0))
        rs = row.get("risk_score")
        risk_score = float(rs) if rs is not None else None
        rl = row.get("risk_level")
        risk_level = str(rl)[:16] if rl is not None else None
        reason = row.get("reason")
        meta = {
            "as_of": as_of,
            "risk_score": risk_score,
            "engine_snapshot": True,
        }
        meta_s = json.dumps(meta, separators=(",", ":"), default=str)
        db.add(
            SignalRecord(
                user_id=user_id,
                pair=pair,
                action=action,
                confidence_pct=conf,
                risk_score=risk_score,
                risk_level=risk_level,
                reason=str(reason) if reason is not None else None,
                as_of=as_of[:64],
            )
        )
        db.add(
            AuditLog(
                user_id=user_id,
                session_id=sid,
                action_type="SIGNAL",
                symbol=pair,
                decision=action,
                confidence=conf,
                risk_level=str(rl)[:32] if rl is not None else None,
                reason=str(reason or "")[:8000],
                metadata_json=meta_s,
            )
        )
    db.commit()


def fetch_audit_logs(
    db: Session,
    *,
    user_id: int,
    limit: int = 100,
    action_type: str | None = None,
    symbol_contains: str | None = None,
    order: str = "desc",
) -> list[dict[str, Any]]:
    limit = max(1, min(500, limit))
    q = db.query(AuditLog).filter(AuditLog.user_id == user_id)
    if action_type and action_type.strip():
        q = q.filter(AuditLog.action_type == action_type.strip()[:48])
    if symbol_contains and symbol_contains.strip():
        q = q.filter(AuditLog.symbol.contains(symbol_contains.strip()))
    rows = q.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(limit).all()
    if order.lower() == "asc":
        rows = list(reversed(rows))
    out: list[dict[str, Any]] = []
    for r in rows:
        try:
            meta = json.loads(r.metadata_json or "{}")
        except json.JSONDecodeError:
            meta = {}
        out.append(
            {
                "id": r.id,
                "timestamp": r.created_at.isoformat() if r.created_at else None,
                "user_id": r.user_id,
                "session_id": r.session_id,
                "action_type": r.action_type,
                "symbol": r.symbol,
                "decision": r.decision,
                "confidence": r.confidence,
                "risk_level": r.risk_level,
                "reason": r.reason,
                "metadata": meta,
            }
        )
    return out


def fetch_signal_history(db: Session, *, user_id: int, limit: int = 100) -> list[dict[str, Any]]:
    limit = max(1, min(200, limit))
    rows = (
        db.query(SignalRecord)
        .filter(SignalRecord.user_id == user_id)
        .order_by(SignalRecord.id.desc())
        .limit(limit)
        .all()
    )
    out: list[dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "id": r.id,
                "timestamp": r.created_at.isoformat() if r.created_at else None,
                "pair": r.pair,
                "action": r.action,
                "confidence_pct": r.confidence_pct,
                "risk_score": r.risk_score,
                "risk_level": r.risk_level,
                "reason": r.reason,
                "as_of": r.as_of,
            }
        )
    return out
