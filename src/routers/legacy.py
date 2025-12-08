import xml.etree.ElementTree as ET

from aiobotocore.response import StreamingBody
from fastapi import APIRouter, HTTPException, Request, Response, Depends, status

from src.api.auth import legacy_get_current_user
from src.cache import LRUCache
from src.clients.polly import PollyProvider, TextTypeType
from src.configuration import Configuration
from src.database import Database
from src.models.usage import Usage
from src.models.user import User
from src.types.aws import AwsStandardVoices

router = APIRouter(prefix="/legacy")


def cache_key(voice: AwsStandardVoices, text: str, text_type: TextTypeType) -> str:
    nvoice: str = voice.lower()
    text = text.lower()
    ntext_type: str = text_type.lower()

    return f"{nvoice}:{ntext_type}:{text}"


@router.get("/speech")
async def get_legacy_speech(
    request: Request,
    voice: AwsStandardVoices,
    text: str,
    text_type: TextTypeType = 'text',
    configuration: Configuration = Depends(Configuration.get),
    user: User = Depends(legacy_get_current_user),
) -> Response:
    database: Database = request.app.state.database
    cache: LRUCache[bytes] = request.app.state.cache
    provider = PollyProvider()

    if len(text) > configuration.maximum_characters_per_request:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Text length exceeds maximum of {configuration.maximum_characters_per_request} characters.",
        )

    key = cache_key(voice, text, text_type)
    cached_audio = await cache.get(key)

    if cached_audio is not None:
        return Response(
            content=cached_audio,
            media_type="audio/mpeg",
        )

    if text_type == 'ssml':
        try:
            ET.fromstring(text)
        except ET.ParseError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid SSML format: {str(e)}. Ensure your SSML is well-formed XML and includes required tags like <speak>.",
            )

    async with provider.get() as client:
        try:
            result = await client.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=voice,
                TextType=text_type,
            )

        except client.exceptions.InvalidSsmlException as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SSML synthesis error: {str(e)}. Please check your SSML content.",
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred during speech synthesis: {str(e)}",
            )

        # TODO: We should stream the response instead of loading it all into memory
        audio_stream: StreamingBody = result['AudioStream']

        async with database.get_session() as session:
            session.add(
                Usage(
                    user_id=user.id,
                    characters_used=len(text),
                )
            )

            await session.commit()

        return Response(
            content=await audio_stream.read(),
            media_type="audio/mpeg",
        )
