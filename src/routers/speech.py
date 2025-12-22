from typing import get_args
import xml.etree.ElementTree as ET

from fastapi import APIRouter, HTTPException, Request, Response, Depends, status

from src.api.auth import get_current_user, legacy_get_current_user
from src.cache import LRUCache
from src.clients.polly import PollyProvider, SSMLException, TextTypeType
from src.configuration import Configuration
from src.database import Database
from src.models.usage import Usage
from src.models.user import User
from src.types.aws import AwsStandardVoices
from src.types.kokoro import KokoroVoices


# Extend this as we add more providers
TypeSupportedVoices = AwsStandardVoices | KokoroVoices

router = APIRouter(prefix="/v1")


# TODO: Only select providers support SSML.
# We probably need a better mechanism to handle this.
# Maybe a protocol? An abstract base class?


# Maybe we want to call specific vendors? I.E>., /v1/speech/polly, /v1/speech/kokoro, etc.
@router.post("/speech")
async def get_speech(
    request: Request,
    voice: AwsStandardVoices,
    text: str,
    # text_type: TextTypeType = TextTypeType.Text,
    configuration: Configuration = Depends(Configuration.get),
    user: User = Depends(get_current_user),
) -> Response:
    database: Database = request.app.state.database
    cache: LRUCache[bytes] = request.app.state.cache

    # We need to route requests based on the speaker

    raise NotImplementedError("This endpoint is under construction.")
    #
    # provider = PollyProvider()

    # if len(text) > configuration.maximum_characters_per_request:
    #     raise HTTPException(
    #         status_code=status.HTTP_413_CONTENT_TOO_LARGE,
    #         detail=f"Text length exceeds maximum of {configuration.maximum_characters_per_request} characters.",
    #     )

    # key = f"{voice.lower()}:{text_type.lower()}:{text.strip().lower()}"
    # cached_audio = await cache.get(key)

    # if cached_audio is not None:
    #     return Response(
    #         content=cached_audio,
    #         media_type="audio/mpeg",
    #     )

    # if text_type == 'ssml':
    #     try:
    #         ET.fromstring(text)
    #     except ET.ParseError as e:
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail=f"Invalid SSML format: {str(e)}. Ensure your SSML is well-formed XML and includes required tags like <speak>.",
    #         )

    # try:
    #     audio_stream = await provider.synthesize_speech(
    #         voice=voice,
    #         text=text,
    #         text_type=text_type,
    #     )
    # except SSMLException as e:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail=f"SSML Error: {str(e)}",
    #     )

    # audio_bytes = audio_stream.read()

    # await cache.set(key, audio_bytes)

    # # Log usage
    # usage_record = Usage(
    #     user_id=user.id,
    #     characters_used=len(text),
    # )

    # async with database.get_session() as session:
    #     session.add(usage_record)
    #     await session.commit()

    # return Response(
    #     content=audio_bytes,
    #     media_type="audio/mpeg",
    # )
