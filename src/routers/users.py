import secrets
from fastapi import APIRouter, Request, Depends
from sqlmodel import select

from src.database import Database
from src.models.user import CreateUser, User
from src.api.auth import get_authorization_token


router = APIRouter(
    prefix="/users",

    # all routes are protected
    dependencies=[
        Depends(get_authorization_token)
    ],
)


@router.get("/")
async def get_users(
    request: Request,
) -> list[User]:
    database: Database = request.app.state.database

    async with database.get_session() as session:
        req = await session.exec(select(User))
        users = req.all()

    return list(users)


@router.post("/")
async def create_user(
    request: Request,
    user: CreateUser,
) -> User:
    database: Database = request.app.state.database

    async with database.get_session() as session:
        nuser = User(
            **user.model_dump(),
            api_token=secrets.token_urlsafe(32),
        )

        session.add(nuser)
        await session.commit()
        await session.refresh(nuser)

    return nuser
