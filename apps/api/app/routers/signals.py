import random
from typing import Any

from fastapi import APIRouter, Request

from app.schemas import SignalPayload, SignalsResponse, WhaleActivity

router = APIRouter(tags=["signals"])


def _row_to_payload(row: dict[str, Any]) -> SignalPayload:
    wa = row.get("whale_activity") or {}
    if not isinstance(wa, dict):
        wa = {}
    whale = WhaleActivity(
        net_flow_usd=float(wa.get("net_flow_usd", 0)),
        large_wallet_moves=int(wa.get("large_wallet_moves", 0)),
        narrative=str(wa.get("narrative", "")),
    )
    return SignalPayload(
        action=row.get("action", "HOLD"),
        symbol=str(row.get("symbol", "—")),
        etf_symbol=str(row.get("etf_symbol", "—")),
        confidence_pct=float(row.get("confidence_pct", 0)),
        market_mood=str(row.get("market_mood", "Cautious ⚠️")),
        reason=str(row.get("reason", "")),
        risk_status=str(row.get("risk_status", "ok")),
        etf_bias=str(row.get("etf_bias", "")),
        whale_activity=whale,
        prices=row.get("prices") or {},
        latency_ms=float(row.get("latency_ms", 0)),
        market=row.get("market"),
    )


@router.get("/signals", response_model=SignalsResponse)
async def get_signals(request: Request) -> SignalsResponse:
    repo = request.app.state.repo
    engine = request.app.state.engine

    st = await repo.get_bot_state()
    await repo.apply_market_tick()
    raw = await engine.generate(bot_status=st.status)
    request.app.state.last_signal = raw

    await repo.insert_signal(raw)

    if hasattr(repo, "insert_trade_if_executed") and random.random() < 0.25:
        await repo.insert_trade_if_executed(str(raw["action"]), dict(raw["prices"]))

    rows = await repo.list_signals(limit=14)
    if not rows:
        latest = _row_to_payload(raw)
        return SignalsResponse(latest=latest, history=[])

    latest = _row_to_payload(rows[0])
    history = [_row_to_payload(r) for r in rows[1:9]]
    return SignalsResponse(latest=latest, history=history)
