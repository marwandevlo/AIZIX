"""Market data: Binance Spot **public read-only** endpoints (24h ticker + klines), with optional synthetic fallback."""

from __future__ import annotations

import logging
import math
import random
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)

PAIRS: tuple[str, ...] = (
    "BTC3L/USDT",
    "BTC3S/USDT",
    "ETH3L/USDT",
    "ETH3S/USDT",
    "SOL3L/USDT",
    "SOL3S/USDT",
)

_BINANCE_SYMBOLS: tuple[str, ...] = ("BTCUSDT", "ETHUSDT", "SOLUSDT")

# Dashboard pair → (Binance symbol, sleeve sign for displayed change %)
_PAIR_UNDERLYING: dict[str, tuple[str, float]] = {
    "BTC3L/USDT": ("BTCUSDT", 1.0),
    "BTC3S/USDT": ("BTCUSDT", -1.0),
    "ETH3L/USDT": ("ETHUSDT", 1.0),
    "ETH3S/USDT": ("ETHUSDT", -1.0),
    "SOL3L/USDT": ("SOLUSDT", 1.0),
    "SOL3S/USDT": ("SOLUSDT", -1.0),
}

# Scale spot → legacy UI magnitudes for leveraged ETF-style labels
_DISPLAY_SCALE: dict[str, float] = {
    "BTC3L/USDT": 22.4 / 95_000.0,
    "BTC3S/USDT": 18.2 / 95_000.0,
    "ETH3L/USDT": 14.6 / 3_500.0,
    "ETH3S/USDT": 11.3 / 3_500.0,
    "SOL3L/USDT": 9.8 / 180.0,
    "SOL3S/USDT": 8.4 / 180.0,
}


def underlying_symbol_for_pair(pair: str) -> str:
    return _PAIR_UNDERLYING[pair][0]


@dataclass
class WhalePulse:
    net_flow_usd: float
    large_wallet_moves: int
    narrative: str


@dataclass(frozen=True)
class OHLCVBar:
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class MarketSnapshot:
    as_of: str
    prices: dict[str, float] = field(default_factory=dict)
    volume_24h_usd: float = 0.0
    volatility_annualized_pct: float = 0.0
    trend: str = "sideways"
    whale_activity: WhalePulse = field(
        default_factory=lambda: WhalePulse(0.0, 0, "")
    )
    sentiment_score: float = 0.0
    """Binance 24h priceChangePercent per dashboard pair (× sleeve sign for 3S)."""
    momentum_pct_by_pair: dict[str, float] = field(default_factory=dict)
    bars_by_pair: dict[str, tuple[OHLCVBar, ...]] = field(default_factory=dict)


@dataclass
class _PairState:
    price: float
    velocity: float = 0.0


class SyntheticMarketEngine:
    """Offline / fallback simulated tape (no external API)."""

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)
        self._t0 = time.monotonic()
        self._prev_prices: dict[str, float] = {}
        self._bar_seq = 0
        base = {
            "BTC3L/USDT": 22.4,
            "BTC3S/USDT": 18.2,
            "ETH3L/USDT": 14.6,
            "ETH3S/USDT": 11.3,
            "SOL3L/USDT": 9.8,
            "SOL3S/USDT": 8.4,
        }
        self._pairs: dict[str, _PairState] = {
            k: _PairState(price=v) for k, v in base.items()
        }
        self._hist: dict[str, deque[OHLCVBar]] = {p: deque(maxlen=150) for p in PAIRS}
        self._seed_history()

    def _seed_history(self) -> None:
        for sym, st in self._pairs.items():
            px = st.price
            for i in range(48):
                w = 0.0011 * math.sin(i * 0.36 + (hash(sym) % 13))
                o = px
                c = max(0.5, px * (1.0 + w))
                tr = 0.0007 * px * (1.0 + abs(math.sin(i * 0.81)))
                h = max(o, c) + tr
                l = min(o, c) - tr
                vol = 220_000.0 * (1.0 + 0.04 * (i % 9))
                self._hist[sym].append(
                    OHLCVBar(
                        open=o,
                        high=max(h, o, c),
                        low=min(l, o, c),
                        close=c,
                        volume=max(1.0, vol),
                    )
                )
                px = c
            st.price = px

    def _clock(self) -> float:
        return time.monotonic() - self._t0

    def _append_bar(self, sym: str, o: float, h: float, l: float, c: float, vol: float) -> None:
        self._hist[sym].append(
            OHLCVBar(
                open=o,
                high=max(h, o, c),
                low=min(l, o, c),
                close=c,
                volume=max(1.0, vol),
            )
        )

    def _tick_prices(self) -> dict[str, float]:
        dt = 0.25 + self._rng.random() * 0.55
        out: dict[str, float] = {}
        for sym, st in self._pairs.items():
            base_vol = 0.002 + self._rng.random() * 0.0015
            shock = self._rng.gauss(0, 1) * base_vol * st.price
            drift = math.sin(self._clock() * 0.22 + hash(sym) % 11) * 0.0002 * st.price
            st.velocity = 0.85 * st.velocity + 0.15 * shock
            st.price = max(0.5, st.price + st.velocity + drift * dt)
            out[sym] = round(st.price, 4 if "SOL" in sym else 3)
        return out

    def snapshot(self) -> MarketSnapshot:
        prices = self._tick_prices()
        momentum_pct: dict[str, float] = {}
        for sym, px in prices.items():
            prev = self._prev_prices.get(sym)
            if prev and prev > 0:
                momentum_pct[sym] = round(100.0 * (px - prev) / prev, 4)
            else:
                momentum_pct[sym] = 0.0
        self._prev_prices = dict(prices)

        bars_map: dict[str, tuple[OHLCVBar, ...]] = {}
        for sym in PAIRS:
            c = prices[sym]
            prev_close = self._hist[sym][-1].close if self._hist[sym] else c
            o = prev_close
            vel = abs(self._pairs[sym].velocity)
            body = abs(c - o) / max(o, 1e-9)
            wick = 0.0004 + min(0.02, vel / max(c, 1e-9))
            h = max(o, c) * (1.0 + wick + 0.35 * body)
            l = min(o, c) * (1.0 - wick - 0.35 * body)
            prev_v = self._hist[sym][-1].volume if self._hist[sym] else 200_000.0
            self._bar_seq += 1
            vfac = 1.0 + 0.012 * math.sin(self._bar_seq * 0.13 + hash(sym) % 11)
            self._append_bar(sym, o, h, l, c, prev_v * vfac)
            bars_map[sym] = tuple(self._hist[sym])

        t = self._clock()
        vol = abs(math.sin(t * 0.65)) * 38 + self._rng.uniform(22, 72)
        sentiment = max(
            -1.0,
            min(1.0, 0.5 * math.sin(t * 0.28) + self._rng.gauss(0, 0.2)),
        )
        trend = (
            "bullish"
            if sentiment > 0.18
            else ("bearish" if sentiment < -0.18 else "sideways")
        )
        notion = sum(prices.values()) * 120_000
        whale_net = self._rng.gauss(0, notion * 0.00004)
        moves = self._rng.randint(0, 22)
        if abs(whale_net) > notion * 0.00003 or moves >= 15:
            narrative = "Synthetic tape: large sleeve rotation on mock venue."
        elif moves >= 10:
            narrative = "Elevated wallet churn on paper index."
        else:
            narrative = "Quiet flow — desk watching correlations."
        return MarketSnapshot(
            as_of=datetime.now(timezone.utc).isoformat(),
            prices=prices,
            volume_24h_usd=round(notion * self._rng.uniform(0.8, 1.4), 2),
            volatility_annualized_pct=round(vol, 2),
            trend=trend,
            whale_activity=WhalePulse(
                net_flow_usd=round(whale_net, 2),
                large_wallet_moves=moves,
                narrative=narrative,
            ),
            sentiment_score=round(sentiment, 4),
            momentum_pct_by_pair=momentum_pct,
            bars_by_pair=bars_map,
        )


class MarketEngine:
    """
    Live Binance Spot **public** data only:
    - ``GET /api/v3/ticker/24hr`` → last price, quote volume (USDT), 24h change %
    - ``GET /api/v3/klines`` → OHLCV history for the AI stack
    """

    def __init__(
        self,
        *,
        base_url: str = "https://api.binance.com",
        timeout: float = 12.0,
        fallback_on_error: bool = True,
    ) -> None:
        self._client = httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout)
        self._fallback_on_error = fallback_on_error
        self._fallback = SyntheticMarketEngine() if fallback_on_error else None
        self._prev_flow_anchor: dict[str, float] = {}

    def _fetch_ticker_24h(self, symbol: str) -> dict[str, Any]:
        r = self._client.get("/api/v3/ticker/24hr", params={"symbol": symbol})
        r.raise_for_status()
        return r.json()

    def _fetch_klines(self, symbol: str, *, limit: int = 120) -> list[list[Any]]:
        r = self._client.get(
            "/api/v3/klines",
            params={"symbol": symbol, "interval": "1h", "limit": limit},
        )
        r.raise_for_status()
        return r.json()

    def _bars_for_pair(self, pair: str, raw: list[list[Any]]) -> tuple[OHLCVBar, ...]:
        scale = _DISPLAY_SCALE.get(pair, 0.0001)
        out: list[OHLCVBar] = []
        for k in raw:
            o = float(k[1]) * scale
            hi = float(k[2]) * scale
            lo = float(k[3]) * scale
            c = float(k[4]) * scale
            qv = float(k[7])
            out.append(
                OHLCVBar(
                    open=o,
                    high=max(hi, o, c),
                    low=min(lo, o, c),
                    close=c,
                    volume=max(1.0, qv),
                )
            )
        return tuple(out)

    def _live_snapshot(self) -> MarketSnapshot:
        tickers: dict[str, dict[str, Any]] = {}
        klines_by_symbol: dict[str, list[list[Any]]] = {}
        for sym in _BINANCE_SYMBOLS:
            tickers[sym] = self._fetch_ticker_24h(sym)
            klines_by_symbol[sym] = self._fetch_klines(sym, limit=120)

        bars_by_pair: dict[str, tuple[OHLCVBar, ...]] = {}
        for pair, (bsym, _) in _PAIR_UNDERLYING.items():
            bars_by_pair[pair] = self._bars_for_pair(pair, klines_by_symbol[bsym])

        prices: dict[str, float] = {}
        momentum_pct: dict[str, float] = {}
        sleeve_changes: list[float] = []
        vol_candidates: list[float] = []

        total_quote_volume_usd = sum(
            float(tickers[s].get("quoteVolume", 0.0)) for s in _BINANCE_SYMBOLS
        )

        for pair, (bsym, sleeve) in _PAIR_UNDERLYING.items():
            t = tickers[bsym]
            last = float(t["lastPrice"])
            scale = _DISPLAY_SCALE.get(pair, 0.0001)
            px = round(last * scale, 4 if "SOL" in pair else 3)
            prices[pair] = px

            chg_pct = float(t["priceChangePercent"])
            momentum_pct[pair] = round(chg_pct * sleeve, 4)
            sleeve_changes.append(chg_pct * sleeve)

            hi = float(t["highPrice"])
            lo = float(t["lowPrice"])
            if last > 0:
                band_pct = (hi - lo) / last * 100
                vol_candidates.append(min(120.0, band_pct * math.sqrt(365)))

        avg_chg = sum(sleeve_changes) / max(len(sleeve_changes), 1)
        if avg_chg > 0.35:
            trend = "bullish"
        elif avg_chg < -0.35:
            trend = "bearish"
        else:
            trend = "sideways"

        sentiment = max(-1.0, min(1.0, avg_chg / 4.0))
        vol_ann = sum(vol_candidates) / max(len(vol_candidates), 1) if vol_candidates else 40.0

        prev_sum = sum(self._prev_flow_anchor.get(p, prices[p]) for p in prices)
        cur_sum = sum(prices.values())
        whale_net = (cur_sum - prev_sum) * total_quote_volume_usd * 1.0e-5
        self._prev_flow_anchor = dict(prices)

        moves = int(min(22, max(0, abs(avg_chg) * 3 + vol_ann * 0.08)))
        if abs(whale_net) > total_quote_volume_usd * 1.5e-6:
            narrative = "Binance 24h tape: elevated quoted flow across majors."
        elif moves >= 12:
            narrative = "24h range expansion on Binance spot benchmarks."
        else:
            narrative = "Binance public feed — relative volume within normal bands."

        return MarketSnapshot(
            as_of=datetime.now(timezone.utc).isoformat(),
            prices=prices,
            volume_24h_usd=round(total_quote_volume_usd, 2),
            volatility_annualized_pct=round(vol_ann, 2),
            trend=trend,
            whale_activity=WhalePulse(
                net_flow_usd=round(whale_net, 2),
                large_wallet_moves=moves,
                narrative=narrative,
            ),
            sentiment_score=round(sentiment, 4),
            momentum_pct_by_pair=momentum_pct,
            bars_by_pair=bars_by_pair,
        )

    def snapshot(self) -> MarketSnapshot:
        try:
            return self._live_snapshot()
        except (httpx.HTTPError, KeyError, ValueError, TypeError) as e:
            if self._fallback is None:
                raise
            logger.warning("Binance market unavailable (%s) — using synthetic fallback.", e)
            return self._fallback.snapshot()


__all__ = [
    "PAIRS",
    "OHLCVBar",
    "MarketSnapshot",
    "WhalePulse",
    "MarketEngine",
    "SyntheticMarketEngine",
    "underlying_symbol_for_pair",
]
