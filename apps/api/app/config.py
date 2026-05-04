from pydantic import Field
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
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    paper_trading: bool = Field(default=True, alias="PAPER_TRADING")

    max_daily_loss_pct: float = Field(default=5.0, alias="MAX_DAILY_LOSS")
    max_risk_per_trade_pct: float = Field(default=2.0, alias="MAX_RISK_PER_TRADE")
    max_open_trades: int = Field(default=4, alias="MAX_OPEN_TRADES")
    min_signal_confidence_pct: float = Field(default=65.0, alias="MIN_SIGNAL_CONFIDENCE")

    supabase_url: str | None = None
    supabase_service_role_key: str | None = None

    signal_latency_ms_min: int = 120
    signal_latency_ms_max: int = 420


def get_settings() -> Settings:
    return Settings()
