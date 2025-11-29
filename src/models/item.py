from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class ItemBase(SQLModel):
    name: str = Field(index=True)
    description: str | None = None
    price: float = Field(ge=0)


class Item(ItemBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)


class ItemCreate(ItemBase):
    pass


class ItemUpdate(SQLModel):
    name: str | None = None
    description: str | None = None
    price: float | None = Field(default=None, ge=0)
