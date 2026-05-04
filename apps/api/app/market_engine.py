"""Realistic mock market microstructure for paper trading (not live venues)."""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field

from pydantic import BaseModel, Field


class WhalePulse(BaseModel):
    net_flow_usd: float
    large_wallet_moves: int
    narrative: str


class MarketSnapshot(BaseModel):
    as_of: str
    prices: dict[str, float] = Field(default_factory=dict)
    volume_24h_usd: float = 0.0
    volatility_annualized_pct: float = 0.0
    trend: str = "sideways"
    whale_activity: WhalePulse
    sentiment_score: float = 0.0


@dataclass
class _AssetState:
    price: float
    velocity: float = 0.0


class MarketEngine:
    """Geometric Brownian-style mock with regime switching."""

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)
        self._t0 = time.monotonic()
        self._assets: dict[str, _AssetState] = {
            "BTC": _AssetState(62_400.0),
            "ETH": _AssetState(3_420.0),
            "SOL": _AssetState(142.0),
        }

    def _clock(self) -> float:
        return time.monotonic() - self._t0

    def _tick_prices(self) -> dict[str, float]:
        dt = 0.35 + self._rng.random() * 0.9
        out: dict[str, float] = {}
        for sym, st in self._assets.items():
            base_vol = 0.0012 if sym == "BTC" else 0.0018
            shock = self._rng.gauss(0, 1) * base_vol * st.price
            drift = math.sin(self._clock() * 0.25 + hash(sym) % 7) * 0.00015 * st.price
            st.velocity = 0.82 * st.velocity + 0.18 * shock
            st.price = max(1.0, st.price + st.velocity + drift * dt)
            decimals = 2 if sym == "BTC" else (4 if sym == "ETH" else 3)
            out[sym] = round(st.price, decimals)
        return out

    def snapshot(self) -> MarketSnapshot:
        prices = self._tick_prices()
        t = self._clock()
        vol = abs(math.sin(t * 0.7)) * 42 + self._rng.uniform(18, 96)
        sentiment = max(
            -1.0,
            min(1.0, 0.55 * math.sin(t * 0.31) + self._rng.gauss(0, 0.22)),
        )
        trend = (
            "bullish"
            if sentiment > 0.22
            else ("bearish" if sentiment < -0.22 else "sideways")
        )
        base_vol = sum(prices.values()) * 42_000_000
        whale_net = self._rng.gauss(0, base_vol * 0.00002)
        moves = self._rng.randint(0, 18)
        if abs(whale_net) > base_vol * 0.000015:
            narrative = "Whale cohort rotation detected on synthetic tape."
        elif moves > 11:
            narrative = "Elevated large-wallet churn; liquidity pockets shifting."
        else:
            narrative = "Whale flow mixed; no dominant iceberg pattern."

        from datetime import datetime, timezone

        return MarketSnapshot(
            as_of=datetime.now(timezone.utc).isoformat(),
            prices=prices,
            volume_24h_usd=round(
                sum(prices[s] * (1200 + self._rng.random() * 900) for s in prices), 2
            ),
            volatility_annualized_pct=round(vol, 2),
            trend=trend,
            whale_activity=WhalePulse(
                net_flow_usd=round(whale_net, 2),
                large_wallet_moves=moves,
                narrative=narrative,
            ),
            sentiment_score=round(sentiment, 4),
        )
