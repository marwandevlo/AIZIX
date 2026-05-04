"""ETF-style leveraged token mapping (simulation only — no exchange routing)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Sleeve = Literal["LONG", "SHORT", "NONE"]


@dataclass(frozen=True)
class ETFRecommendation:
    """Target synthetic leveraged pair for the current regime."""

    symbol: str | None
    sleeve: Sleeve
    rationale: str


def recommend(
    *,
    trend: str,
    sentiment_score: float,
    volatility_annualized_pct: float,
) -> ETFRecommendation:
    """
    Rules (paper):
    - Bullish tape → prefer long leveraged sleeve (BTC3L / ETH3L).
    - Bearish tape → prefer short leveraged sleeve (BTC3S / ETH3S).
    - Sideways or high volatility → no leveraged sleeve (NONE / stand aside).
    """
    high_vol = volatility_annualized_pct >= 58.0
    sideways = trend == "sideways"

    if sideways or high_vol:
        return ETFRecommendation(
            symbol=None,
            sleeve="NONE",
            rationale=(
                "Sideways or high-volatility regime: stand aside from leveraged "
                "3x sleeves; capital preservation first (paper)."
            ),
        )

    use_eth = abs(sentiment_score) < 0.55

    if trend == "bullish" or sentiment_score > 0.18:
        sym = "ETH3L/USDT" if use_eth else "BTC3L/USDT"
        return ETFRecommendation(
            symbol=sym,
            sleeve="LONG",
            rationale=(
                f"Bullish risk-on skew → prefer {sym} (synthetic 3x long beta sleeve)."
            ),
        )

    if trend == "bearish" or sentiment_score < -0.18:
        sym = "ETH3S/USDT" if use_eth else "BTC3S/USDT"
        return ETFRecommendation(
            symbol=sym,
            sleeve="SHORT",
            rationale=(
                f"Bearish risk-off skew → prefer {sym} (synthetic 3x inverse sleeve)."
            ),
        )

    return ETFRecommendation(
        symbol=None,
        sleeve="NONE",
        rationale="Neutral edge: no clear 3x sleeve tilt (paper).",
    )
