from __future__ import annotations

import hashlib
import math
from datetime import datetime, timezone
from typing import Literal

from app.modules.risk_manager import RiskManager

Action = Literal["buy", "sell", "hold"]
Mood = Literal["bullish", "neutral", "cautious", "risk-off"]


def _seed(symbol: str, hour: int) -> float:
    digest = hashlib.sha256(f"{symbol}:{hour}".encode()).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def generate_etf_signal(symbol: str, risk: RiskManager) -> dict:
    """
    Lightweight synthetic ETF-style signal (paper only).
    Uses deterministic mock variation — not market data.
    """
    now = datetime.now(timezone.utc)
    hour = now.hour
    s = _seed(symbol, hour)

    momentum = math.sin((s * 12.566)) * 0.5 + 0.5
    vol = abs(math.cos(s * 9.1)) * 0.35

    if risk.gate_action() == "halt":
        action: Action = "hold"
        confidence = round(0.35 + vol * 0.1, 4)
        mood: Mood = "risk-off"
        reason = "Risk manager halted new exposure; stand down or reduce size."
    elif momentum > 0.62 and vol < 0.22:
        action = "buy"
        confidence = round(min(0.93, 0.55 + momentum * 0.25), 4)
        mood = "bullish"
        reason = "Synthetic basket momentum supportive; leverage ETF bias up (paper)."
    elif momentum < 0.38 or vol > 0.28:
        action = "sell"
        confidence = round(min(0.88, 0.5 + (1 - momentum) * 0.3), 4)
        mood = "cautious"
        reason = "Elevated synthetic volatility / mean reversion cue (paper)."
    else:
        action = "hold"
        confidence = round(0.45 + vol * 0.2, 4)
        mood = "neutral"
        reason = "No strong edge in mock regime; wait for clearer basket tilt."

    return {
        "symbol": symbol,
        "action": action,
        "confidence": confidence,
        "mood": mood,
        "reason": reason,
        "as_of": now.isoformat(),
    }


def signal_universe() -> list[str]:
    return ["BTC3L", "ETH3L", "SOL2L", "DEFI2L", "AI_IDX"]
