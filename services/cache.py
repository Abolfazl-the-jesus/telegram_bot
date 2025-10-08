import os
import asyncio
from typing import Optional
from redis.asyncio import Redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_redis: Optional[Redis] = None


def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    return _redis


async def get(key: str) -> Optional[str]:
    return await get_redis().get(key)


async def set(key: str, value: str, ex: Optional[int] = None) -> None:
    await get_redis().set(key, value, ex=ex)


async def incr(key: str) -> int:
    return await get_redis().incr(key)


async def decr(key: str) -> int:
    return await get_redis().decr(key)


async def delete(key: str) -> None:
    await get_redis().delete(key)


async def lpush(key: str, *values: str) -> int:
    return await get_redis().lpush(key, *values)


async def brpop(key: str, timeout: int = 0):
    return await get_redis().brpop(key, timeout=timeout)


async def rate_limit_check(key: str, limit: int, period_seconds: int) -> bool:
    """
    Sliding window via INCR with TTL.
    Returns True if allowed, False if over limit.
    """
    r = get_redis()
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, period_seconds)
    count, _ = await pipe.execute()
    return int(count) <= limit


