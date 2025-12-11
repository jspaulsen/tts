from collections.abc import AsyncGenerator
from typing import AsyncContextManager, cast
from contextlib import asynccontextmanager

import aioboto3
from aiobotocore.config import AioConfig
from types_aiobotocore_polly import PollyClient
from types_aiobotocore_polly.literals import VoiceIdType, TextTypeType  # pylint: disable=unused-import


class PollyProvider:
    def __init__(self, region_name: str = 'us-west-2'):
        self.region_name = region_name
        self.session = aioboto3.Session()
        self.config = AioConfig(
            connect_timeout=10,
            read_timeout=10,
        )

    @asynccontextmanager
    async def get(self) -> AsyncGenerator[PollyClient, None]:
        async with cast(
            AsyncContextManager[PollyClient],
            self.session.client("polly", region_name=self.region_name, config=self.config)
        ) as client:
            yield client
