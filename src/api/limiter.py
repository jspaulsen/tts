from fastapi import Request
from fastapi.security import HTTPBearer
from slowapi import Limiter


security = HTTPBearer(auto_error=False)


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


limiter = Limiter(key_func=by_api_token)
