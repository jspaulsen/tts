import asyncio
from dataclasses import dataclass


@dataclass
class CacheEntry[T]:
    value: T
    timestamp: float


class LRUCache[T]:
    def __init__(
        self,
        max_size: int = 128,
    ) -> None:
        self.max_size = max_size
        self.cache: dict[str, CacheEntry[T]] = {}
        self.lock = asyncio.Lock()

    async def get(self, key: str) -> T | None:
        async with self.lock:
            entry = self.cache.get(key)

            if entry:
                entry.timestamp = (
                    asyncio
                        .get_event_loop()
                        .time()
                )

            return entry.value if entry else None

    async def find_oldest_key(self) -> str | None:
        async with self.lock:
            if not self.cache:
                return None

            oldest_key = min(
                self.cache.keys(),
                key=lambda k: self.cache[k].timestamp,
            )

            return oldest_key

    async def set(self, key: str, value: T) -> None:
        async with self.lock:
            if len(self.cache) >= self.max_size:
                oldest_key = await self.find_oldest_key()

                if oldest_key is not None:
                    del self.cache[oldest_key]

            self.cache[key] = CacheEntry(
                value=value,
                timestamp=(
                    asyncio
                        .get_event_loop()
                        .time()
                ),
            )
