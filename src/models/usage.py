import datetime
from sqlmodel import Field, SQLModel


class Usage(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)

    characters_used: int
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None),
        index=True,
    )
