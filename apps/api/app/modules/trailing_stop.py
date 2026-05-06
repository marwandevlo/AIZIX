"""Trailing stop helpers for paper positions (synthetic mid)."""

from __future__ import annotations

from typing import Literal

StopMode = Literal["OPEN", "TRAIL"]


def next_trail_price(
    *,
    side: str,
    entry: float,
    mark: float,
    trail_pct: float,
    current_trail: float | None,
) -> tuple[float, StopMode]:
    """Return (stop_price, OPEN if initial fixed stop else TRAIL)."""
    side_l = side.lower()
    trail_pct = max(0.1, min(trail_pct, 25.0))
    if side_l == "buy":
        base = entry * (1.0 - trail_pct / 100.0)
        if current_trail is None:
            return base, "OPEN"
        improved = max(current_trail, mark * (1.0 - trail_pct / 100.0))
        return improved, "TRAIL"
    base = entry * (1.0 + trail_pct / 100.0)
    if current_trail is None:
        return base, "OPEN"
    improved = min(current_trail, mark * (1.0 + trail_pct / 100.0))
    return improved, "TRAIL"
