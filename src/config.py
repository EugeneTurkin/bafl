from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    NETWORK_STORAGE: Path
    STORAGE_DIR: Path

    model_config = SettingsConfigDict(env_file=".env")


config = Config()
