from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

Side = Literal["buy", "sell"]


@dataclass
class PaperOrder:
    id: str
    symbol: str
    side: Side
    qty: float
    price: float
    status: Literal["open", "filled", "cancelled"]
    created_at: str


class PaperTradingBook:
    """In-memory paper book — swap for Supabase persistence later."""

    def __init__(self) -> None:
        self._orders: dict[str, PaperOrder] = {}
        self._seq: list[str] = []

    def place_market(
        self, symbol: str, side: Side, qty: float, price: float
    ) -> PaperOrder:
        oid = str(uuid.uuid4())
        order = PaperOrder(
            id=oid,
            symbol=symbol,
            side=side,
            qty=qty,
            price=price,
            status="filled",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._orders[oid] = order
        self._seq.append(oid)
        return order

    def recent(self, limit: int = 20) -> list[dict]:
        ids = list(reversed(self._seq))[:limit]
        return [
            {
                "id": self._orders[i].id,
                "symbol": self._orders[i].symbol,
                "side": self._orders[i].side,
                "qty": self._orders[i].qty,
                "price": self._orders[i].price,
                "status": self._orders[i].status,
                "created_at": self._orders[i].created_at,
            }
            for i in ids
        ]


paper_book = PaperTradingBook()
