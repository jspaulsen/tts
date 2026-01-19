from src.routers.legacy import router as legacy_router
from src.routers.speech import router as speech_router
from src.routers.users import router as users_router


__all__ = [
    "legacy_router",
    "speech_router",
    "users_router",
]
