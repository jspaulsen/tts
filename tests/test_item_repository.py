import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.item import ItemCreate, ItemUpdate
from src.repositories.item import ItemRepository


@pytest.fixture
def repository(session: AsyncSession) -> ItemRepository:
    return ItemRepository(session)


@pytest.mark.asyncio
async def test_create_item(repository: ItemRepository) -> None:
    item_data = ItemCreate(name="Test Item", description="A test item", price=9.99)
    item = await repository.create(item_data)

    assert item.id is not None
    assert item.name == "Test Item"
    assert item.description == "A test item"
    assert item.price == 9.99


@pytest.mark.asyncio
async def test_get_item(repository: ItemRepository) -> None:
    item_data = ItemCreate(name="Test Item", price=9.99)
    created = await repository.create(item_data)

    fetched = await repository.get(created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == "Test Item"


@pytest.mark.asyncio
async def test_get_item_not_found(repository: ItemRepository) -> None:
    from uuid import uuid4

    result = await repository.get(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_get_all_items(repository: ItemRepository) -> None:
    await repository.create(ItemCreate(name="Item 1", price=10.00))
    await repository.create(ItemCreate(name="Item 2", price=20.00))
    await repository.create(ItemCreate(name="Item 3", price=30.00))

    items = await repository.get_all()
    assert len(items) == 3


@pytest.mark.asyncio
async def test_update_item(repository: ItemRepository) -> None:
    item_data = ItemCreate(name="Original", price=10.00)
    created = await repository.create(item_data)

    update_data = ItemUpdate(name="Updated", price=15.00)
    updated = await repository.update(created.id, update_data)

    assert updated is not None
    assert updated.name == "Updated"
    assert updated.price == 15.00


@pytest.mark.asyncio
async def test_update_item_partial(repository: ItemRepository) -> None:
    item_data = ItemCreate(name="Original", description="Desc", price=10.00)
    created = await repository.create(item_data)

    update_data = ItemUpdate(name="Updated")
    updated = await repository.update(created.id, update_data)

    assert updated is not None
    assert updated.name == "Updated"
    assert updated.description == "Desc"
    assert updated.price == 10.00


@pytest.mark.asyncio
async def test_delete_item(repository: ItemRepository) -> None:
    item_data = ItemCreate(name="To Delete", price=10.00)
    created = await repository.create(item_data)

    deleted = await repository.delete(created.id)
    assert deleted is True

    fetched = await repository.get(created.id)
    assert fetched is None


@pytest.mark.asyncio
async def test_delete_item_not_found(repository: ItemRepository) -> None:
    from uuid import uuid4

    deleted = await repository.delete(uuid4())
    assert deleted is False
