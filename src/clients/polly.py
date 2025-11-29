from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, AsyncContextManager, cast
from contextlib import asynccontextmanager

import aioboto3
from types_aiobotocore_polly import PollyClient

if TYPE_CHECKING:
    from types_aiobotocore_polly.literals import VoiceIdType


class PollyProvider:
    def __init__(self, region_name: str = 'us-west-2'):
        self.region_name = region_name
        self.session = aioboto3.Session()

    @asynccontextmanager
    async def get(self) -> AsyncGenerator[PollyClient, None]:
        async with cast(
            AsyncContextManager[PollyClient],
            self.session.client("polly", region_name=self.region_name)
        ) as client:
            yield client
