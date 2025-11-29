from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from src.routers import legacy_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield


app = FastAPI(title="TTS", lifespan=lifespan)
app.include_router(legacy_router)



@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
