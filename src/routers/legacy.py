from fastapi import APIRouter, HTTPException, Response, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.clients.polly import PollyProvider, VoiceIdType
from src.configuration import Configuration


router = APIRouter(prefix="/legacy")
security = HTTPBearer()


async def get_authorization_token(
    configuration: Configuration = Depends(Configuration.get),
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    token = credentials.credentials

    if token != configuration.api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token",
        )

    return token



@router.get("/speech")
async def get_legacy_speech(
    voice: VoiceIdType,
    text: str,
    # _token: str = Depends(get_authorization_token)
    token: str,
    configuration: Configuration = Depends(Configuration.get)
) -> Response:
    provider = PollyProvider()

    if token != configuration.api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token",
        )

    async with provider.get() as client:
        result = await client.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId=voice
        )

        audio_stream = result['AudioStream']
        audio_bytes = await audio_stream.read()

        return Response(content=audio_bytes, media_type="audio/mpeg")
