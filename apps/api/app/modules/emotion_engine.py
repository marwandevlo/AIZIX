"""Synthetic desk mood labels for the dashboard (not sentiment analysis)."""

from __future__ import annotations

from typing import Literal

Mood = Literal["Bullish 🐂", "Cautious ⚠️", "Whale Alert 🐋", "Panic 🚨", "Confident 😈"]


def mood_from_context(
    *,
    trend: str,
    volatility_pct: float,
    whale_alert: bool,
    confidence: float,
    panic_drawdown_pct: float,
) -> Mood:
    if panic_drawdown_pct >= 8.0:
        return "Panic 🚨"
    if whale_alert:
        return "Whale Alert 🐋"
    if confidence >= 82 and trend == "bullish":
        return "Confident 😈"
    if trend == "bullish" and volatility_pct < 55:
        return "Bullish 🐂"
    if volatility_pct >= 62 or trend == "sideways":
        return "Cautious ⚠️"
    if trend == "bearish":
        return "Cautious ⚠️"
    return "Bullish 🐂"
