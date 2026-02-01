from fastapi import Request
from slowapi import Limiter

from src.configuration import Configuration


def by_api_token(request: Request) -> str:
    api_token = request.query_params.get("token")
    api_token = api_token or request.headers.get("Authorization")

    if api_token and api_token.startswith('Bearer '):
        api_token = api_token.split('Bearer ')[1].strip()

    if not api_token:
        return request.client.host if request.client and request.client.host else "127.0.0.1"

    return api_token


def get_character_cost(text: str | None = None) -> int:
    return len(text if text else '')


def callable_rate_limit() -> str:
    return (
        Configuration
            .get()
            .maximum_characters_per_minute
    )


limiter = Limiter(key_func=by_api_token)
