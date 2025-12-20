import asyncio
from contextlib import closing
from enum import StrEnum

import boto3

from src.types.aws import AwsStandardVoices


class SSMLException(Exception):
    pass


class TextTypeType(StrEnum):
    Text = 'text'
    Ssml = 'ssml'


class PollyProvider:
    def __init__(self, region_name: str = 'us-west-2'):
        self.region_name = region_name
        self.session = boto3.Session()

    def _synthesize(
        self,
        text: str,
        voice_id: AwsStandardVoices,
        output_format: str = 'mp3',
        text_type: TextTypeType = TextTypeType.Text,
    ) -> bytes:
        polly_client = self.session.client('polly', region_name=self.region_name)

        try:
            response = polly_client.synthesize_speech(
                Text=text,
                VoiceId=voice_id,
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
        text: str,
        voice_id: AwsStandardVoices,
        output_format: str = 'mp3',
        text_type: TextTypeType = TextTypeType.Text,
    ) -> bytes:
        loop = asyncio.get_running_loop()

        return await loop.run_in_executor(
            None,
            self._synthesize,
            text,
            voice_id,
            output_format,
            text_type
        )
