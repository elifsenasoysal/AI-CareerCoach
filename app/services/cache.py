import json
import logging
import time
from typing import Any, Optional
# pyrefly: ignore [missing-import]
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self.in_memory_cache: dict = {}
        self.redis_available = False
        self.last_check_time = 0.0
        self.check_cooldown = 60.0  # seconds

        # Attempt to initialize Redis client
        try:
            self.redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            self.redis_available = True
            logger.info("Redis cache client configured.")
        except Exception as e:
            logger.warning(f"Redis client configuration failed: {e}. Falling back to in-memory caching.")
            self.redis_available = False

    async def _ping_redis(self) -> bool:
        if self.redis_client is None:
            return False
        
        current_time = time.time()
        
        # If Redis is known to be unavailable, prevent ping storm and respect cooldown
        if not self.redis_available:
            if current_time - self.last_check_time < self.check_cooldown:
                return False
        
        try:
            self.last_check_time = current_time
            await self.redis_client.ping()
            if not self.redis_available:
                logger.info("Redis server is back online! Switching back to Redis cache.")
                self.redis_available = True
            return True
        except Exception as e:
            if self.redis_available:
                logger.warning(f"Redis server has become unreachable ({e}). Using in-memory caching fallback.")
                self.redis_available = False
            return False

    async def get(self, key: str) -> Optional[Any]:
        if await self._ping_redis():
            try:
                val = await self.redis_client.get(key)
                if val:
                    return json.loads(val)
            except Exception as e:
                logger.error(f"Redis GET failed for key {key}: {e}")
        
        # Fallback to in-memory cache
        logger.debug(f"Retrieving key '{key}' from in-memory cache.")
        return self.in_memory_cache.get(key)

    async def set(self, key: str, value: Any, expire: int = None) -> None:
        if expire is None:
            expire = settings.CACHE_EXPIRE_SECONDS

        serialized_value = json.dumps(value)

        if await self._ping_redis():
            try:
                await self.redis_client.set(key, serialized_value, ex=expire)
                return
            except Exception as e:
                logger.error(f"Redis SET failed for key {key}: {e}")

        # Fallback to in-memory cache
        logger.debug(f"Storing key '{key}' in in-memory cache.")
        self.in_memory_cache[key] = value

# Singleton instance
cache_service = CacheService()
