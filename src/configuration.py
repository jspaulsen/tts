from __future__ import annotations
from pydantic_settings import BaseSettings


CONFIGURATION: Configuration | None = None


class Configuration(BaseSettings):
    api_token: str | None = None

    @staticmethod
    def get() -> Configuration:
        global CONFIGURATION

        if CONFIGURATION is None:
            CONFIGURATION = Configuration()

        return CONFIGURATION
