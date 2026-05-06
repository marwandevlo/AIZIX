from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    api_host: str = Field(default="0.0.0.0", alias="HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000"

    paper_trading: bool = Field(default=True, alias="PAPER_TRADING")
    live_trading_enabled: bool = Field(
        default=False,
        alias="LIVE_TRADING_ENABLED",
        description="Must remain false for this codebase — no live order routing.",
    )

    max_daily_loss_pct: float = Field(default=5.0, alias="MAX_DAILY_LOSS")
    max_risk_per_trade_pct: float = Field(default=2.0, alias="MAX_RISK_PER_TRADE")
    max_open_trades: int = Field(default=6, alias="MAX_OPEN_TRADES")
    min_signal_confidence_pct: float = Field(default=55.0, alias="MIN_SIGNAL_CONFIDENCE")

    supabase_url: str | None = None
    supabase_service_role_key: str | None = None

    database_url: str = Field(
        default="sqlite:///./aizix.db",
        alias="DATABASE_URL",
        description="SQLAlchemy URL (PostgreSQL or SQLite).",
    )
    jwt_secret_key: str = Field(
        default="change-me-in-production",
        validation_alias=AliasChoices("JWT_SECRET_KEY", "SECRET_KEY"),
        description=(
            "JWT signing secret only (HS256). SECRET_KEY env is an alias for this field. "
            "Demo user password is fixed in app/db/bootstrap.py (DEMO_SEED_PASSWORD), not from env."
        ),
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60 * 24 * 7, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    require_auth: bool = Field(
        default=True,
        alias="REQUIRE_AUTH",
        description="If true, all protected routes require a valid JWT (SaaS mode).",
    )
    demo_user_email: str = Field(default="demo@aizix.local", alias="DEMO_USER_EMAIL")
    binance_base_url: str = Field(default="https://api.binance.com", alias="BINANCE_BASE_URL")
    use_binance_market: bool = Field(
        default=True,
        validation_alias=AliasChoices("USE_BINANCE_MARKET", "BINANCE_PUBLIC_DATA"),
        description="Use Binance public REST for market snapshots when true.",
    )

    signal_latency_ms_min: int = 80
    signal_latency_ms_max: int = 280


def get_settings() -> Settings:
    return Settings()
