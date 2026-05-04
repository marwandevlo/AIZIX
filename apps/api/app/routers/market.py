from fastapi import APIRouter, Request

from app.schemas import MarketResponse

router = APIRouter(tags=["market"])


@router.get("/market", response_model=MarketResponse)
async def get_market(request: Request) -> MarketResponse:
    snap = request.app.state.market.snapshot()
    return MarketResponse(snapshot=snap.model_dump())
