"""
Aegis Journal - Enterprise-Grade Concurrency-Safe Rate Limiter.
Provides tenant-aware, endpoint-aware sliding-window rate limiting with support for:
1. High-cost AI cognitive endpoints (stricter tier)
2. Standard transactional endpoints (standard tier)
3. In-memory concurrency-safe sliding log with automatic TTL eviction
4. Optional Redis/Memorystore distributed backend when REDIS_URL is provided
5. Telemetry sanitization (zero secrets, zero tokens, zero journal content logged)
"""
import os
import time
import hashlib
import logging
import asyncio
from typing import Optional, Tuple, Dict, List

logger = logging.getLogger("aegis_journal.rate_limiter")

# Configurable limits via Environment Variables
RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60"))
MAX_AI_REQUESTS_PER_WINDOW = int(os.environ.get("AI_RATE_LIMIT_PER_MINUTE", "20"))
MAX_STANDARD_REQUESTS_PER_WINDOW = int(os.environ.get("STANDARD_RATE_LIMIT_PER_MINUTE", "100"))
MAX_UNAUTH_REQUESTS_PER_WINDOW = int(os.environ.get("UNAUTH_RATE_LIMIT_PER_MINUTE", "30"))

REDIS_URL = os.environ.get("REDIS_URL", None)


class SlidingWindowRateLimiter:
    """
    Concurrency-safe Sliding Window Rate Limiter.
    Supports in-memory locking or Redis backend.
    """
    def __init__(self, window_seconds: int = RATE_LIMIT_WINDOW_SECONDS):
        self.window_seconds = window_seconds
        self._memory_store: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()
        self._redis_client = None
        self._is_distributed = False

        if REDIS_URL:
            try:
                import redis
                self._redis_client = redis.from_url(REDIS_URL, decode_responses=True)
                self._is_distributed = True
                logger.info("Distributed Redis rate limiter initialized.")
            except Exception as e:
                logger.warning(f"Redis initialization failed ({e}). Falling back to in-memory rate limiting.")
                self._redis_client = None
                self._is_distributed = False

    @property
    def is_distributed(self) -> bool:
        return self._is_distributed

    def sanitize_identifier(self, client_ip: str, auth_header: Optional[str] = None) -> str:
        """
        Derives a tenant key without exposing user tokens or private data.
        Returns a short SHA-256 pseudonym.
        """
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            if token:
                token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
                return f"tenant:{token_hash}"
        
        ip_hash = hashlib.sha256((client_ip or "unknown").encode("utf-8")).hexdigest()[:16]
        return f"ip:{ip_hash}"

    def get_tier_limit(self, path: str) -> Tuple[int, str]:
        """
        Returns (max_requests_allowed, tier_name) based on endpoint sensitivity.
        """
        # AI Cognitive Endpoints (expensive LLM operations)
        if (
            path.startswith("/api/journal/ask")
            or path.startswith("/api/journal/reflect")
            or path.startswith("/api/journal/chat")
            or path.startswith("/api/memory")
            or path.startswith("/api/insights")
            or path.startswith("/users/me/insights")
        ):
            return MAX_AI_REQUESTS_PER_WINDOW, "ai_intensive"
        
        # Standard Data Endpoints
        return MAX_STANDARD_REQUESTS_PER_WINDOW, "standard"

    async def check_rate_limit(
        self, 
        client_ip: str, 
        path: str, 
        auth_header: Optional[str] = None
    ) -> Tuple[bool, int, int]:
        """
        Checks if the request is allowed.
        Returns:
            (is_allowed: bool, retry_after_seconds: int, remaining_requests: int)
        """
        max_requests, tier = self.get_tier_limit(path)
        tenant_id = self.sanitize_identifier(client_ip, auth_header)
        key = f"ratelimit:{tier}:{tenant_id}"
        now = time.time()

        # 1. Distributed Redis Implementation
        if self._is_distributed and self._redis_client:
            try:
                pipe = self._redis_client.pipeline()
                window_start = now - self.window_seconds
                # Remove expired records
                pipe.zremrangebyscore(key, 0, window_start)
                # Count current records
                pipe.zcard(key)
                # Set key expiration
                pipe.expire(key, self.window_seconds + 5)
                _, count, _ = pipe.execute()

                if count >= max_requests:
                    # Get oldest timestamp in window to compute retry-after
                    oldest = self._redis_client.zrange(key, 0, 0, withscores=True)
                    retry_after = self.window_seconds
                    if oldest:
                        retry_after = max(1, int(self.window_seconds - (now - oldest[0][1])))
                    logger.warning(f"Rate limit exceeded for {tenant_id} on {tier} tier (limit: {max_requests})")
                    return False, retry_after, 0

                # Record request
                self._redis_client.zadd(key, {str(now): now})
                remaining = max(0, max_requests - count - 1)
                return True, 0, remaining
            except Exception as ex:
                logger.error(f"Redis rate check error: {ex}. Falling back to in-memory check.")

        # 2. Concurrency-Safe In-Memory Implementation
        async with self._lock:
            # Clean up window
            timestamps = self._memory_store.get(key, [])
            cutoff = now - self.window_seconds
            valid_timestamps = [t for t in timestamps if t > cutoff]

            if len(valid_timestamps) >= max_requests:
                oldest_ts = valid_timestamps[0]
                retry_after = max(1, int(self.window_seconds - (now - oldest_ts)))
                self._memory_store[key] = valid_timestamps
                logger.warning(f"Rate limit exceeded for {tenant_id} on {tier} tier (limit: {max_requests})")
                return False, retry_after, 0

            # Record timestamp
            valid_timestamps.append(now)
            self._memory_store[key] = valid_timestamps

            # Periodic prune of all keys if memory map grows large
            if len(self._memory_store) > 1000:
                self._prune_stale_keys(now)

            remaining = max(0, max_requests - len(valid_timestamps))
            return True, 0, remaining

    def _prune_stale_keys(self, now: float):
        """Removes expired entries to avoid memory growth."""
        cutoff = now - self.window_seconds
        stale_keys = [
            k for k, timestamps in self._memory_store.items() 
            if not timestamps or timestamps[-1] <= cutoff
        ]
        for k in stale_keys:
            del self._memory_store[k]

    def reset_state(self):
        """Clears all in-memory rate limiting records (useful for test isolation)."""
        self._memory_store.clear()


# Global Limiter Instance
limiter = SlidingWindowRateLimiter()
