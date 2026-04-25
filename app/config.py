from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    temporal_host: str = "localhost:7233"
    temporal_namespace: str = "cronjobs"
    temporal_task_queue: str = "smartass-checker"
    telegram_bot_token: str
    telegram_chat_id: str
    smartass_url: str = "https://smartass.club/lviv-myrnoho/calendar"
    state_file: str = "~/.smartass_state.json"
    metrics_port: int = 9090


@lru_cache
def get_settings() -> Settings:
    return Settings()
