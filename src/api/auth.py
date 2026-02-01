from fastapi import HTTPException, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import SecretStr
from sqlmodel import select

from src.cache import TTLCache
from src.configuration import Configuration
from src.database import Database
from src.models.user import User


security = HTTPBearer(auto_error=False)


async def get_authorization_token(
    configuration: Configuration = Depends(Configuration.get),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> SecretStr:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token",
        )

    token = credentials.credentials

    if token != configuration.admin_api_token.get_secret_value():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token",
        )

    return SecretStr(token)


async def get_current_user(
    request: Request,
    token: SecretStr | None = None,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User:
    ttl_cache: TTLCache[User] = request.app.state.ttl_cache
    api_token = credentials.credentials if credentials else token

    if not api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API token is required",
        )

    api_token = SecretStr(api_token) if not isinstance(api_token, SecretStr) else api_token

    if cached_user := await ttl_cache.get(api_token.get_secret_value()):
        return cached_user

    database: Database = request.app.state.database

    async with database.get_session() as session:
        result = await session.exec(
            select(User)
                .where(User.api_token == api_token.get_secret_value())
        )

        user = result.one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API token",
            )

    await ttl_cache.set(api_token.get_secret_value(), user)
    return user
