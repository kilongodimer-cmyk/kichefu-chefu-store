import asyncio
import json
from typing import Any, Sequence

from redis.asyncio import Redis

from ..core.config import get_settings


class RedisClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._url = settings.redis_url
        self._client = Redis.from_url(self._url, decode_responses=True)

    @property
    def client(self) -> Redis:
        return self._client

    async def ping(self) -> bool:
        return bool(await self._client.ping())

    async def publish(self, channel: str, message: Any) -> None:
        await self._client.publish(channel, message)

    async def publish_json(self, channel: str, payload: dict[str, Any]) -> None:
        await self.publish(channel, json.dumps(payload, default=str))

    async def push_stream(
        self,
        stream: str,
        payload: dict[str, Any],
        *,
        maxlen: int = 500,
    ) -> None:
        await self._client.xadd(
            stream,
            {"payload": json.dumps(payload, default=str)},
            maxlen=maxlen,
            approximate=True,
        )

    async def subscribe(self, channels: Sequence[str] | str):
        pubsub = self._client.pubsub()
        if isinstance(channels, str):
            await pubsub.subscribe(channels)
        else:
            await pubsub.subscribe(*channels)
        return pubsub


redis_client = RedisClient()


async def ensure_redis_connection(timeout: float = 5.0) -> None:
    try:
        await asyncio.wait_for(redis_client.ping(), timeout=timeout)
    except asyncio.TimeoutError as exc:
        raise RuntimeError("Redis connection timeout") from exc
