from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.item import Item, ItemCreate, ItemUpdate
from app.repositories.item import ItemRepository

router = APIRouter(prefix="/items", tags=["items"])


def get_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ItemRepository:
    return ItemRepository(session)


@router.get("/", response_model=Sequence[Item])
async def list_items(
    repo: Annotated[ItemRepository, Depends(get_repository)],
    offset: int = 0,
    limit: int = 100,
) -> Sequence[Item]:
    return await repo.get_all(offset=offset, limit=limit)


@router.get("/{item_id}", response_model=Item)
async def get_item(
    item_id: UUID,
    repo: Annotated[ItemRepository, Depends(get_repository)],
) -> Item:
    item = await repo.get(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.post("/", response_model=Item, status_code=status.HTTP_201_CREATED)
async def create_item(
    item: ItemCreate,
    repo: Annotated[ItemRepository, Depends(get_repository)],
) -> Item:
    return await repo.create(item)


@router.patch("/{item_id}", response_model=Item)
async def update_item(
    item_id: UUID,
    item: ItemUpdate,
    repo: Annotated[ItemRepository, Depends(get_repository)],
) -> Item:
    updated = await repo.update(item_id, item)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return updated


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: UUID,
    repo: Annotated[ItemRepository, Depends(get_repository)],
) -> None:
    deleted = await repo.delete(item_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
