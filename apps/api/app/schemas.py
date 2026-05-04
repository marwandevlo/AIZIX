from typing import Any, Literal

from pydantic import BaseModel, Field

BotStatus = Literal["ACTIVE", "PAUSED", "STOPPED"]
SignalAction = Literal["BUY", "SELL", "HOLD"]


class Balances(BaseModel):
    trading_balance: float = Field(..., description="USD in trading wallet")
    safety_balance: float = Field(..., description="USD in safety wallet")
    total: float = Field(..., description="Total USD")


class CompoundingResponse(BaseModel):
    trading_balance: float
    safety_balance: float
    total: float
    compounding_enabled: bool


class WhaleActivity(BaseModel):
    net_flow_usd: float
    large_wallet_moves: int
    narrative: str


class SignalPayload(BaseModel):
    action: SignalAction
    symbol: str = "—"
    etf_symbol: str = "—"
    confidence_pct: float
    market_mood: str
    reason: str
    risk_status: str = "ok"
    etf_bias: str
    whale_activity: WhaleActivity
    prices: dict[str, float]
    latency_ms: float
    market: dict[str, Any] | None = None


class SignalsResponse(BaseModel):
    latest: SignalPayload
    history: list[SignalPayload]


class BotStatusResponse(BaseModel):
    status: BotStatus
    compounding_enabled: bool
    balances: Balances
    win_rate_pct: float
    daily_pnl_usd: float


class BotActionResponse(BaseModel):
    ok: bool
    status: BotStatus
    message: str


class CompoundingToggleBody(BaseModel):
    enabled: bool


class HealthResponse(BaseModel):
    ok: bool
    storage: Literal["supabase", "memory"]
    paper_trading: bool


class MarketResponse(BaseModel):
    snapshot: dict[str, Any]


class OpenPositionOut(BaseModel):
    id: str
    symbol: str
    side: str
    qty: float
    entry_price: float
    opened_at: str


class PortfolioResponse(BaseModel):
    paper_trading: bool
    balances: Balances
    bot_status: BotStatus
    paper: dict[str, Any]
    open_positions: list[OpenPositionOut]


class PaperExecuteBody(BaseModel):
    symbol: str | None = None
    side: Literal["buy", "sell"] | None = None
    qty: float | None = None
    price: float | None = None
    notional_pct: float = 1.25


class PaperExecuteResponse(BaseModel):
    ok: bool
    message: str
    position: OpenPositionOut | None = None


class PaperCloseAllResponse(BaseModel):
    ok: bool
    closed: int
    trades: list[dict[str, Any]]
