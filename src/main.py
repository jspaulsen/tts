from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
import importlib
import pkgutil

from fastapi import FastAPI, Request
import logfire
from sqlmodel import select
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from src.configuration import Configuration
from src.database import Database
import src.models
from src.cache import LRUCache
from src.routers import (
    legacy_router,
    users_router,
)


# Dynamically import all models in src.models
# Automatically import all modules in src.models to register SQLModel metadata
package = src.models

for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
    if not is_pkg:
        importlib.import_module(module_name)


logfire.configure()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configuration = Configuration.get()

    # Setup the database
    database = await Database.initialize(configuration.async_database_url)
    logfire.instrument_sqlalchemy(database.engine, enable_commenter=True)

    # Setup LRU cache
    app.state.cache = LRUCache()
    app.state.database = database

    yield

    await database.close()


app = FastAPI(title="TTS", lifespan=lifespan)
logfire.instrument_fastapi(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(legacy_router)
app.include_router(users_router)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": "Resource already exists"},
    )


@app.get("/health")
async def health(request: Request) -> dict[str, str]:
    database: Database = request.app.state.database

    async with database.get_session() as session:
        await session.exec(select(1))

    return {"status": "ok"}
