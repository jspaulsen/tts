from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession



class Database:
    """
    Manages SQLite database connections and sessions using SQLModel.
    """

    def __init__(
        self,
        engine: AsyncEngine,
    ) -> None:
        self.engine: AsyncEngine = engine

    @classmethod
    async def initialize(
        cls,
        database_url: str,
        debug: bool = False,
    ) -> Database:
        engine: AsyncEngine = create_async_engine(
            database_url,
            echo=debug,
            future=True,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )

        # async with engine.begin() as conn:
        #     await conn.run_sync(SQLModel.metadata.create_all)

        return cls(engine)

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[SQLModelAsyncSession, None]:
        """
        Async context manager that provides a database session.

        Yields:
            AsyncSession for database operations
        """
        async with SQLModelAsyncSession(self.engine) as session:
            yield session

    async def close(self) -> None:
        """
        Close the database engine and cleanup resources.
        """
        await self.engine.dispose()
