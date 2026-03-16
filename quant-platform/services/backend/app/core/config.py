from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, PostgresDsn, Field


class Settings(BaseSettings):
    api_title: str = "Quant Trading Platform"
    api_version: str = "0.1.0"
    api_docs_url: str = "/docs"
    api_openapi_url: str = "/openapi.json"

    redis_url: str = "redis://redis:6379/0"
    postgres_dsn: PostgresDsn | None = Field(
        default=None,
        description="SQLAlchemy-compatible DSN, e.g. postgresql+psycopg://postgres:postgres@postgres:5432/quant",
    )

    binance_api_key: str | None = None
    binance_api_secret: str | None = None
    trading_symbol: str = "BTC/USDT"

    frontend_base_url: AnyHttpUrl | None = None
    telemetry_webhook: str | None = Field(default=None, description="Generic webhook for telemetry")
    telegram_bot_token: str | None = Field(default=None, description="Telegram bot token")
    telegram_chat_id: str | None = Field(default=None, description="Telegram chat ID for alerts")
    historical_csv_path: Path | None = Field(
        default=None,
        description="Path to historical OHLCV CSV used for training/backtests",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
