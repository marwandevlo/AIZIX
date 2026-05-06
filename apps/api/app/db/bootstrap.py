from __future__ import annotations

import json

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import get_password_hash

# Fixed demo seed password — never derive from JWT_SECRET_KEY / SECRET_KEY (bcrypt max 72 bytes).
DEMO_SEED_PASSWORD = "AizixDemo123!"
from app.db.base import Base
from app.db.database import engine
from app.db.models import Portfolio, User


def _migrate_audit_log_columns() -> None:
    """Add session_id and metadata_json to existing audit_logs tables."""
    insp = inspect(engine)
    if "audit_logs" not in insp.get_table_names():
        return
    dialect = engine.dialect.name
    cols = {c["name"] for c in insp.get_columns("audit_logs")}
    with engine.begin() as conn:
        if "session_id" not in cols:
            if dialect == "sqlite":
                conn.execute(text("ALTER TABLE audit_logs ADD COLUMN session_id VARCHAR(64)"))
            else:
                conn.execute(text("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS session_id VARCHAR(64)"))
        if "metadata_json" not in cols:
            if dialect == "sqlite":
                conn.execute(text("ALTER TABLE audit_logs ADD COLUMN metadata_json TEXT DEFAULT '{}'"))
            else:
                conn.execute(
                    text("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS metadata_json TEXT DEFAULT '{}'")
                )


def _migrate_trade_metadata_columns() -> None:
    """Add paper trade attribution columns on existing DBs (SQLite / Postgres)."""
    insp = inspect(engine)
    if "trades" not in insp.get_table_names():
        return
    dialect = engine.dialect.name
    cols = {c["name"] for c in insp.get_columns("trades")}
    with engine.begin() as conn:
        if "confidence_pct" not in cols:
            if dialect == "sqlite":
                conn.execute(text("ALTER TABLE trades ADD COLUMN confidence_pct FLOAT"))
            else:
                conn.execute(text("ALTER TABLE trades ADD COLUMN IF NOT EXISTS confidence_pct DOUBLE PRECISION"))
        if "risk_level" not in cols:
            if dialect == "sqlite":
                conn.execute(text("ALTER TABLE trades ADD COLUMN risk_level VARCHAR(32)"))
            else:
                conn.execute(text("ALTER TABLE trades ADD COLUMN IF NOT EXISTS risk_level VARCHAR(32)"))
        if "reason" not in cols:
            if dialect == "sqlite":
                conn.execute(text("ALTER TABLE trades ADD COLUMN reason TEXT"))
            else:
                conn.execute(text("ALTER TABLE trades ADD COLUMN IF NOT EXISTS reason TEXT"))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _migrate_trade_metadata_columns()
    _migrate_audit_log_columns()


def ensure_demo_user(db: Session, settings: Settings) -> None:
    email = settings.demo_user_email
    u = db.query(User).filter(User.email == email).one_or_none()
    if u:
        if u.portfolio is None:
            db.add(
                Portfolio(
                    user_id=u.id,
                    balance_usd=u.balance_usd,
                    portfolio_value_usd=u.balance_usd,
                    peak_equity_usd=u.balance_usd,
                )
            )
            db.commit()
        return
    user = User(
        email=email,
        hashed_password=get_password_hash(DEMO_SEED_PASSWORD),
        balance_usd=12_540.25,
        prefs_json=json.dumps(
            {
                "strategy": "AI Adaptive Strategy",
                "trading_mode": "ETF MODE",
                "pair": "BTC3L/USDT",
            }
        ),
    )
    db.add(user)
    db.flush()
    db.add(
        Portfolio(
            user_id=user.id,
            balance_usd=user.balance_usd,
            portfolio_value_usd=user.balance_usd,
            peak_equity_usd=user.balance_usd,
        )
    )
    db.commit()
