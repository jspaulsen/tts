import io
from typing import Literal, cast, get_args
import xml.etree.ElementTree as ET

from fastapi import APIRouter, HTTPException, Query, Request, Response, Depends, status
from fastapi.responses import StreamingResponse

from src.api.auth import get_current_user
from src.api.limiter import limiter, get_character_cost
from src.cache import LRUCache
from src.clients.polly import PollyProvider, SSMLException, TextTypeType
from src.configuration import Configuration
from src.database import Database
from src.models.usage import Usage
from src.models.user import User
from src.tts.kokoro import KokoroProvider
from src.types.aws import AWSStandardVoices
from src.types.kokoro import KokoroVoices

# Combined type for OpenAPI schema generation
SupportedVoices = Literal[AWSStandardVoices, KokoroVoices]

# Extend this as we add more providers
router = APIRouter(prefix="/v1")


@router.get("/voices")
async def get_voices() -> list[str]:
    return list(get_args(AWSStandardVoices)) + list(get_args(KokoroVoices))


# Maybe we want to call specific vendors? I.E>., /v1/speech/polly, /v1/speech/kokoro, etc.
@router.get("/speech")
@limiter.limit("4096/minute", cost=get_character_cost)
async def get_speech(
    request: Request,
    voice: SupportedVoices = Query(...),
    text: str = Query(...),
    text_type: TextTypeType = Query(default=TextTypeType.Text),
    configuration: Configuration = Depends(Configuration.get),
    user: User = Depends(get_current_user),
) -> Response:
    database: Database = request.app.state.database
    cache: LRUCache[bytes] = request.app.state.cache

    if len(text) > configuration.maximum_characters_per_request:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Text length exceeds maximum of {configuration.maximum_characters_per_request} characters.",
        )


    # We need to route requests based on the speaker
    # TODO: I sort of hate this.
    provider: PollyProvider | KokoroProvider | None = None
    cache_key: str | None = None

    match voice:
        case v if v in PollyProvider.voices():
            provider = PollyProvider()
        case v if v in KokoroProvider.voices():
            provider = request.app.state.kokoro_provider
        case _:
            provider = None

    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Voice '{voice}' is not supported by any available TTS provider.",
        )

    if provider.can_cache:
        cache_key = provider.generate_cache(voice, text)

        if cached_audio := await cache.get(cache_key):
            return StreamingResponse(
                content=io.BytesIO(cached_audio),
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": f'inline; filename="{voice}.mp3"',
                }
            )

    if provider.has_financial_cost:
        async with database.get_session() as session:
            session.add(
                Usage(
                    user_id=user.id,
                    characters_used=len(text),
                )
            )

            await session.commit()

    # TODO: Support SSML input where applicable
    if text_type == TextTypeType.Ssml:
        try:
            ET.fromstring(text)
        except ET.ParseError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid SSML format: {str(e)}. Ensure your SSML is well-formed XML and includes required tags like <speak>.",
            )

    # TODO: Correct the typing nightmare here
    content = await provider.synthesize_speech(voice, text)  # type: ignore
    if provider.can_cache and cache_key is not None:
        await cache.set(cache_key, content)

    return StreamingResponse(
        content=io.BytesIO(content),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'inline; filename="{voice}.mp3"',
        }
    )
