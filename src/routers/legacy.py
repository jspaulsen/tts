import xml.etree.ElementTree as ET

from fastapi import APIRouter, HTTPException, Response, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.clients.polly import PollyProvider, TextTypeType
from src.configuration import Configuration
from src.types.aws import AwsStandardVoices

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
    voice: AwsStandardVoices,
    text: str,
    # _token: str = Depends(get_authorization_token)
    token: str | None = None,
    text_type: TextTypeType = 'text',
    configuration: Configuration = Depends(Configuration.get)
) -> Response:
    provider = PollyProvider()

    if token != configuration.api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token",
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

        audio_stream = result['AudioStream']
        audio_bytes = await audio_stream.read()

        return Response(content=audio_bytes, media_type="audio/mpeg")
