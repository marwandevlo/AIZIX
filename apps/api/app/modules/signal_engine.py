"""Multi-pair signal aggregation built on the AI decision core."""

from __future__ import annotations

import asyncio
from typing import Any

from app.core.config import Settings
from app.modules.ai_engine import AIEngine
from app.modules.market_engine import MarketEngine, PAIRS
from app.modules.risk_manager import RiskManager


class SignalEngine:
    def __init__(
        self,
        *,
        market: MarketEngine,
        settings: Settings,
        risk: RiskManager | None = None,
        ai: AIEngine | None = None,
    ) -> None:
        self._market = market
        self._risk = risk
        self._ai = ai or AIEngine()
        self._latency_bounds = (
            settings.signal_latency_ms_min,
            settings.signal_latency_ms_max,
        )

    async def all_signals(self, *, bot_active: bool, risk: RiskManager | None = None) -> dict[str, Any]:
        # Deterministic pacing (latency bounds kept for future jitter toggles).
        await asyncio.sleep((self._latency_bounds[0] + self._latency_bounds[1]) / 2000.0)
        m = self._market.snapshot()
        rm = risk or self._risk
        if rm is None:
            raise RuntimeError("SignalEngine requires a RiskManager (inject per request).")
        risk_gate = rm.gate_action()
        risk_ok = risk_gate == "trade"
        rows: list[dict[str, Any]] = []
        for pair in PAIRS:
            d = self._ai.decide(
                pair=pair,
                snapshot=m,
                bot_active=bot_active,
                risk_gate_ok=risk_ok,
            )
            px = m.prices.get(pair, 1.0)
            pub = d.public_signal()
            rows.append(
                {
                    "pair": pair,
                    "signal": pub["signal"],
                    "confidence": pub["confidence"],
                    "risk": pub["risk"],
                    "reason": pub["reason"],
                    "action": d.action,
                    "confidence_pct": d.confidence_pct,
                    "calibrated_confidence_pct": d.calibrated_confidence_pct,
                    "risk_level": d.risk_level,
                    "risk_score": d.risk_score,
                    "stance": d.stance,
                    "trend_alignment": d.trend_alignment,
                    "trend_strength": d.trend_strength,
                    "momentum_score": d.momentum_score,
                    "volume_score": d.volume_score,
                    "volatility_pct": d.volatility_pct,
                    "components": d.components,
                    "price": px,
                    "risk_status": "ok" if risk_ok else "halt",
                    "flow_metrics": {
                        "volume_24h_usd": m.volume_24h_usd,
                        "volatility_annualized_pct": m.volatility_annualized_pct,
                    },
                }
            )
        return {
            "as_of": m.as_of,
            "market": {
                "trend": m.trend,
                "volatility_annualized_pct": m.volatility_annualized_pct,
                "sentiment_score": m.sentiment_score,
                "volume_24h_usd": m.volume_24h_usd,
            },
            "signals": rows,
        }
