from hashlib import sha256

from redis.asyncio import Redis

from app.log import logger
from app.settings import settings


class RateGuardUnavailable(RuntimeError):
    pass


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

    async def hit_limit(self, key: str, limit: int, seconds: int, *, strict: bool = False) -> bool:
        if limit <= 0 or seconds <= 0:
            return False
        try:
            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.incr(key)
                pipe.expire(key, seconds)
                count, _ = await pipe.execute()
            return int(count) >= limit
        except Exception as exc:
            if strict:
                raise RateGuardUnavailable from exc
            logger.warning("rate guard limit skipped: key={}, error={}", key, exc)
            return False

    async def hit_window_limit(self, key: str, limit: int, seconds: int) -> bool:
        if limit <= 0 or seconds <= 0:
            return False
        try:
            count = await self.redis.incr(key)
            if count == 1:
                await self.redis.expire(key, seconds)
            return int(count) > limit
        except Exception as exc:
            logger.warning("rate guard window limit skipped: key={}, error={}", key, exc)
            return False

    async def is_limited(self, key: str, limit: int, *, strict: bool = False) -> bool:
        if limit <= 0:
            return False
        try:
            count = await self.redis.get(key)
            return int(count or 0) >= limit
        except Exception as exc:
            if strict:
                raise RateGuardUnavailable from exc
            logger.warning("rate guard limit check skipped: key={}, error={}", key, exc)
            return False

    async def exists(self, key: str, *, strict: bool = False) -> bool:
        try:
            return bool(await self.redis.exists(key))
        except Exception as exc:
            if strict:
                raise RateGuardUnavailable from exc
            logger.warning("rate guard exists check skipped: key={}, error={}", key, exc)
            return False

    async def block(self, key: str, seconds: int, *, strict: bool = False) -> None:
        if seconds <= 0:
            return
        try:
            await self.redis.set(key, "1", ex=seconds)
        except Exception as exc:
            if strict:
                raise RateGuardUnavailable from exc
            logger.warning("rate guard block skipped: key={}, error={}", key, exc)

    async def clear(self, *keys: str, strict: bool = False) -> None:
        if not keys:
            return
        try:
            await self.redis.delete(*keys)
        except Exception as exc:
            if strict:
                raise RateGuardUnavailable from exc
            logger.warning("rate guard clear skipped: keys={}, error={}", keys, exc)


rate_guard_service = RateGuardService()
