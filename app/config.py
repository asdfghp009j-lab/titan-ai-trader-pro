from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TITAN_", env_file=".env", extra="ignore")

    api_key: SecretStr = Field(default=SecretStr(""))
    database_path: str = "titan.sqlite3"
    mt5_enabled: bool = False
    mt5_login: int | None = None
    mt5_password: SecretStr | None = None
    mt5_server: str | None = None
    mt5_path: str | None = None
    telegram_bot_token: SecretStr | None = None
    telegram_chat_id: str | None = None
    max_risk_pct: float = Field(default=0.5, gt=0, le=1.0)
    max_position_lots: float = Field(default=1.0, gt=0, le=100)


settings = Settings()
