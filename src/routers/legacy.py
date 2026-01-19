import xml.etree.ElementTree as ET

from fastapi import APIRouter, HTTPException, Request, Response, Depends, status

from src.api.auth import get_current_user
from src.cache import LRUCache
from src.clients.polly import PollyProvider, SSMLException, TextTypeType
from src.configuration import Configuration
from src.database import Database
from src.models.usage import Usage
from src.models.user import User
from src.types.aws import AWSStandardVoices


router = APIRouter(prefix="/legacy")


@router.get("/speech")
async def get_legacy_speech(
    request: Request,
    voice: AWSStandardVoices,
    text: str,
    text_type: TextTypeType = TextTypeType.Text,
    configuration: Configuration = Depends(Configuration.get),
    user: User = Depends(get_current_user),
) -> Response:
    database: Database = request.app.state.database
    cache: LRUCache[bytes] = request.app.state.cache
    provider = PollyProvider()

    if len(text) > configuration.maximum_characters_per_request:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Text length exceeds maximum of {configuration.maximum_characters_per_request} characters.",
        )

    key = provider.generate_cache(voice, text)
    cached_audio = await cache.get(key)

    if cached_audio is not None:
        return Response(
            content=cached_audio,
            media_type="audio/mpeg",
        )

    if text_type == TextTypeType.Ssml:
        try:
            ET.fromstring(text)
        except ET.ParseError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid SSML format: {str(e)}. Ensure your SSML is well-formed XML and includes required tags like <speak>.",
            )

    try:
        audio_bytes = await provider.synthesize_speech(
            voice,
            text,
            output_format='mp3',
            text_type=text_type,
        )

    except SSMLException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SSML synthesis error: {str(e)}. Please check your SSML content.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during speech synthesis: {str(e)}",
        )

    async with database.get_session() as session:
        session.add(
            Usage(
                user_id=user.id,
                characters_used=len(text),
            )
        )

        await session.commit()

    await cache.set(key, audio_bytes)
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
    )
