from __future__ import annotations
import re

from pydantic import SecretStr
from pydantic_settings import BaseSettings


CONFIGURATION: Configuration | None = None


class Configuration(BaseSettings):
    maximum_characters_per_request: int = 2048
    lru_cache_size: int = 64

    database_url: SecretStr

    # TODO: Let's find a better way to handle admin API keys
    admin_api_token: SecretStr

    logfire_token: SecretStr | None = None
    log_level: str = "INFO"


    @staticmethod
    def get() -> Configuration:
        global CONFIGURATION

        if CONFIGURATION is None:
            CONFIGURATION = Configuration()  # type: ignore[assignment]

        return CONFIGURATION

    @property
    def async_database_url(self) -> str:
        ret = self.database_url.get_secret_value()

        if ret.startswith("postgres://"):
            ret = ret.replace("postgres://", "postgresql+asyncpg://", 1)

        if ret.startswith("postgresql://"):
            ret = ret.replace("postgresql://", "postgresql+asyncpg://", 1)

        # asyncpg doesn't correctly support sslmode with postgresql+asyncpg://
        # For now, just remove it from the string outright
        ret = re.sub(r'[?&]sslmode=[^&]*$', '', ret)
        return ret
