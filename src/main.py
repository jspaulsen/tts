from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
import importlib
import logging
import pkgutil

from fastapi import FastAPI, Request
import logfire

from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from sqlmodel import select
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import IntegrityError

from src.configuration import Configuration
from src.database import Database
import src.models
from src.cache import LRUCache, TTLCache
from src.api.limiter import limiter
from src.routers import (
    legacy_router,
    speech_router,
    users_router,
)

from src.tts.kokoro import KokoroProvider


# Dynamically import all models in src.models
# Automatically import all modules in src.models to register SQLModel metadata
package = src.models

for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
    if not is_pkg:
        importlib.import_module(module_name)


CONFIGURATION: Configuration = Configuration.get()


logger = logging.getLogger()


# Configure Logfire logging
logfire.configure(
    send_to_logfire=CONFIGURATION.logfire_token is not None,
    token=CONFIGURATION.logfire_token.get_secret_value() if CONFIGURATION.logfire_token else None,
    scrubbing=logfire.ScrubbingOptions(extra_patterns=['token']),
)

logger.addHandler(logfire.LogfireLoggingHandler())


# Instrument botocore with OpenTelemetry
BotocoreInstrumentor().instrument()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configuration = Configuration.get()

    # Setup the database
    database = await Database.initialize(configuration.async_database_url)
    logfire.instrument_sqlalchemy(database.engine, enable_commenter=True)

    # Setup LRU cache
    app.state.ttl_cache = TTLCache(maxsize=configuration.ttl_cache_size, ttl=configuration.ttl_cache_ttl)
    app.state.cache = LRUCache(max_size=configuration.lru_cache_size)
    app.state.database = database
    app.state.limiter = limiter  # TODO: Is this needed?

    # TODO: These providers should be initialized based on configuration
    # not hardcoded here.
    app.state.kokoro_provider = KokoroProvider(lang_code='a')

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
app.include_router(speech_router)
app.include_router(users_router)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
    )


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
