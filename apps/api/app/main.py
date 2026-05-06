"""AIZIX multi-user trading OS — FastAPI + JWT + paper execution."""

from __future__ import annotations

import json
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.saas import TenantContext
from app.db.bootstrap import ensure_demo_user, init_db
from app.db.database import SessionLocal, get_db
from app.db.models import Portfolio, User
from app.deps import CurrentUser
from app.modules.backtest_engine import (
    compare_backtests_binance,
    compare_backtests_synthetic,
    run_backtest,
    run_backtest_binance,
)
from app.modules.market_engine import PAIRS, MarketEngine, SyntheticMarketEngine
from app.modules.compounding import wallet_balances
from app.modules.signal_engine import SignalEngine
from app.routers import auth as auth_router
from app.routers import strategies as strategies_router
from app.services.persistence import persist_closed_trade, persist_signal_row
from app.services.performance_report import build_performance_payload
from app.services.portfolio_view import build_portfolio_payload
from app.services.user_runtime import get_user_runtime, persist_dashboard_prefs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

BotStatus = Literal["ACTIVE", "PAUSED", "STOPPED"]


class ClosePositionBody(BaseModel):
    position_id: str


@dataclass
class DashboardState:
    status: BotStatus = "ACTIVE"
    risk_level: int = 65
    strategy: str = "AI Adaptive Strategy"
    trading_mode: str = "ETF MODE"
    pair: str = "BTC3L/USDT"
    sl_pct: float = 2.0
    tp_pct: float = 4.0
    trail_pct: float = 1.25
    confidence_threshold: float = 60.0
    max_open_trades: int = 12
    capital_usage_pct: float = 68.0
    sound_on: bool = True
    lang: str = "en"
    speed: float = 1.0
    compounding_enabled: bool = True
    total_balance_usd: float = 12_540.25
    last_backtest: dict[str, Any] | None = None
    peak_portfolio_usd: float = 12_540.25
    max_daily_loss_pct: float = 5.0


class BacktestRequest(BaseModel):
    pair: str = "BTC3L/USDT"
    sl_pct: float = 2.0
    tp_pct: float = 4.0
    days: int = 42
    source: Literal["binance", "synthetic"] = "binance"
    optimization_objective: Literal["total_return", "return_over_drawdown", "profit_factor"] = (
        "return_over_drawdown"
    )


class BacktestCompareRequest(BaseModel):
    days: int = 90
    source: Literal["binance", "synthetic"] = "binance"
    optimization_objective: Literal["total_return", "return_over_drawdown", "profit_factor"] = (
        "return_over_drawdown"
    )
    configs: list[dict[str, Any]] = Field(
        default_factory=lambda: [
            {"label": "BTC core", "pair": "BTC3L/USDT", "sl_pct": 2.0, "tp_pct": 4.0},
            {"label": "ETH sleeve", "pair": "ETH3L/USDT", "sl_pct": 2.0, "tp_pct": 5.0},
        ]
    )


class BotBody(BaseModel):
    risk_level: int | None = None


class PaperExecuteBody(BaseModel):
    symbol: str | None = None
    side: str | None = Field(default=None, description="buy or sell")
    qty: float | None = None
    confidence_pct: float | None = None
    reason: str | None = Field(default=None, description="Attribution note stored with closed trade metadata")


class DashPrefsBody(BaseModel):
    risk_level: int | None = None
    strategy: str | None = None
    trading_mode: str | None = None
    pair: str | None = None
    sl_pct: float | None = None
    tp_pct: float | None = None
    trail_pct: float | None = None
    confidence_threshold: float | None = None
    max_open_trades: int | None = None
    capital_usage_pct: float | None = None
    sound_on: bool | None = None
    lang: str | None = None
    speed: float | None = None
    compounding_enabled: bool | None = None
    max_daily_loss_pct: float | None = None


class StrategySaveBody(BaseModel):
    name: str = Field(min_length=1, max_length=128)


def _run_backtest_core(body: BacktestRequest, binance_base: str) -> dict[str, Any]:
    obj = body.optimization_objective
    if body.source == "synthetic":
        return run_backtest(
            pair=body.pair,
            sl_pct=body.sl_pct,
            tp_pct=body.tp_pct,
            days=body.days,
            objective=obj,
        )
    return run_backtest_binance(
        pair=body.pair,
        sl_pct=body.sl_pct,
        tp_pct=body.tp_pct,
        days=body.days,
        base_url=binance_base,
        objective=obj,
    )


def _sync_portfolio_row(db: Session, user: User, dash: DashboardState, portfolio_value: float) -> None:
    row = db.query(Portfolio).filter(Portfolio.user_id == user.id).one_or_none()
    if not row:
        row = Portfolio(user_id=user.id)
        db.add(row)
    row.balance_usd = float(dash.total_balance_usd)
    row.portfolio_value_usd = float(portfolio_value)
    row.peak_equity_usd = float(dash.peak_portfolio_usd)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db()
    sdb = SessionLocal()
    try:
        ensure_demo_user(sdb, settings)
    finally:
        sdb.close()

    if settings.use_binance_market:
        market = MarketEngine(
            base_url=settings.binance_base_url,
            fallback_on_error=True,
        )
    else:
        market = SyntheticMarketEngine()

    engine = SignalEngine(market=market, settings=settings)

    app.state.settings = settings
    app.state.market = market
    app.state.signal_engine = engine
    app.state.user_runtimes = {}
    app.state.dashboard_state_cls = DashboardState
    app.state.tenant = TenantContext()

    if settings.require_auth and settings.jwt_secret_key == "change-me-in-production":
        logger.warning("JWT_SECRET_KEY is still default — set a strong secret for production.")
    logger.info(
        "AIZIX SaaS — auth=%s db=%s — http://127.0.0.1:%s/",
        settings.require_auth,
        "sqlite" if settings.database_url.startswith("sqlite") else "postgres",
        settings.api_port,
    )
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

    app = FastAPI(
        title="AIZIX Trading Operating System",
        version="3.0.0",
        lifespan=lifespan,
        description="Multi-user paper trading with Binance market data and JWT auth.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router.router)
    app.include_router(strategies_router.router)

    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> Any:
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "title": "AIZIX",
                "pairs": list(PAIRS),
                "require_auth": settings.require_auth,
            },
        )

    @app.get("/login", response_class=HTMLResponse)
    async def login_page(request: Request) -> Any:
        return templates.TemplateResponse(request, "login.html", {"title": "Sign in"})

    @app.get("/signup", response_class=HTMLResponse)
    async def signup_page(request: Request) -> Any:
        return templates.TemplateResponse(request, "signup.html", {"title": "Create account"})

    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard_quick() -> HTMLResponse:
        return HTMLResponse(
            "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8' />"
            "<meta name='viewport' content='width=device-width, initial-scale=1' />"
            "<title>AIZIX · Dashboard</title></head>"
            "<body style='margin:0;min-height:100vh;background:#060816;color:#e2e8f0;"
            "font-family:system-ui,sans-serif;display:flex;align-items:center;"
            "justify-content:center;flex-direction:column;gap:1rem'>"
            "<h1 style='margin:0;font-weight:600'>AIZIX</h1>"
            "<p style='color:#94a3b8'>SaaS paper mode · API online</p>"
            "<p><a style='color:#6C5CE7' href='/'>Console</a> · "
            "<a style='color:#6C5CE7' href='/api/health'>Health</a></p>"
            "</body></html>"
        )

    @app.get("/api/health")
    async def api_health() -> dict[str, Any]:
        return {
            "ok": True,
            "version": "3.0.0",
            "paper_trading": True,
            "product": "aizix-os",
            "require_auth": settings.require_auth,
            "market": "binance" if settings.use_binance_market else "synthetic",
        }

    @app.get("/api/market")
    async def api_market(request: Request) -> dict[str, Any]:
        m = request.app.state.market.snapshot()
        return {
            "as_of": m.as_of,
            "prices": m.prices,
            "pairs": list(PAIRS),
            "volume_24h_usd": m.volume_24h_usd,
            "volatility_annualized_pct": m.volatility_annualized_pct,
            "trend": m.trend,
            "sentiment_score": m.sentiment_score,
            "momentum_pct_by_pair": m.momentum_pct_by_pair,
            "change_pct_by_pair": m.momentum_pct_by_pair,
            "liquidity_flow": {
                "net_flow_usd": m.whale_activity.net_flow_usd,
                "large_moves": m.whale_activity.large_wallet_moves,
                "note": m.whale_activity.narrative,
            },
            "whale_activity": {
                "net_flow_usd": m.whale_activity.net_flow_usd,
                "large_wallet_moves": m.whale_activity.large_wallet_moves,
                "narrative": m.whale_activity.narrative,
            },
        }

    @app.get("/api/signals")
    async def api_signals(
        request: Request,
        user: CurrentUser,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        rt = get_user_runtime(request.app, user, settings, DashboardState)
        dash = rt.dash
        eng: SignalEngine = request.app.state.signal_engine
        result = await eng.all_signals(bot_active=dash.status == "ACTIVE", risk=rt.risk)
        rt.last_signal_snapshot = result
        hist = rt.signal_history
        for row in result.get("signals", []):
            if row.get("pair") == dash.pair:
                hist.append(
                    {
                        "as_of": result.get("as_of"),
                        "pair": row["pair"],
                        "action": row["action"],
                        "confidence_pct": row["confidence_pct"],
                        "risk_score": row.get("risk_score"),
                        "risk_level": row.get("risk_level"),
                        "reason": row.get("reason"),
                    }
                )
                break
        now = time.time()
        if now - rt.last_signal_persist_ts >= 45.0:
            for row in result.get("signals", []):
                if row.get("pair") == dash.pair:
                    persist_signal_row(
                        db,
                        user_id=user.id,
                        pair=str(row["pair"]),
                        action=str(row["action"]),
                        confidence_pct=float(row["confidence_pct"]),
                        risk_score=row.get("risk_score"),
                        risk_level=str(row.get("risk_level")) if row.get("risk_level") else None,
                        reason=row.get("reason"),
                        as_of=str(result.get("as_of", "")),
                    )
                    rt.last_signal_persist_ts = now
                    break
        return result

    @app.get("/api/positions")
    async def api_positions(
        request: Request,
        user: CurrentUser,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        rt = get_user_runtime(request.app, user, settings, DashboardState)
        payload = build_portfolio_payload(
            db=db,
            user_id=user.id,
            dash=rt.dash,
            paper=rt.paper,
            risk=rt.risk,
            signal_history=rt.signal_history,
            last_signal_snapshot=rt.last_signal_snapshot,
            market=request.app.state.market,
        )
        return {"positions": payload["positions"]}

    @app.get("/api/portfolio")
    async def api_portfolio(
        request: Request,
        user: CurrentUser,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        rt = get_user_runtime(request.app, user, settings, DashboardState)
        return build_portfolio_payload(
            db=db,
            user_id=user.id,
            dash=rt.dash,
            paper=rt.paper,
            risk=rt.risk,
            signal_history=rt.signal_history,
            last_signal_snapshot=rt.last_signal_snapshot,
            market=request.app.state.market,
        )

    @app.get("/api/performance")
    async def api_performance(
        request: Request,
        user: CurrentUser,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        rt = get_user_runtime(request.app, user, settings, DashboardState)
        return build_performance_payload(
            db=db,
            user_id=user.id,
            starting_equity_usd=float(rt.dash.total_balance_usd),
            paper=rt.paper,
        )

    @app.get("/api/compounding")
    async def api_compounding(request: Request, user: CurrentUser) -> dict[str, Any]:
        rt = get_user_runtime(request.app, user, settings, DashboardState)
        dash = rt.dash
        w = wallet_balances(dash.total_balance_usd, dash.compounding_enabled)
        return {
            "trading_balance": w["trading_balance"],
            "safety_balance": w["safety_balance"],
            "total": w["total"],
            "compounding_enabled": dash.compounding_enabled,
        }

    @app.get("/api/preferences")
    async def api_get_preferences(
        request: Request,
        user: CurrentUser,
        db: Session = Depends(get_db),
        invalidate_runtime: bool = False,
    ) -> dict[str, Any]:
        """Return persisted dashboard prefs + portfolio snapshot; optional cache bust for this user."""
        if invalidate_runtime:
            request.app.state.user_runtimes.pop(user.id, None)
        db.refresh(user)
        try:
            prefs = json.loads(user.prefs_json or "{}")
        except json.JSONDecodeError:
            prefs = {}
        prow = db.query(Portfolio).filter(Portfolio.user_id == user.id).one_or_none()
        portfolio_summary = None
        if prow:
            portfolio_summary = {
                "balance_usd": prow.balance_usd,
                "portfolio_value_usd": prow.portfolio_value_usd,
                "peak_equity_usd": prow.peak_equity_usd,
                "updated_at": prow.updated_at.isoformat() if prow.updated_at else None,
            }
        return {
            "user_id": user.id,
            "email": user.email,
            "balance_usd": user.balance_usd,
            "prefs": prefs,
            "portfolio": portfolio_summary,
        }

    @app.post("/api/bot/start")
    async def bot_start(
        request: Request,
        user: CurrentUser,
        body: BotBody | None = None,
    ) -> dict[str, str]:
        rt = get_user_runtime(request.app, user, settings, DashboardState)
        dash = rt.dash
        rt.risk.set_emergency_stop(False)
        dash.status = "ACTIVE"
        if body and body.risk_level is not None:
            dash.risk_level = max(1, min(100, int(body.risk_level)))
        return {"status": dash.status}

    @app.post("/api/bot/pause")
    async def bot_pause(request: Request, user: CurrentUser) -> dict[str, str]:
        rt = get_user_runtime(request.app, user, settings, DashboardState)
        rt.dash.status = "PAUSED"
        return {"status": rt.dash.status}

    @app.post("/api/bot/stop")
    async def bot_stop(request: Request, user: CurrentUser) -> dict[str, str]:
        rt = get_user_runtime(request.app, user, settings, DashboardState)
        rt.risk.set_emergency_stop(True)
        rt.dash.status = "STOPPED"
        return {"status": rt.dash.status}

    @app.post("/api/bot/emergency-stop")
    async def bot_emergency(request: Request, user: CurrentUser) -> dict[str, str]:
        rt = get_user_runtime(request.app, user, settings, DashboardState)
        rt.risk.set_emergency_stop(True)
        rt.dash.status = "STOPPED"
        return {"status": "EMERGENCY", "bot": rt.dash.status}

    @app.post("/api/paper-trade/execute")
    async def paper_execute(
        request: Request,
        user: CurrentUser,
        body: PaperExecuteBody | None = None,
    ) -> dict[str, Any]:
        rt = get_user_runtime(request.app, user, settings, DashboardState)
        dash = rt.dash
        if dash.status != "ACTIVE":
            return {"ok": False, "message": "Bot not ACTIVE — no paper execution."}
        body = body or PaperExecuteBody()
        sym = body.symbol or dash.pair
        side = (body.side or "buy").lower()
        if side not in ("buy", "sell"):
            side = "buy"
        m = request.app.state.market.snapshot()
        px = float(m.prices.get(sym, 1.0))
        qty = float(body.qty or 120.0)
        conf = float(body.confidence_pct or max(dash.confidence_threshold, 70.0))
        reason_raw = (body.reason or "").strip() if body.reason else ""
        reason = reason_raw or "Paper execute (dashboard)"
        res = rt.paper.execute(
            symbol=sym,
            side=side,  # type: ignore[arg-type]
            qty=qty,
            price=px,
            confidence_pct=conf,
            risk=rt.risk,
            sl_pct=dash.sl_pct,
            tp_pct=dash.tp_pct,
            trail_pct=dash.trail_pct,
            risk_level=str(dash.risk_level),
            reason=reason,
        )
        if res.position:
            return {
                "ok": True,
                "message": res.message,
                "position": {
                    "id": res.position.id,
                    "symbol": res.position.symbol,
                    "side": res.position.side,
                    "entry": res.position.entry_price,
                    "trailing_sl": res.position.stop_price,
                    "stop_badge": res.position.stop_mode,
                },
            }
        return {"ok": False, "message": res.message}

    @app.post("/api/paper-trade/close-all")
    async def paper_close_all(
        request: Request,
        user: CurrentUser,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        rt = get_user_runtime(request.app, user, settings, DashboardState)
        m = request.app.state.market.snapshot()
        closed = rt.paper.close_all(m.prices, default_price=1.0)
        for c in closed:
            rt.risk.record_close_pnl_pct(c.pnl_pct)
            persist_closed_trade(db, user_id=user.id, trade=c, opened_at=None)
        return {"closed": len(closed), "trades": [c.__dict__ for c in closed]}

    @app.post("/api/paper-trade/close")
    async def paper_close_one(
        request: Request,
        user: CurrentUser,
        payload: ClosePositionBody,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        rt = get_user_runtime(request.app, user, settings, DashboardState)
        m = request.app.state.market.snapshot()
        paper = rt.paper
        pos = next((p for p in paper.open_positions if p.id == payload.position_id), None)
        if not pos:
            return {"ok": False, "message": "Position not found."}
        px = float(m.prices.get(pos.symbol, pos.entry_price))
        ct = paper.close_position(payload.position_id, px)
        if ct:
            rt.risk.record_close_pnl_pct(ct.pnl_pct)
            persist_closed_trade(db, user_id=user.id, trade=ct, opened_at=pos.opened_at)
            return {"ok": True, "trade": ct.__dict__}
        return {"ok": False, "message": "Close failed."}

    @app.post("/api/backtest/run")
    async def backtest_run(
        request: Request,
        user: CurrentUser,
        body: BacktestRequest,
    ) -> dict[str, Any]:
        result = _run_backtest_core(body, settings.binance_base_url)
        rt = get_user_runtime(request.app, user, settings, DashboardState)
        rt.dash.last_backtest = result
        return result

    @app.post("/api/backtest/compare")
    async def backtest_compare(body: BacktestCompareRequest) -> dict[str, Any]:
        if body.source == "synthetic":
            return compare_backtests_synthetic(
                configs=body.configs, days=body.days, objective=body.optimization_objective
            )
        return compare_backtests_binance(
            configs=body.configs,
            days=body.days,
            base_url=settings.binance_base_url,
            objective=body.optimization_objective,
        )

    @app.post("/api/backtest/apply-best-settings")
    async def backtest_apply(request: Request, user: CurrentUser) -> dict[str, Any]:
        rt = get_user_runtime(request.app, user, settings, DashboardState)
        dash = rt.dash
        if not dash.last_backtest:
            return {"ok": False, "message": "Run a backtest first."}
        rec = dash.last_backtest
        dash.sl_pct = float(rec.get("recommended_sl_pct", dash.sl_pct))
        dash.tp_pct = float(rec.get("recommended_tp_pct", dash.tp_pct))
        return {
            "ok": True,
            "sl_pct": dash.sl_pct,
            "tp_pct": dash.tp_pct,
            "message": "Applied recommended SL/TP from last backtest (paper).",
        }

    @app.post("/api/dashboard/preferences")
    async def dash_prefs(
        request: Request,
        user: CurrentUser,
        prefs: DashPrefsBody,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        rt = get_user_runtime(request.app, user, settings, DashboardState)
        d = rt.dash
        data = prefs.model_dump(exclude_unset=True)
        if "risk_level" in data and data["risk_level"] is not None:
            d.risk_level = max(1, min(100, int(data["risk_level"])))
        if "strategy" in data and data["strategy"]:
            d.strategy = str(data["strategy"])
        if "trading_mode" in data and data["trading_mode"]:
            d.trading_mode = str(data["trading_mode"])[:64]
        if "pair" in data and data["pair"]:
            d.pair = str(data["pair"])
        if "sl_pct" in data and data["sl_pct"] is not None:
            d.sl_pct = float(data["sl_pct"])
        if "tp_pct" in data and data["tp_pct"] is not None:
            d.tp_pct = float(data["tp_pct"])
        if "trail_pct" in data and data["trail_pct"] is not None:
            d.trail_pct = float(data["trail_pct"])
        if "confidence_threshold" in data and data["confidence_threshold"] is not None:
            d.confidence_threshold = float(data["confidence_threshold"])
            rt.risk.configure(min_signal_confidence_pct=d.confidence_threshold)
        if "max_open_trades" in data and data["max_open_trades"] is not None:
            d.max_open_trades = max(1, min(50, int(data["max_open_trades"])))
            rt.risk.configure(max_open_trades=d.max_open_trades)
        if "capital_usage_pct" in data and data["capital_usage_pct"] is not None:
            d.capital_usage_pct = max(5.0, min(100.0, float(data["capital_usage_pct"])))
        if "sound_on" in data and data["sound_on"] is not None:
            d.sound_on = bool(data["sound_on"])
        if "lang" in data and data["lang"] in ("en", "ar"):
            d.lang = str(data["lang"])
        if "speed" in data and data["speed"] is not None:
            d.speed = max(0.25, min(3.0, float(data["speed"])))
        if "compounding_enabled" in data and data["compounding_enabled"] is not None:
            d.compounding_enabled = bool(data["compounding_enabled"])
        if "max_daily_loss_pct" in data and data["max_daily_loss_pct"] is not None:
            d.max_daily_loss_pct = max(0.5, min(25.0, float(data["max_daily_loss_pct"])))
            rt.risk.configure(max_daily_loss_pct=d.max_daily_loss_pct)

        persist_dashboard_prefs(user, d)
        payload = build_portfolio_payload(
            db=db,
            user_id=user.id,
            dash=d,
            paper=rt.paper,
            risk=rt.risk,
            signal_history=rt.signal_history,
            last_signal_snapshot=rt.last_signal_snapshot,
            market=request.app.state.market,
        )
        _sync_portfolio_row(db, user, d, payload["portfolio_value_usd"])
        db.commit()
        return {"ok": True, "dashboard": payload}

    @app.post("/api/dashboard/save-strategy")
    async def save_strategy_current(
        request: Request,
        user: CurrentUser,
        body: StrategySaveBody,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        from app.db.models import Strategy as StrategyModel

        rt = get_user_runtime(request.app, user, settings, DashboardState)
        d = rt.dash
        row = StrategyModel(
            user_id=user.id,
            name=body.name.strip(),
            sl_pct=d.sl_pct,
            tp_pct=d.tp_pct,
            trail_pct=d.trail_pct,
            risk_level=d.risk_level,
            max_open_trades=d.max_open_trades,
            confidence_threshold=d.confidence_threshold,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return {"ok": True, "id": row.id, "name": row.name}

    return app


app = create_app()
