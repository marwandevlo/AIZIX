from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Request

from app.schemas import OpenPositionOut, PaperCloseAllResponse, PaperExecuteBody, PaperExecuteResponse

router = APIRouter(prefix="/paper-trade", tags=["paper-trade"])


def _synthetic_price(underlying_btc: float, symbol: str) -> float:
    base = max(0.02, underlying_btc / 140_000.0)
    if "3L" in symbol:
        return round(base * 1.04, 6)
    if "3S" in symbol:
        return round(base * 0.96, 6)
    return round(base, 6)


def _side_from_signal(action: str | None) -> Literal["buy", "sell"] | None:
    if action == "BUY":
        return "buy"
    if action == "SELL":
        return "sell"
    return None


@router.post("/execute", response_model=PaperExecuteResponse)
async def paper_execute(
    request: Request,
    body: PaperExecuteBody,
) -> PaperExecuteResponse:
    last: dict[str, Any] | None = getattr(request.app.state, "last_signal", None)
    repo = request.app.state.repo
    st = await repo.get_bot_state()

    if st.status != "ACTIVE":
        return PaperExecuteResponse(
            False,
            "Bot must be ACTIVE to execute paper trades.",
            None,
        )

    symbol = body.symbol or (last or {}).get("symbol")
    if not symbol or symbol == "—":
        return PaperExecuteResponse(False, "Missing symbol — poll /signals first.", None)

    side = body.side or _side_from_signal(str((last or {}).get("action", "HOLD")))
    if side is None:
        return PaperExecuteResponse(False, "No actionable side (HOLD or blocked).", None)

    confidence = float((last or {}).get("confidence_pct", 0.0))
    px = body.price
    if px is None:
        m = request.app.state.market.snapshot()
        px = _synthetic_price(m.prices.get("BTC", 60_000), symbol)

    qty = float(body.qty or 10.0)

    res = request.app.state.paper.execute(
        symbol=symbol,
        side=side,
        qty=qty,
        price=float(px),
        confidence_pct=confidence,
        risk=request.app.state.risk,
        notional_pct=float(body.notional_pct),
    )
    if not res.ok or not res.position:
        return PaperExecuteResponse(False, res.message, None)

    p = res.position
    return PaperExecuteResponse(
        True,
        res.message,
        OpenPositionOut(
            id=p.id,
            symbol=p.symbol,
            side=p.side,
            qty=p.qty,
            entry_price=p.entry_price,
            opened_at=p.opened_at,
        ),
    )


@router.post("/close-all", response_model=PaperCloseAllResponse)
async def paper_close_all(request: Request) -> PaperCloseAllResponse:
    m = request.app.state.market.snapshot()
    hint = _synthetic_price(m.prices.get("BTC", 60_000), "BTC3L/USDT")
    trades: list[dict[str, Any]] = []
    for ct in request.app.state.paper.close_all(hint):
        request.app.state.risk.record_close_pnl_pct(ct.pnl_pct * 0.15)
        trades.append(
            {
                "symbol": ct.symbol,
                "side": ct.side,
                "pnl_usd": ct.pnl_usd,
                "pnl_pct": ct.pnl_pct,
                "closed_at": ct.closed_at,
            }
        )
    return PaperCloseAllResponse(ok=True, closed=len(trades), trades=trades)
