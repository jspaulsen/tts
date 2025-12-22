from fastapi import HTTPException, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import select

from src.configuration import Configuration
from src.database import Database
from src.models.user import User


security = HTTPBearer()


async def get_authorization_token(
    configuration: Configuration = Depends(Configuration.get),
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    token = credentials.credentials

    if token != configuration.admin_api_token.get_secret_value():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token",
        )

    return token


async def legacy_get_current_user(
    request: Request,
    token: str | None,
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API token is required",
        )

    database: Database = request.app.state.database

    async with database.get_session() as session:
        result = await session.exec(select(User).where(User.api_token == token))
        user = result.one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API token",
            )

    return user


async def get_current_user(
    request: Request,
    # configuration: Configuration = Depends(Configuration.get),
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    database: Database = request.app.state.database
    token = credentials.credentials

    async with database.get_session() as session:
        result = await session.exec(select(User).where(User.api_token == token))
        user = result.one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API token",
            )

    return user
