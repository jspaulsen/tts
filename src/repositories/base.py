from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Generic, TypeVar
from uuid import UUID

from sqlmodel import SQLModel

T = TypeVar("T", bound=SQLModel)
CreateT = TypeVar("CreateT", bound=SQLModel)
UpdateT = TypeVar("UpdateT", bound=SQLModel)


class AbstractRepository(ABC, Generic[T, CreateT, UpdateT]):
    @abstractmethod
    async def get(self, id: UUID) -> T | None:
        raise NotImplementedError

    @abstractmethod
    async def get_all(self, offset: int = 0, limit: int = 100) -> Sequence[T]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, obj: CreateT) -> T:
        raise NotImplementedError

    @abstractmethod
    async def update(self, id: UUID, obj: UpdateT) -> T | None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        raise NotImplementedError
