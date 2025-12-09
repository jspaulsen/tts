from __future__ import annotations
import re

from pydantic_settings import BaseSettings


CONFIGURATION: Configuration | None = None


class Configuration(BaseSettings):
    maximum_characters_per_request: int = 2048
    lru_cache_size: int = 64

    database_url: str

    # TODO: Let's find a better way to handle admin API keys
    admin_api_token: str

    @staticmethod
    def get() -> Configuration:
        global CONFIGURATION

        if CONFIGURATION is None:
            CONFIGURATION = Configuration()  # type: ignore[assignment]

        return CONFIGURATION

    @property
    def async_database_url(self) -> str:
        ret = self.database_url

        if self.database_url.startswith("postgres://"):
            ret =  self.database_url.replace("postgres://", "postgresql+asyncpg://", 1)

        if self.database_url.startswith("postgresql://"):
            ret = self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        # asyncpg doesn't correctly support sslmode with postgresql+asyncpg://
        # For now, just remove it from the string outright
        ret = re.sub(r'[?&]sslmode=[^&]*$', '', ret)
        return ret
