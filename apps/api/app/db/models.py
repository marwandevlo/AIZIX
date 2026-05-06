from __future__ import annotations

import datetime as dt

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    balance_usd: Mapped[float] = mapped_column(Float, default=12_540.25)
    prefs_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    trades: Mapped[list["TradeRecord"]] = relationship(back_populates="user")
    signals: Mapped[list["SignalRecord"]] = relationship(back_populates="user")
    strategies: Mapped[list["Strategy"]] = relationship(back_populates="user")
    portfolio: Mapped["Portfolio | None"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Portfolio(Base):
    """Snapshot row per user for dashboard persistence (cash, peak DD context)."""

    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    balance_usd: Mapped[float] = mapped_column(Float, default=12_540.25)
    portfolio_value_usd: Mapped[float] = mapped_column(Float, default=12_540.25)
    peak_equity_usd: Mapped[float] = mapped_column(Float, default=12_540.25)
    positions_json: Mapped[str] = mapped_column(Text, default="[]")
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)

    user: Mapped["User"] = relationship(back_populates="portfolio")


class TradeRecord(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(64))
    side: Mapped[str] = mapped_column(String(8))
    qty: Mapped[float] = mapped_column(Float)
    entry_price: Mapped[float] = mapped_column(Float)
    exit_price: Mapped[float] = mapped_column(Float)
    pnl_usd: Mapped[float] = mapped_column(Float)
    pnl_pct: Mapped[float] = mapped_column(Float)
    opened_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    closed_at: Mapped[str] = mapped_column(String(64))
    paper: Mapped[bool] = mapped_column(Boolean, default=True)
    confidence_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="trades")


class SignalRecord(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    pair: Mapped[str] = mapped_column(String(32))
    action: Mapped[str] = mapped_column(String(8))
    confidence_pct: Mapped[float] = mapped_column(Float)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    as_of: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    user: Mapped["User"] = relationship(back_populates="signals")


class Strategy(Base):
    __tablename__ = "strategies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    sl_pct: Mapped[float] = mapped_column(Float, default=2.0)
    tp_pct: Mapped[float] = mapped_column(Float, default=4.0)
    trail_pct: Mapped[float] = mapped_column(Float, default=1.25)
    risk_level: Mapped[int] = mapped_column(Integer, default=65)
    max_open_trades: Mapped[int] = mapped_column(Integer, default=12)
    confidence_threshold: Mapped[float] = mapped_column(Float, default=60.0)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    user: Mapped["User"] = relationship(back_populates="strategies")
