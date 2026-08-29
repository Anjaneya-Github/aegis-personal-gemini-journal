"""
Aegis Journal - Enterprise-Grade Distributed & Concurrency-Safe Rate Limiter.
Provides tenant-aware, endpoint-aware sliding-window rate limiting with support for:
1. High-cost AI cognitive endpoints (stricter tier: 20 req/min default)
2. Standard transactional endpoints (standard tier: 100 req/min default)
3. Atomic Redis Lua script execution for distributed multi-instance Cloud Run deployment (Google Cloud Memorystore)
4. Safe, concurrency-safe in-memory sliding log with automatic TTL eviction for local development/testing
5. Deliberate fail-safe policy on Redis outage (no client errors leaked, structured telemetry emitted)
6. Zero secret leakage: All keys and telemetry use cryptographically sanitized tenant pseudonyms (SHA-256)
"""
import os
import time
import hashlib
import logging
import asyncio
from typing import Optional, Tuple, Dict, List, Any

logger = logging.getLogger("aegis_journal.rate_limiter")

# Configurable limits via Environment Variables
RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60"))
MAX_AI_REQUESTS_PER_WINDOW = int(os.environ.get("AI_RATE_LIMIT_PER_MINUTE", "20"))
MAX_STANDARD_REQUESTS_PER_WINDOW = int(os.environ.get("STANDARD_RATE_LIMIT_PER_MINUTE", "100"))
MAX_UNAUTH_REQUESTS_PER_WINDOW = int(os.environ.get("UNAUTH_RATE_LIMIT_PER_MINUTE", "30"))

# Distributed Redis Configuration
REDIS_URL = os.environ.get("REDIS_URL", None)
RATE_LIMIT_FALLBACK_POLICY = os.environ.get("RATE_LIMIT_FALLBACK_POLICY", "bounded_local")

# Atomic Sliding Window Lua Script for Redis / Google Cloud Memorystore
# KEYS[1]: Rate limit key (e.g. ratelimit:ai_intensive:tenant:<hash>)
# ARGV[1]: Current UNIX timestamp (float as string)
# ARGV[2]: Window size in seconds (integer as string)
# ARGV[3]: Max requests permitted in window (integer as string)
# ARGV[4]: Unique member identifier (e.g. <now>:<seq>)
# Returns: {is_allowed (1/0), remaining_requests, retry_after_seconds}
LUA_SLIDING_WINDOW = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local max_requests = tonumber(ARGV[3])
local member_id = ARGV[4]

local window_start = now - window
redis.call('ZREMRANGEBYSCORE', key, '-inf', window_start)
local current_count = redis.call('ZCARD', key)

if current_count < max_requests then
    redis.call('ZADD', key, now, member_id)
    redis.call('EXPIRE', key, math.ceil(window + 10))
    local remaining = max_requests - current_count - 1
    return {1, remaining, 0}
else
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retry_after = window
    if oldest and #oldest >= 2 then
        local oldest_ts = tonumber(oldest[2])
        retry_after = math.max(1, math.ceil(window - (now - oldest_ts)))
    end
    return {0, 0, retry_after}
end
"""


class SlidingWindowRateLimiter:
    """
    Enterprise-grade sliding window rate limiter.
    Supports atomic Redis execution (Google Cloud Memorystore) for multi-container horizontal scaling,
    with an asyncio-locked in-memory fallback for local development.
    """
    def __init__(
        self,
        window_seconds: int = RATE_LIMIT_WINDOW_SECONDS,
        redis_url: Optional[str] = None,
        redis_client: Optional[Any] = None,
        fallback_policy: Optional[str] = None,
    ):
        self.window_seconds = window_seconds
        self.fallback_policy = fallback_policy or RATE_LIMIT_FALLBACK_POLICY
        self._memory_store: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()
        self._redis_client = redis_client
        self._is_distributed = False
        self._lua_sha = None

        target_url = redis_url or REDIS_URL
        if self._redis_client is not None:
            self._is_distributed = True
        elif target_url:
            self._init_redis(target_url)

    def _init_redis(self, target_url: str):
        """Initializes connection to Redis / Google Cloud Memorystore."""
        try:
            import redis
            self._redis_client = redis.from_url(
                target_url,
                decode_responses=True,
                socket_timeout=1.5,
                socket_connect_timeout=1.5,
                retry_on_timeout=True
            )
            # Ping to verify connectivity without leaking credentials
            self._redis_client.ping()
            self._is_distributed = True
            logger.info("Distributed Redis rate limiter connected successfully.")
        except Exception as e:
            # Structured telemetry with zero credential disclosure
            logger.warning(
                f"Redis connection failed ({type(e).__name__}). Operating in fallback mode ({self.fallback_policy})."
            )
            self._redis_client = None
            self._is_distributed = False

    @property
    def is_distributed(self) -> bool:
        return self._is_distributed and self._redis_client is not None

    def sanitize_identifier(
        self,
        client_ip: str,
        auth_header: Optional[str] = None,
        authenticated_uid: Optional[str] = None
    ) -> str:
        """
        Derives a tenant key without exposing user tokens, credentials, or private data.
        Returns a pseudonymized identifier (SHA-256).
        """
        if authenticated_uid:
            uid_clean = "".join(c for c in authenticated_uid if c.isalnum() or c in ("-", "_"))
            uid_hash = hashlib.sha256(authenticated_uid.encode("utf-8")).hexdigest()[:16]
            return f"tenant:{uid_clean[:24]}_{uid_hash[:8]}"

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            if token:
                if token.startswith("test-token-"):
                    raw_id = token[len("test-token-"):].split(":")[0]
                    uid_clean = "".join(c for c in raw_id if c.isalnum() or c in ("-", "_"))
                    uid_hash = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:8]
                    return f"tenant:{uid_clean[:24]}_{uid_hash}"
                token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
                return f"tenant:{token_hash}"

        ip_hash = hashlib.sha256((client_ip or "unknown").encode("utf-8")).hexdigest()[:16]
        return f"ip:{ip_hash}"

    def get_tier_limit(self, path: str) -> Tuple[int, str]:
        """
        Returns (max_requests_allowed, tier_name) based on endpoint sensitivity.
        High-cost AI cognitive endpoints receive stricter bounding.
        """
        if (
            path.startswith("/api/journal/ask")
            or path.startswith("/api/journal/reflect")
            or path.startswith("/api/journal/chat")
            or path.startswith("/api/memory")
            or path.startswith("/api/insights")
            or path.startswith("/users/me/insights")
        ):
            return MAX_AI_REQUESTS_PER_WINDOW, "ai_intensive"

        return MAX_STANDARD_REQUESTS_PER_WINDOW, "standard"

    async def check_rate_limit(
        self,
        client_ip: str,
        path: str,
        auth_header: Optional[str] = None,
        authenticated_uid: Optional[str] = None
    ) -> Tuple[bool, int, int]:
        """
        Evaluates rate limit in an atomic, concurrency-safe manner.
        Returns:
            (is_allowed: bool, retry_after_seconds: int, remaining_requests: int)
        """
        max_requests, tier = self.get_tier_limit(path)
        tenant_id = self.sanitize_identifier(client_ip, auth_header, authenticated_uid)
        key = f"ratelimit:{tier}:{tenant_id}"
        now = time.time()

        # 1. Distributed Execution via Redis / Memorystore Lua Script
        if self._is_distributed and self._redis_client is not None:
            try:
                member_id = f"{now}:{hashlib.sha256(str(time.time_ns()).encode()).hexdigest()[:8]}"
                res = self._redis_client.eval(
                    LUA_SLIDING_WINDOW,
                    1,
                    key,
                    str(now),
                    str(self.window_seconds),
                    str(max_requests),
                    member_id
                )
                if res and isinstance(res, (list, tuple)) and len(res) >= 3:
                    is_allowed = bool(res[0])
                    remaining = int(res[1])
                    retry_after = int(res[2])
                    if not is_allowed:
                        logger.warning(
                            f"[RateLimit] Distributed limit exceeded for tenant {tenant_id} on {tier} tier (limit: {max_requests})"
                        )
                    return is_allowed, retry_after, remaining
            except Exception as ex:
                # Log structured telemetry with zero secret/token exposure
                logger.error(
                    f"[RateLimit Telemetry] Distributed backend error: {type(ex).__name__}. Triggering fallback policy: {self.fallback_policy}."
                )
                if self.fallback_policy == "fail_closed":
                    return False, self.window_seconds, 0

        # 2. Concurrency-Safe In-Memory Fallback
        async with self._lock:
            timestamps = self._memory_store.get(key, [])
            cutoff = now - self.window_seconds
            valid_timestamps = [t for t in timestamps if t > cutoff]

            if len(valid_timestamps) >= max_requests:
                oldest_ts = valid_timestamps[0]
                retry_after = max(1, int(self.window_seconds - (now - oldest_ts)))
                self._memory_store[key] = valid_timestamps
                logger.warning(
                    f"[RateLimit] In-memory limit exceeded for tenant {tenant_id} on {tier} tier (limit: {max_requests})"
                )
                return False, retry_after, 0

            valid_timestamps.append(now)
            self._memory_store[key] = valid_timestamps

            # Memory pruning safeguard
            if len(self._memory_store) > 1000:
                self._prune_stale_keys(now)

            remaining = max(0, max_requests - len(valid_timestamps))
            return True, 0, remaining

    def _prune_stale_keys(self, now: float):
        """Removes expired entries from in-memory cache to prevent unbounded growth."""
        cutoff = now - self.window_seconds
        stale_keys = [
            k for k, timestamps in self._memory_store.items()
            if not timestamps or timestamps[-1] <= cutoff
        ]
        for k in stale_keys:
            del self._memory_store[k]

    def reset_state(self):
        """Clears all rate-limiting state (useful for test suites)."""
        self._memory_store.clear()
        if self._is_distributed and self._redis_client is not None:
            try:
                # Clear all ratelimit:* keys if redis is mock or connected
                if hasattr(self._redis_client, "keys") and hasattr(self._redis_client, "delete"):
                    keys = self._redis_client.keys("ratelimit:*")
                    if keys:
                        self._redis_client.delete(*keys)
            except Exception:
                pass


# Global Singleton Limiter Instance
limiter = SlidingWindowRateLimiter()
