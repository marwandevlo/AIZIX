from fastapi import APIRouter, Request

from app.schemas import (
    Balances,
    BotActionResponse,
    BotStatusResponse,
    CompoundingResponse,
    CompoundingToggleBody,
)
from app.compounding import wallet_balances

router = APIRouter(prefix="/bot", tags=["bot"])


@router.get("/status", response_model=BotStatusResponse)
async def bot_status(request: Request) -> BotStatusResponse:
    repo = request.app.state.repo
    paper = request.app.state.paper
    st = await repo.get_bot_state()
    b = wallet_balances(st.total_balance_usd, st.compounding_enabled)
    stats = paper.stats()
    win = stats["win_rate_pct"] if stats["closed_trades"] > 0 else st.win_rate_pct
    return BotStatusResponse(
        status=st.status,
        compounding_enabled=st.compounding_enabled,
        balances=Balances(**b),
        win_rate_pct=win,
        daily_pnl_usd=st.daily_pnl_usd,
    )


@router.post("/start", response_model=BotActionResponse)
async def bot_start(request: Request) -> BotActionResponse:
    request.app.state.risk.set_emergency_stop(False)
    repo = request.app.state.repo
    st = await repo.set_status("ACTIVE")
    return BotActionResponse(ok=True, status=st.status, message="Bot is ACTIVE.")


@router.post("/pause", response_model=BotActionResponse)
async def bot_pause(request: Request) -> BotActionResponse:
    repo = request.app.state.repo
    st = await repo.set_status("PAUSED")
    return BotActionResponse(ok=True, status=st.status, message="Bot is PAUSED.")


@router.post("/stop", response_model=BotActionResponse)
async def bot_stop(request: Request) -> BotActionResponse:
    request.app.state.risk.set_emergency_stop(True)
    repo = request.app.state.repo
    st = await repo.set_status("STOPPED")
    return BotActionResponse(ok=True, status=st.status, message="Emergency stop engaged.")


@router.post("/compounding", response_model=BotStatusResponse)
async def bot_compounding(
    request: Request,
    body: CompoundingToggleBody,
) -> BotStatusResponse:
    repo = request.app.state.repo
    st = await repo.set_compounding(body.enabled)
    b = wallet_balances(st.total_balance_usd, st.compounding_enabled)
    return BotStatusResponse(
        status=st.status,
        compounding_enabled=st.compounding_enabled,
        balances=Balances(**b),
        win_rate_pct=st.win_rate_pct,
        daily_pnl_usd=st.daily_pnl_usd,
    )


@router.get("/compounding", response_model=CompoundingResponse)
async def compounding_split(request: Request) -> CompoundingResponse:
    repo = request.app.state.repo
    st = await repo.get_bot_state()
    b = wallet_balances(st.total_balance_usd, st.compounding_enabled)
    return CompoundingResponse(
        trading_balance=b["trading_balance"],
        safety_balance=b["safety_balance"],
        total=b["total"],
        compounding_enabled=st.compounding_enabled,
    )
