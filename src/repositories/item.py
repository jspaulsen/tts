from collections.abc import Sequence
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.item import Item, ItemCreate, ItemUpdate
from app.repositories.base import AbstractRepository


class ItemRepository(AbstractRepository[Item, ItemCreate, ItemUpdate]):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, id: UUID) -> Item | None:
        return await self.session.get(Item, id)

    async def get_all(self, offset: int = 0, limit: int = 100) -> Sequence[Item]:
        result = await self.session.exec(select(Item).offset(offset).limit(limit))
        return result.all()

    async def create(self, obj: ItemCreate) -> Item:
        item = Item.model_validate(obj)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def update(self, id: UUID, obj: ItemUpdate) -> Item | None:
        item = await self.get(id)
        if not item:
            return None
        update_data = obj.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item, key, value)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def delete(self, id: UUID) -> bool:
        item = await self.get(id)
        if not item:
            return False
        await self.session.delete(item)
        await self.session.commit()
        return True
