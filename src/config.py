from pathlib import Path

from huey import SqliteHuey
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyUrl
from pydantic.types import SecretStr


class Config(BaseSettings):
    ROOTDIR: Path = Path(__file__).parent.parent
    FILES_DIR: Path = ROOTDIR / "files"
    NETWORK_STORAGE: Path
    STORAGE_DIR: Path

    YADISK_API_BASE_URL: AnyUrl
    YADISK_DIR: str
    YADISK_OAUTH_TOKEN: str

    model_config = SettingsConfigDict(env_file=".env")

    @property
    def UPLOAD_DST(self):
        return self.NETWORK_STORAGE / self.STORAGE_DIR


config = Config()
huey = SqliteHuey("bafl", filename=config.ROOTDIR / "huey.sqlite", immediate=True)
