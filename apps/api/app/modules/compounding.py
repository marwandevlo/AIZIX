from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WalletSplit:
    trading_usd: float
    safety_usd: float


def split_profit(
    profit_usd: float,
    *,
    trading_wallet_pct: float = 0.70,
    safety_wallet_pct: float = 0.30,
) -> WalletSplit:
    """
    Allocate paper profits between trading and safety wallets.
    Percentages should sum to 1.0; invalid sums fall back to 70/30.
    """
    if profit_usd <= 0:
        return WalletSplit(trading_usd=0.0, safety_usd=0.0)

    total_pct = trading_wallet_pct + safety_wallet_pct
    if abs(total_pct - 1.0) > 1e-6:
        trading_wallet_pct, safety_wallet_pct = 0.70, 0.30

    return WalletSplit(
        trading_usd=round(profit_usd * trading_wallet_pct, 2),
        safety_usd=round(profit_usd * safety_wallet_pct, 2),
    )
