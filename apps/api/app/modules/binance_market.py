"""Backward-compatible imports — Binance logic lives in ``market_engine``."""

from __future__ import annotations

from app.modules.market_engine import (
    MarketEngine as BinanceMarketEngine,
    SyntheticMarketEngine,
    underlying_symbol_for_pair,
)

__all__ = ["BinanceMarketEngine", "SyntheticMarketEngine", "underlying_symbol_for_pair"]
