from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Strategy
from app.deps import CurrentUser
from app.services.user_runtime import get_user_runtime

router = APIRouter(prefix="/api/strategies", tags=["strategies"])


class StrategyBody(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    sl_pct: float = 2.0
    tp_pct: float = 4.0
    trail_pct: float = 1.25
    risk_level: int = 65
    max_open_trades: int = 12
    confidence_threshold: float = 60.0


class StrategyOut(BaseModel):
    id: int
    name: str
    sl_pct: float
    tp_pct: float
    trail_pct: float
    risk_level: int
    max_open_trades: int
    confidence_threshold: float

    model_config = {"from_attributes": True}


def _dash_cls(request: Request) -> type:
    return request.app.state.dashboard_state_cls


@router.get("", response_model=list[StrategyOut])
def list_strategies(user: CurrentUser, db: Session = Depends(get_db)) -> Any:
    rows = db.query(Strategy).filter(Strategy.user_id == user.id).order_by(Strategy.id.desc()).all()
    return rows


@router.post("", response_model=StrategyOut)
def create_strategy(
    body: StrategyBody,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> Strategy:
    row = Strategy(
        user_id=user.id,
        name=body.name.strip(),
        sl_pct=body.sl_pct,
        tp_pct=body.tp_pct,
        trail_pct=body.trail_pct,
        risk_level=body.risk_level,
        max_open_trades=body.max_open_trades,
        confidence_threshold=body.confidence_threshold,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{strategy_id}")
def delete_strategy(
    strategy_id: int,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    row = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == user.id).one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.post("/{strategy_id}/apply")
def apply_strategy(
    strategy_id: int,
    request: Request,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    row = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == user.id).one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    settings = request.app.state.settings
    rt = get_user_runtime(request.app, user, settings, _dash_cls(request))
    d = rt.dash
    d.sl_pct = float(row.sl_pct)
    d.tp_pct = float(row.tp_pct)
    d.trail_pct = float(row.trail_pct)
    d.risk_level = int(row.risk_level)
    d.max_open_trades = int(row.max_open_trades)
    d.confidence_threshold = float(row.confidence_threshold)
    d.strategy = row.name
    rt.risk.configure(
        min_signal_confidence_pct=d.confidence_threshold,
        max_open_trades=d.max_open_trades,
        max_daily_loss_pct=d.max_daily_loss_pct,
    )
    return {"ok": True, "applied_strategy_id": row.id, "name": row.name}
