"""AI-style signal generation on top of mock market + ETF sleeves + risk overlay."""

from __future__ import annotations

import asyncio
import random
from typing import Any, Literal

from app.config import Settings
from app.etf_strategy import recommend
from app.market_engine import MarketEngine, MarketSnapshot
from app.risk_manager import RiskManager

SignalAction = Literal["BUY", "SELL", "HOLD"]
BotStatus = Literal["ACTIVE", "PAUSED", "STOPPED"]


class SignalEngine:
    def __init__(
        self,
        *,
        market: MarketEngine,
        risk: RiskManager,
        settings: Settings,
    ) -> None:
        self._market = market
        self._risk = risk
        self._rng = random.Random()
        self._latency_bounds = (
            settings.signal_latency_ms_min,
            settings.signal_latency_ms_max,
        )

    def _mood_for(
        self,
        *,
        whale_alert: bool,
        cautious: bool,
        trend: str,
    ) -> str:
        if whale_alert:
            return "Whale Alert 🐋"
        if cautious:
            return "Cautious ⚠️"
        if trend == "bullish":
            return "Bullish 🐂"
        if trend == "bearish":
            return "Bearish 🐻"
        return "Cautious ⚠️"

    async def generate(
        self,
        *,
        bot_status: BotStatus,
    ) -> dict[str, Any]:
        await asyncio.sleep(
            self._rng.uniform(
                self._latency_bounds[0] / 1000,
                self._latency_bounds[1] / 1000,
            )
        )

        m: MarketSnapshot = self._market.snapshot()
        etf = recommend(
            trend=m.trend,
            sentiment_score=m.sentiment_score,
            volatility_annualized_pct=m.volatility_annualized_pct,
        )

        whale_alert = abs(m.whale_activity.net_flow_usd) > 1.25e6 or m.whale_activity.large_wallet_moves >= 14
        cautious = m.trend == "sideways" or m.volatility_annualized_pct >= 58.0

        raw_action: SignalAction = "HOLD"
        reason_parts: list[str] = []

        if cautious or etf.sleeve == "NONE":
            raw_action = "HOLD"
            reason_parts.append(etf.rationale)
        elif etf.sleeve == "LONG" and etf.symbol:
            raw_action = "BUY"
            reason_parts.append(etf.rationale)
        elif etf.sleeve == "SHORT" and etf.symbol:
            raw_action = "SELL"
            reason_parts.append(etf.rationale)
        else:
            raw_action = "HOLD"
            reason_parts.append("No actionable sleeve on synthetic tape.")

        base_conf = 52.0 + abs(m.sentiment_score) * 34.0
        if whale_alert:
            base_conf += 6.0
        if cautious:
            base_conf -= 10.0
        confidence_pct = float(round(min(96.0, max(41.0, base_conf + self._rng.uniform(-5, 7))), 1))

        risk_status = "ok"
        if bot_status != "ACTIVE":
            raw_action = "HOLD"
            risk_status = "bot_not_active"
            reason_parts.append("Bot is not ACTIVE; signals are observational only.")
        elif confidence_pct < self._risk.min_signal_confidence_pct:
            raw_action = "HOLD"
            risk_status = "low_confidence"
            reason_parts.append(
                f"Confidence {confidence_pct:.1f}% below required {self._risk.min_signal_confidence_pct:.0f}%."
            )
        elif cautious and risk_status == "ok":
            risk_status = "volatility_watch"

        if self._risk.gate_action() == "halt":
            raw_action = "HOLD"
            risk_status = "risk_halt"
            reason_parts.append("Risk halt: daily loss budget or kill-switch engaged.")

        if raw_action == "HOLD":
            if risk_status in ("low_confidence", "risk_halt", "bot_not_active"):
                mood = "Cautious ⚠️"
            elif whale_alert:
                mood = "Whale Alert 🐋"
            elif cautious:
                mood = "Cautious ⚠️"
            elif m.trend == "bearish":
                mood = "Bearish 🐻"
            elif m.trend == "bullish":
                mood = "Bullish 🐂"
            else:
                mood = "Cautious ⚠️"
            display_symbol = "—"
        else:
            mood = self._mood_for(
                whale_alert=whale_alert,
                cautious=False,
                trend=m.trend,
            )
            display_symbol = etf.symbol or (
                "BTC3L/USDT" if raw_action == "BUY" else "BTC3S/USDT"
            )

        reason = " ".join(reason_parts).strip()

        latency_ms = round(
            self._rng.uniform(float(self._latency_bounds[0]), float(self._latency_bounds[1])),
            1,
        )

        return {
            "action": raw_action,
            "confidence_pct": confidence_pct,
            "market_mood": mood,
            "reason": reason or "Synthetic desk evaluation complete.",
            "etf_bias": etf.rationale,
            "etf_symbol": etf.symbol or "—",
            "symbol": display_symbol,
            "risk_status": risk_status,
            "whale_activity": m.whale_activity.model_dump(),
            "prices": m.prices,
            "latency_ms": latency_ms,
            "market": m.model_dump(),
        }
