"""Deterministic, explainable signal core (rules + classical indicators, no black-box ML)."""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from typing import Any, Literal

from app.modules.market_engine import OHLCVBar, MarketSnapshot

SignalAction = Literal["BUY", "SELL", "HOLD"]
RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]
VolRegime = Literal["low", "normal", "high"]


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _ema_series(closes: list[float], span: int) -> list[float]:
    if not closes:
        return []
    k = 2.0 / (span + 1)
    out = [closes[0]]
    for i in range(1, len(closes)):
        out.append(closes[i] * k + out[-1] * (1.0 - k))
    return out


def _rsi_wilder(closes: list[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, len(closes)):
        ch = closes[i] - closes[i - 1]
        gains.append(max(ch, 0.0))
        losses.append(max(-ch, 0.0))
    avg_gain = sum(gains[0:period]) / period
    avg_loss = sum(losses[0:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss < 1e-12:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _atr_window(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> tuple[float, float, float]:
    """ATR-like SMA(True Range); returns (atr_last, atr_median_slice, median_close)."""
    if len(closes) < 2:
        return 0.0, 1e-9, closes[-1] if closes else 1.0
    trs: list[float] = []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        trs.append(tr)
    window = trs[-period:] if len(trs) >= period else trs
    atr_last = window[-1]
    sorted_mid = sorted(window)
    mid = len(sorted_mid) // 2
    atr_med = sorted_mid[mid] if sorted_mid else atr_last
    sorted_c = sorted(closes[-period:])
    mc = sorted_c[len(sorted_c) // 2] if sorted_c else closes[-1]
    return atr_last, max(atr_med, 1e-12), max(mc, 1e-12)


def _vol_regime(atr_last: float, atr_med: float) -> VolRegime:
    ratio = atr_last / max(atr_med, 1e-12)
    if ratio >= 1.28:
        return "high"
    if ratio <= 0.82:
        return "low"
    return "normal"


def _ema_cross_score(closes: list[float], fast: int = 12, slow: int = 26) -> float:
    if len(closes) < slow + 3:
        return 0.0
    ef = _ema_series(closes, fast)
    es = _ema_series(closes, slow)
    diff_now = ef[-1] - es[-1]
    diff_prev = ef[-4] - es[-4] if len(ef) >= 4 else diff_now
    sep_vel = (diff_now - diff_prev) / max(closes[-1], 1e-9)
    norm = diff_now / max(closes[-1], 1e-9)
    z = norm * 55.0 + sep_vel * 120.0
    return _clamp(math.tanh(z), -1.0, 1.0)


def _structure_score(highs: list[float], lows: list[float], lookback: int = 14) -> float:
    if len(highs) < lookback + 2:
        return 0.0
    hh = ll = 0
    for i in range(-lookback, -1):
        if highs[i] > highs[i - 1]:
            hh += 1
        if lows[i] < lows[i - 1]:
            ll += 1
    denom = max(lookback - 1, 1)
    return _clamp((hh - ll) / denom, -1.0, 1.0)


def _breakout_score(closes: list[float], highs: list[float], lows: list[float], lookback: int = 20) -> float:
    if len(closes) < lookback + 2:
        return 0.0
    window_h = max(highs[-lookback - 1 : -1])
    window_l = min(lows[-lookback - 1 : -1])
    c = closes[-1]
    if c > window_h:
        return _clamp(((c - window_h) / max(window_h, 1e-9)) * 80.0, 0.0, 1.0)
    if c < window_l:
        return -_clamp(((window_l - c) / max(window_l, 1e-9)) * 80.0, 0.0, 1.0)
    return 0.0


def _volume_features(volumes: list[float], period: int = 20) -> tuple[float, bool, float]:
    if len(volumes) < period + 2:
        return 0.0, False, 1.0
    sma = sum(volumes[-period - 1 : -1]) / period
    last = volumes[-1]
    ratio = last / max(sma, 1e-9)
    spike = ratio >= 1.45
    z = _clamp((ratio - 1.0) * 2.2, -1.0, 1.0)
    return z, spike, ratio


def _macro_alignment(trend: str, sentiment: float, sleeve_bias: float) -> float:
    if trend == "bullish":
        base = 0.62
    elif trend == "bearish":
        base = -0.62
    else:
        base = sentiment * 0.55
    return _clamp(base * sleeve_bias + sentiment * 0.2 * sleeve_bias, -1.0, 1.0)


def _series_from_bars(
    pair: str, snapshot: MarketSnapshot
) -> tuple[list[float], list[float], list[float], list[float], list[float]]:
    bars = snapshot.bars_by_pair.get(pair)
    px = float(snapshot.prices.get(pair, 1.0))
    if not bars or len(bars) < 10:
        bars = tuple(OHLCVBar(px, px, px, px, 150_000.0 + 1000.0 * i) for i in range(45))
    opens = [b.open for b in bars]
    highs = [b.high for b in bars]
    lows = [b.low for b in bars]
    closes = [b.close for b in bars]
    vols = [b.volume for b in bars]
    return opens, highs, lows, closes, vols


def _stance(vol_ann: float, regime: VolRegime, risk_score: float, calibrated_conf: float) -> str:
    if risk_score >= 72:
        return "Elevated risk - reduce pace"
    if regime == "high" or vol_ann >= 62:
        return "Volatile tape - selective entries"
    if calibrated_conf >= 78:
        return "Strong agreement across indicators"
    if regime == "low":
        return "Quiet volatility - respect stops"
    return "Neutral - maintain discipline"


@dataclass(frozen=True)
class AIDecision:
    action: SignalAction
    confidence_pct: float
    calibrated_confidence_pct: float
    risk_level: RiskLevel
    risk_score: float
    reason: str
    trend_alignment: float
    trend_strength: float
    momentum_score: float
    volume_score: float
    volatility_pct: float
    stance: str
    components: dict[str, Any]

    def public_signal(self) -> dict[str, Any]:
        return {
            "signal": self.action,
            "confidence": round(float(self.calibrated_confidence_pct), 2),
            "risk": self.risk_level,
            "reason": self.reason,
        }


class AIEngine:
    """Rule-based analyst with explicit indicators and rolling calibration."""

    def __init__(self, calibration_window: int = 96) -> None:
        self._calibration_window = max(8, calibration_window)
        self._outcomes: deque[bool] = deque(maxlen=self._calibration_window)

    def record_calibration_outcome(self, *, directional_correct: bool) -> None:
        """Feed realized directional results (e.g., after paper exits) to tighten confidence."""
        self._outcomes.append(bool(directional_correct))

    def _hit_rate(self) -> float:
        if not self._outcomes:
            return 0.5
        return sum(1 for x in self._outcomes if x) / len(self._outcomes)

    def decide(
        self,
        *,
        pair: str,
        snapshot: MarketSnapshot,
        bot_active: bool,
        risk_gate_ok: bool,
    ) -> AIDecision:
        vol_ann = float(snapshot.volatility_annualized_pct)

        if not bot_active:
            return AIDecision(
                action="HOLD",
                confidence_pct=0.0,
                calibrated_confidence_pct=0.0,
                risk_level="LOW",
                risk_score=12.0,
                reason="Automation halted - signals suppressed.",
                trend_alignment=0.0,
                trend_strength=0.0,
                momentum_score=0.0,
                volume_score=0.0,
                volatility_pct=vol_ann,
                stance="Paused",
                components={},
            )

        opens, highs, lows, closes, vols = _series_from_bars(pair, snapshot)
        base = pair.split("/")[0].upper()
        is_long_sleeve = "3L" in base or (base.endswith("L") and "3S" not in base)
        sleeve_bias = 1.0 if is_long_sleeve else -1.0

        ema_cross = _ema_cross_score(closes)
        structure = _structure_score(highs, lows)
        rsi = _rsi_wilder(closes, 14)
        rsi_norm = _clamp((rsi - 50.0) / 50.0, -1.0, 1.0)
        breakout = _breakout_score(closes, highs, lows)
        vol_z, vol_spike, vol_ratio = _volume_features(vols)
        last_bar_bull = closes[-1] >= opens[-1]
        vol_confirm = vol_z * (1.0 if last_bar_bull else -1.0)
        macro = _macro_alignment(snapshot.trend, snapshot.sentiment_score, sleeve_bias)

        sleeve_trend = _clamp(
            0.55 * ema_cross * sleeve_bias
            + 0.45 * structure * sleeve_bias
            + 0.35 * breakout,
            -1.0,
            1.0,
        )

        S = _clamp(
            0.24 * ema_cross * sleeve_bias
            + 0.17 * structure * sleeve_bias
            + 0.18 * rsi_norm * sleeve_bias
            + 0.14 * breakout
            + 0.11 * vol_confirm
            + 0.16 * macro,
            -1.0,
            1.0,
        )

        atr_last, atr_med, med_c = _atr_window(highs, lows, closes, 14)
        atr_pct = 100.0 * atr_last / max(med_c, 1e-9)
        regime = _vol_regime(atr_last, atr_med)

        trend_alignment = sleeve_trend
        trend_strength = _clamp(
            0.45 * abs(ema_cross) + 0.35 * abs(structure) + 0.2 * abs(breakout),
            0.0,
            1.0,
        )
        momentum_score = _clamp(0.6 * rsi_norm + 0.4 * breakout, -1.0, 1.0)
        volume_score = _clamp(vol_z + (0.25 if vol_spike else 0.0), -1.0, 1.0)

        risk_score = _clamp(
            34.0
            + min(38.0, atr_pct * 6.8)
            + min(18.0, max(0.0, vol_ann - 40.0) * 0.28)
            + (10.0 if regime == "high" else (-6.0 if regime == "low" else 0.0))
            - 16.0 * trend_strength
            + (48.0 if not risk_gate_ok else 0.0),
            0.0,
            100.0,
        )
        if vol_spike and abs(vol_confirm) > 0.35:
            risk_score = min(100.0, risk_score + 5.0)
        if abs(snapshot.whale_activity.net_flow_usd) > 2e6:
            risk_score = min(100.0, risk_score + 5.0)

        risk_level: RiskLevel = (
            "HIGH" if risk_score >= 68 else ("MEDIUM" if risk_score >= 44 else "LOW")
        )

        enter_long = S > 0.19
        enter_short = S < -0.19

        action: SignalAction = "HOLD"
        if enter_long:
            action = "BUY" if is_long_sleeve else "SELL"
        elif enter_short:
            action = "SELL" if is_long_sleeve else "BUY"

        conflict = max(0.0, -(ema_cross * sleeve_bias) * rsi_norm)
        conflict_penalty = 1.0 - 0.14 * conflict

        mag = abs(S)
        raw_conf = (44.0 + 52.0 * _clamp(mag * 1.25, 0.0, 1.0)) * conflict_penalty
        raw_conf *= 1.0 - min(0.22, max(0.0, (vol_ann - 42.0) / 240.0))
        if regime == "high":
            raw_conf *= 0.9
        if snapshot.trend == "sideways" and abs(snapshot.sentiment_score) < 0.08:
            raw_conf = min(raw_conf, 61.0)
            if mag < 0.26:
                action = "HOLD"

        if regime == "high" and risk_level == "HIGH" and mag < 0.35:
            action = "HOLD"

        if vol_ann > 72:
            action = "HOLD"
            raw_conf = min(raw_conf, 52.0)

        if not risk_gate_ok and action != "HOLD":
            action = "HOLD"
            raw_conf = min(raw_conf, 50.0)

        hit = self._hit_rate()
        cal_mult = 0.78 + 0.44 * hit
        calibrated = _clamp(raw_conf * cal_mult, 0.0, 94.0)

        reason_parts: list[str] = []
        if action == "HOLD":
            reason_parts.append("No trade: composite below threshold, mixed indicators, or risk/vol filter.")
        elif action == "BUY":
            if is_long_sleeve:
                reason_parts.append("Long sleeve: EMA/structure/momentum align bullish.")
            else:
                reason_parts.append("Inverse sleeve: metrics align for bear-hedge add.")
        elif action == "SELL":
            if is_long_sleeve:
                reason_parts.append("Long sleeve: metrics argue trim or de-risk.")
            else:
                reason_parts.append("Inverse sleeve: metrics argue cover / reduce hedge.")

        if vol_spike:
            reason_parts.append("Volume spike - confirm breakout vs exhaustion.")
        if regime == "high":
            reason_parts.append("ATR regime high - wider noise band.")
        elif regime == "low":
            reason_parts.append("ATR regime low - tighter ranges.")

        rsi_tag = "RSI stretched high" if rsi >= 68 else ("RSI stretched low" if rsi <= 32 else "RSI neutral band")
        reason_parts.append(rsi_tag + ".")

        reason = " ".join(reason_parts).strip()

        components: dict[str, Any] = {
            "ema_cross_raw": round(ema_cross, 4),
            "structure": round(structure, 4),
            "rsi": round(rsi, 2),
            "rsi_norm": round(rsi_norm, 4),
            "breakout": round(breakout, 4),
            "volume_ratio": round(vol_ratio, 3),
            "volume_spike": vol_spike,
            "atr_last": round(atr_last, 8),
            "atr_pct_of_price": round(atr_pct, 4),
            "atr_ratio_vs_median_tr": round(atr_last / atr_med, 4),
            "volatility_regime": regime,
            "composite_S": round(S, 4),
            "calibration_hit_rate": round(hit, 4),
            "calibration_samples": len(self._outcomes),
        }

        stance = _stance(vol_ann, regime, risk_score, calibrated)

        return AIDecision(
            action=action,
            confidence_pct=round(float(raw_conf), 2),
            calibrated_confidence_pct=round(float(calibrated), 2),
            risk_level=risk_level,
            risk_score=round(float(risk_score), 2),
            reason=reason,
            trend_alignment=round(float(trend_alignment), 4),
            trend_strength=round(float(trend_strength), 4),
            momentum_score=round(float(momentum_score), 4),
            volume_score=round(float(volume_score), 4),
            volatility_pct=round(float(vol_ann), 2),
            stance=stance,
            components=components,
        )
