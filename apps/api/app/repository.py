"""Persistence: Supabase when configured, else in-process memory."""

from __future__ import annotations

import asyncio
import copy
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

from supabase import Client, create_client

from app.config import Settings
from app.compounding import wallet_balances

logger = logging.getLogger(__name__)

BotStatus = Literal["ACTIVE", "PAUSED", "STOPPED"]


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class BotStateRow:
    id: str = "default"
    status: BotStatus = "STOPPED"
    compounding_enabled: bool = True
    total_balance_usd: float = 12_540.0
    trading_balance_usd: float = 8_778.0
    safety_balance_usd: float = 3_762.0
    win_rate_pct: float = 78.0
    daily_pnl_usd: float = 240.0
    updated_at: str = field(default_factory=_utcnow)


class MemoryRepository:
    def __init__(self) -> None:
        self._state = BotStateRow(status="STOPPED")
        self._signals: list[dict[str, Any]] = []

    async def get_bot_state(self) -> BotStateRow:
        return copy.deepcopy(self._state)

    async def set_status(self, status: BotStatus) -> BotStateRow:
        self._state.status = status
        self._state.updated_at = _utcnow()
        return copy.deepcopy(self._state)

    async def set_compounding(self, enabled: bool) -> BotStateRow:
        self._state.compounding_enabled = enabled
        b = wallet_balances(self._state.total_balance_usd, enabled)
        self._state.trading_balance_usd = b["trading_balance"]
        self._state.safety_balance_usd = b["safety_balance"]
        self._state.updated_at = _utcnow()
        return copy.deepcopy(self._state)

    async def apply_market_tick(self) -> BotStateRow:
        """Small random PnL / balance drift so the UI feels alive."""
        import random

        r = random.Random()
        delta = r.uniform(-85.0, 110.0)
        self._state.daily_pnl_usd = round(max(-400.0, self._state.daily_pnl_usd + delta * 0.08), 2)
        self._state.total_balance_usd = round(max(2_000.0, self._state.total_balance_usd + delta * 0.05), 2)
        self._state.win_rate_pct = round(
            min(92.0, max(55.0, self._state.win_rate_pct + r.uniform(-1.1, 1.1)), 2
        )
        b = wallet_balances(self._state.total_balance_usd, self._state.compounding_enabled)
        self._state.trading_balance_usd = b["trading_balance"]
        self._state.safety_balance_usd = b["safety_balance"]
        self._state.updated_at = _utcnow()
        return copy.deepcopy(self._state)

    async def insert_signal(self, payload: dict[str, Any]) -> None:
        row = {
            **payload,
            "id": str(uuid.uuid4()),
            "created_at": _utcnow(),
        }
        self._signals.insert(0, row)
        self._signals = self._signals[:80]

    async def list_signals(self, limit: int = 12) -> list[dict[str, Any]]:
        return copy.deepcopy(self._signals[:limit])


class SupabaseRepository:
    def __init__(self, client: Client) -> None:
        self._client = client

    async def get_bot_state(self) -> BotStateRow:
        def _run() -> dict[str, Any]:
            res = (
                self._client.table("bot_state")
                .select("*")
                .eq("id", "default")
                .limit(1)
                .execute()
            )
            rows = res.data or []
            if not rows:
                self._client.table("bot_state").insert({"id": "default"}).execute()
                res2 = (
                    self._client.table("bot_state")
                    .select("*")
                    .eq("id", "default")
                    .single()
                    .execute()
                )
                return res2.data
            return rows[0]

        data = await asyncio.to_thread(_run)
        return BotStateRow(
            id=str(data.get("id", "default")),
            status=data.get("status", "STOPPED"),  # type: ignore[arg-type]
            compounding_enabled=bool(data.get("compounding_enabled", True)),
            total_balance_usd=float(data.get("total_balance_usd", 12_540)),
            trading_balance_usd=float(data.get("trading_balance_usd", 8_778)),
            safety_balance_usd=float(data.get("safety_balance_usd", 3_762)),
            win_rate_pct=float(data.get("win_rate_pct", 78)),
            daily_pnl_usd=float(data.get("daily_pnl_usd", 240)),
            updated_at=str(data.get("updated_at", _utcnow())),
        )

    async def _upsert_state(self, patch: dict[str, Any]) -> None:
        patch = {**patch, "updated_at": _utcnow()}

        def _run() -> None:
            self._client.table("bot_state").upsert({"id": "default", **patch}).execute()

        await asyncio.to_thread(_run)

    async def set_status(self, status: BotStatus) -> BotStateRow:
        await self._upsert_state({"status": status})
        return await self.get_bot_state()

    async def set_compounding(self, enabled: bool) -> BotStateRow:
        st = await self.get_bot_state()
        b = wallet_balances(st.total_balance_usd, enabled)
        await self._upsert_state(
            {
                "compounding_enabled": enabled,
                "trading_balance_usd": b["trading_balance"],
                "safety_balance_usd": b["safety_balance"],
            }
        )
        return await self.get_bot_state()

    async def apply_market_tick(self) -> BotStateRow:
        import random

        r = random.Random()
        st = await self.get_bot_state()
        delta = r.uniform(-85.0, 110.0)
        daily = round(max(-400.0, st.daily_pnl_usd + delta * 0.08), 2)
        total = round(max(2_000.0, st.total_balance_usd + delta * 0.05), 2)
        win = round(min(92.0, max(55.0, st.win_rate_pct + r.uniform(-1.1, 1.1))), 2)
        b = wallet_balances(total, st.compounding_enabled)
        await self._upsert_state(
            {
                "daily_pnl_usd": daily,
                "total_balance_usd": total,
                "trading_balance_usd": b["trading_balance"],
                "safety_balance_usd": b["safety_balance"],
                "win_rate_pct": win,
            }
        )
        return await self.get_bot_state()

    async def insert_signal(self, payload: dict[str, Any]) -> None:
        api = payload
        action = str(api["action"]).lower()
        conf = float(api["confidence_pct"])
        if conf > 1.0:
            conf = min(1.0, conf / 100.0)

        row = {
            "symbol": "AIZIX-ETF",
            "action": action,
            "confidence": conf,
            "mood": api["market_mood"],
            "reason": str(api.get("reason", "simulated_engine"))[:2000],
            "payload": {
                "etf_bias": api.get("etf_bias"),
                "whale_activity": api.get("whale_activity"),
                "prices": api.get("prices"),
                "latency_ms": api.get("latency_ms"),
                "action_display": api.get("action"),
                "reason": api.get("reason"),
                "risk_status": api.get("risk_status"),
                "symbol": api.get("symbol"),
                "etf_symbol": api.get("etf_symbol"),
                "market": api.get("market"),
            },
        }

        def _run() -> None:
            self._client.table("signals").insert(row).execute()

        try:
            await asyncio.to_thread(_run)
        except Exception as e:  # noqa: BLE001
            logger.warning("Supabase signals insert failed: %s", e)

    async def insert_trade_if_executed(self, action: str, prices: dict[str, float]) -> None:
        if action not in ("BUY", "SELL"):
            return
        sym = "BTC"
        px = float(prices.get("BTC", 60_000))

        def _run() -> None:
            self._client.table("trades").insert(
                {
                    "symbol": sym,
                    "side": "buy" if action == "BUY" else "sell",
                    "quantity": round(0.01 + (uuid.uuid4().int % 100) / 10_000, 6),
                    "price": px,
                    "status": "simulated",
                    "meta": {"source": "signal_engine"},
                }
            ).execute()

        try:
            await asyncio.to_thread(_run)
        except Exception as e:  # noqa: BLE001
            logger.warning("Supabase trades insert failed: %s", e)

    async def list_signals(self, limit: int = 12) -> list[dict[str, Any]]:
        def _run() -> list[dict[str, Any]]:
            res = (
                self._client.table("signals")
                .select("id, symbol, action, confidence, mood, payload, created_at")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return list(res.data or [])

        try:
            rows = await asyncio.to_thread(_run)
        except Exception as e:  # noqa: BLE001
            logger.warning("Supabase signals list failed: %s", e)
            return []

        out: list[dict[str, Any]] = []
        for r in rows:
            pay = r.get("payload") or {}
            act = str(pay.get("action_display", r.get("action", "HOLD"))).upper()
            if act not in ("BUY", "SELL", "HOLD"):
                act = str(r.get("action", "hold")).upper()
            conf = float(r.get("confidence", 0.5))
            if conf <= 1.0:
                conf *= 100.0
            out.append(
                {
                    "action": act,
                    "symbol": pay.get("symbol", "—"),
                    "etf_symbol": pay.get("etf_symbol", "—"),
                    "confidence_pct": round(conf, 1),
                    "market_mood": r.get("mood", "Cautious ⚠️"),
                    "reason": pay.get("reason", r.get("reason", "")),
                    "risk_status": pay.get("risk_status", "ok"),
                    "etf_bias": pay.get("etf_bias", ""),
                    "whale_activity": pay.get("whale_activity", {}),
                    "prices": pay.get("prices", {}),
                    "latency_ms": float(pay.get("latency_ms", 0)),
                    "market": pay.get("market"),
                    "created_at": r.get("created_at"),
                }
            )
        return out


def build_repository(settings: Settings) -> MemoryRepository | SupabaseRepository:
    url = (settings.supabase_url or "").strip()
    key = (settings.supabase_service_role_key or "").strip()
    if url and key:
        client = create_client(url, key)
        return SupabaseRepository(client)
    return MemoryRepository()
