import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.compounding import wallet_balances
from app.config import get_settings
from app.market_engine import MarketEngine
from app.paper_trader import PaperTrader
from app.repository import MemoryRepository, SupabaseRepository, build_repository
from app.risk_manager import RiskManager
from app.routers import bot, market, paper_trade, portfolio, signals
from app.schemas import CompoundingResponse, HealthResponse
from app.signal_engine import SignalEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    repo = build_repository(settings)
    market_eng = MarketEngine()
    risk = RiskManager(settings)
    engine = SignalEngine(market=market_eng, risk=risk, settings=settings)
    paper = PaperTrader()

    app.state.settings = settings
    app.state.repo = repo
    app.state.market = market_eng
    app.state.risk = risk
    app.state.engine = engine
    app.state.paper = paper
    app.state.last_signal = None

    kind = "supabase" if isinstance(repo, SupabaseRepository) else "memory"
    logger.info(
        "AIZIX API started (storage=%s paper_trading=%s)",
        kind,
        settings.paper_trading,
    )
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

    app = FastAPI(
        title="AIZIX API",
        version="0.2.0",
        lifespan=lifespan,
        description="Paper-only AI trading engine. Not financial advice. No live execution.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(signals.router)
    app.include_router(bot.router)
    app.include_router(market.router)
    app.include_router(portfolio.router)
    app.include_router(paper_trade.router)

    @app.get("/health", response_model=HealthResponse)
    async def health(request: Request) -> HealthResponse:
        repo = request.app.state.repo
        storage: str = "supabase" if isinstance(repo, SupabaseRepository) else "memory"
        return HealthResponse(
            ok=True,
            storage=storage,  # type: ignore[arg-type]
            paper_trading=bool(request.app.state.settings.paper_trading),
        )

    @app.get("/compounding", response_model=CompoundingResponse)
    async def compounding_root(request: Request) -> CompoundingResponse:
        repo = request.app.state.repo
        st = await repo.get_bot_state()
        b = wallet_balances(st.total_balance_usd, st.compounding_enabled)
        return CompoundingResponse(
            trading_balance=b["trading_balance"],
            safety_balance=b["safety_balance"],
            total=b["total"],
            compounding_enabled=st.compounding_enabled,
        )

    return app


app = create_app()
