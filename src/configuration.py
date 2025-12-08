from __future__ import annotations
from pydantic_settings import BaseSettings


CONFIGURATION: Configuration | None = None


class Configuration(BaseSettings):
    api_token: str | None = None
    maximum_characters_per_request: int = 1024

    # Postgres example: postgres+asyncpg://user:password@localhost/dbname
    database_url: str

    # TODO: Let's find a better way to handle admin API keys
    admin_api_token: str

    @staticmethod
    def get() -> Configuration:
        global CONFIGURATION

        if CONFIGURATION is None:
            CONFIGURATION = Configuration()  # type: ignore[assignment]

        return CONFIGURATION

    # TODO: This is incorrect and it needs to be postgresql not postgres
    @property
    def async_database_url(self) -> str:
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql+asyncpg://", 1)

        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        return self.database_url
