import asyncio
from contextlib import closing
from enum import StrEnum
from typing import get_args

import boto3
from botocore.config import Config

from src.tts.provider import TTSProvider
from src.types.aws import AWSStandardVoices


class SSMLException(Exception):
    pass


class TextTypeType(StrEnum):
    Text = 'text'
    Ssml = 'ssml'


class PollyProvider(TTSProvider[AWSStandardVoices]):
    def __init__(self, region_name: str = 'us-west-2') -> None:
        self.region_name = region_name
        self.config = Config(
            read_timeout=5,  # Force the socket to raise an exception if no data is received within 5 seconds.
            connect_timeout=5,  # Fail fast if the initial handshake takes too long.
            retries={
                'max_attempts': 2,
                'mode': 'standard'
            },

            # Ask the OS to send "Are you there?" packets to keep the NAT entry active.
            # tcp_keepalive=True
        )

        self.session = boto3.Session()

    @property
    def can_cache(self) -> bool:
        return True

    @property
    def supports_ssml(self) -> bool:
        return True

    @property
    def has_financial_cost(self) -> bool:
        return True

    def _synthesize(
        self,
        voice: AWSStandardVoices,
        text: str,
        output_format: str = 'mp3',
        text_type: TextTypeType = TextTypeType.Text,
    ) -> bytes:
        polly_client = self.session.client(
            'polly',
            region_name=self.region_name,
            config=self.config,
        )

        try:
            response = polly_client.synthesize_speech(
                Text=text,
                VoiceId=voice,
                OutputFormat=output_format,
                TextType=text_type,
            )
        except polly_client.exceptions.InvalidSsmlException as e:
            raise SSMLException(str(e)) from e

        with closing(response['AudioStream']) as stream:
            result = stream.read()

        return result

    async def synthesize_speech(
        self,
        voice: AWSStandardVoices,
        text: str,
        **kwargs,
    ) -> bytes:
        output_format: str = kwargs.get('output_format', 'mp3')
        text_type: TextTypeType = kwargs.get('text_type', TextTypeType.Text)
        loop = asyncio.get_running_loop()

        return await loop.run_in_executor(
            None,
            self._synthesize,
            voice,
            text,
            output_format,
            text_type,
        )

    @staticmethod
    def voices() -> list[str]:
        return list(get_args(AWSStandardVoices))
