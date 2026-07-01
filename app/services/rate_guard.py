from hashlib import sha256

from redis.asyncio import Redis

from app.log import logger
from app.settings import settings


class RateGuardService:
    def __init__(self) -> None:
        self._redis: Redis | None = None

    @property
    def redis(self) -> Redis:
        if self._redis is None:
            self._redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    def build_key(self, namespace: str, *parts: object) -> str:
        raw_key = "|".join(str(part or "").strip() for part in parts)
        return f"rate-guard:{namespace}:{sha256(raw_key.encode('utf-8')).hexdigest()}"

    async def once_in_window(self, key: str, seconds: int) -> bool:
        if seconds <= 0:
            return True
        try:
            return bool(await self.redis.set(key, "1", ex=seconds, nx=True))
        except Exception as exc:
            logger.warning("rate guard dedup skipped: key={}, error={}", key, exc)
            return True

    async def hit_limit(self, key: str, limit: int, seconds: int) -> bool:
        if limit <= 0 or seconds <= 0:
            return False
        try:
            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.incr(key)
                pipe.expire(key, seconds)
                count, _ = await pipe.execute()
            return int(count) > limit
        except Exception as exc:
            logger.warning("rate guard limit skipped: key={}, error={}", key, exc)
            return False

    async def is_limited(self, key: str, limit: int) -> bool:
        if limit <= 0:
            return False
        try:
            count = await self.redis.get(key)
            return int(count or 0) >= limit
        except Exception as exc:
            logger.warning("rate guard limit check skipped: key={}, error={}", key, exc)
            return False

    async def clear(self, *keys: str) -> None:
        if not keys:
            return
        try:
            await self.redis.delete(*keys)
        except Exception as exc:
            logger.warning("rate guard clear skipped: keys={}, error={}", keys, exc)


rate_guard_service = RateGuardService()
