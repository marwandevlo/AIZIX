"""Dual-wallet split: 70% trading / 30% safety when compounding is enabled."""

from __future__ import annotations


def wallet_balances(total_usd: float, compounding_enabled: bool) -> dict[str, float]:
    total_usd = max(0.0, float(total_usd))
    if not compounding_enabled:
        return {
            "trading_balance": round(total_usd, 2),
            "safety_balance": 0.0,
            "total": round(total_usd, 2),
        }
    return {
        "trading_balance": round(total_usd * 0.7, 2),
        "safety_balance": round(total_usd * 0.3, 2),
        "total": round(total_usd, 2),
    }


def allocate_paper_profit(
    profit_usd: float,
    *,
    compounding_enabled: bool,
) -> dict[str, float]:
    """Allocate a closed-trade profit into wallets (paper)."""
    if profit_usd <= 0 or not compounding_enabled:
        return {"trading_usd": 0.0, "safety_usd": 0.0}
    return {
        "trading_usd": round(profit_usd * 0.7, 2),
        "safety_usd": round(profit_usd * 0.3, 2),
    }
