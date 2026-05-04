from fastapi import APIRouter, Request

from app.compounding import wallet_balances
from app.schemas import Balances, OpenPositionOut, PortfolioResponse

router = APIRouter(tags=["portfolio"])


@router.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio(request: Request) -> PortfolioResponse:
    repo = request.app.state.repo
    paper = request.app.state.paper
    st = await repo.get_bot_state()
    b = wallet_balances(st.total_balance_usd, st.compounding_enabled)
    stats = paper.stats()
    win = stats["win_rate_pct"] if stats["closed_trades"] > 0 else st.win_rate_pct
    open_rows = [
        OpenPositionOut(
            id=p.id,
            symbol=p.symbol,
            side=p.side,
            qty=p.qty,
            entry_price=p.entry_price,
            opened_at=p.opened_at,
        )
        for p in paper.open_positions
    ]
    return PortfolioResponse(
        paper_trading=True,
        balances=Balances(**b),
        bot_status=st.status,
        paper={
            **stats,
            "win_rate_pct": win,
            "daily_pnl_usd": st.daily_pnl_usd,
        },
        open_positions=open_rows,
    )
