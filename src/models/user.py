from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    username: str = Field(index=True, unique=True)


class User(UserBase, table=True):
    id: int = Field(default=None, primary_key=True)
    api_token: str = Field(index=True, unique=True)


class CreateUser(UserBase):
    pass
