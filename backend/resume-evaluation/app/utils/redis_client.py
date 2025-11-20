"""
Redis client utilities for the application
"""
import redis.asyncio as redis
import json
from typing import Optional, Any, Dict
from contextlib import asynccontextmanager
from uuid import UUID
from datetime import datetime, date
from ..config import settings


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles UUID and datetime objects"""

    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


class RedisClient:
    """Redis client wrapper for async operations"""

    def __init__(self):
        self.client: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis"""
        if not self.client:
            self.client = redis.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                decode_responses=settings.REDIS_DECODE_RESPONSES,
                encoding="utf-8"
            )
        return self.client

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def ping(self) -> bool:
        """Test Redis connection"""
        if not self.client:
            await self.connect()
        try:
            return await self.client.ping()
        except Exception:
            return False

    # Token Blacklisting Methods
    async def blacklist_token(self, jti: str, user_id: str, expires_at: float) -> bool:
        """Add token to blacklist with expiration"""
        if not self.client:
            await self.connect()

        key = f"blacklist:token:{jti}"
        data = {
            "jti": jti,
            "user_id": user_id,
            "expires_at": expires_at
        }

        # Calculate TTL in seconds from now
        import time
        ttl = max(1, int(expires_at - time.time()))

        # Store with TTL
        await self.client.setex(key, ttl, json.dumps(data, cls=CustomJSONEncoder))
        return True

    async def is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted"""
        if not self.client:
            await self.connect()

        key = f"blacklist:token:{jti}"
        exists = await self.client.exists(key)
        return bool(exists)

    # Refresh Token Methods
    async def store_refresh_token(self, token: str, user_id: str, expires_in_days: int = 7) -> bool:
        """Store refresh token with expiration"""
        if not self.client:
            await self.connect()

        key = f"refresh:{token}"
        data = {
            "token": token,
            "user_id": user_id
        }

        ttl = expires_in_days * 24 * 60 * 60  # Convert days to seconds
        await self.client.setex(key, ttl, json.dumps(data, cls=CustomJSONEncoder))
        return True

    async def validate_refresh_token(self, token: str) -> Optional[str]:
        """Validate refresh token and return user_id if valid"""
        if not self.client:
            await self.connect()

        key = f"refresh:{token}"
        data = await self.client.get(key)

        if not data:
            return None

        try:
            token_data = json.loads(data)
            return token_data["user_id"]
        except (json.JSONDecodeError, KeyError):
            return None

    async def revoke_refresh_token(self, token: str) -> bool:
        """Revoke refresh token"""
        if not self.client:
            await self.connect()

        key = f"refresh:{token}"
        result = await self.client.delete(key)
        return result > 0

    # Rate Limiting Methods
    async def check_rate_limit(self, identifier: str, limit: int, window: int) -> Dict[str, Any]:
        """Check and update rate limit for an identifier"""
        if not self.client:
            await self.connect()

        key = f"ratelimit:{identifier}"
        current_time = await self.client.time()
        current_timestamp = current_time[0]

        # Check if key exists
        exists = await self.client.exists(key)

        if not exists:
            # First request, set initial count
            await self.client.setex(key, window, "1")
            return {"allowed": True, "remaining": limit - 1, "reset": current_timestamp + window}

        # Increment counter
        count = await self.client.incr(key)
        ttl = await self.client.ttl(key)

        if count > limit:
            return {"allowed": False, "remaining": 0, "reset": current_timestamp + ttl}

        return {"allowed": True, "remaining": limit - count + 1, "reset": current_timestamp + ttl}

    # Caching Methods
    async def cache_get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        if not self.client:
            await self.connect()
        return await self.client.get(key)

    async def cache_set(self, key: str, value: str, ttl: int = None) -> bool:
        """Set value in cache with optional TTL"""
        if not self.client:
            await self.connect()

        if ttl:
            await self.client.setex(key, ttl, value)
        else:
            await self.client.set(key, value)
        return True

    async def cache_set_json(self, key: str, data: Any, ttl: int = None) -> bool:
        """Set structured data in cache as JSON with UUID support"""
        if not self.client:
            await self.connect()

        json_str = json.dumps(data, cls=CustomJSONEncoder)

        if ttl:
            await self.client.setex(key, ttl, json_str)
        else:
            await self.client.set(key, json_str)
        return True

    async def cache_delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.client:
            await self.connect()
        result = await self.client.delete(key)
        return result > 0

    async def cache_exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.client:
            await self.connect()
        exists = await self.client.exists(key)
        return bool(exists)


# Global Redis client instance
redis_client = RedisClient()


@asynccontextmanager
async def get_redis_client():
    """Dependency to get Redis client"""
    await redis_client.connect()
    try:
        yield redis_client
    finally:
        # Note: We don't disconnect here as Redis client is meant to be reused
        pass
