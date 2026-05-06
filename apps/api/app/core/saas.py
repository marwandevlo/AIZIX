"""SaaS boundaries — tenant context and persistence hooks (future Supabase / multi-user).

The dashboard currently runs as a single-tenant paper deployment. Import `TenantContext`
when wiring authenticated routes; persist dashboard state via `repository` once accounts land.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class TenantContext:
    """Reserved for authenticated workspace isolation."""

    tenant_id: UUID | None = None
    user_id: UUID | None = None
    plan: str = "paper"


class RepositoryStub:
    """Replace with Supabase / Postgres repository implementing async CRUD."""

    async def load_dashboard_prefs(self, tenant_id: UUID) -> dict[str, Any] | None:
        return None

    async def save_dashboard_prefs(self, tenant_id: UUID, prefs: dict[str, Any]) -> None:
        raise NotImplementedError("Persist preferences once database layer is connected.")
