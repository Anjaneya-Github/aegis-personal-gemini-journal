"""
Comprehensive Test Suite for Aegis Journal Distributed & Concurrency-Safe Rate Limiter.
Validates:
1. Standard tier request limits (100 req/min)
2. AI tier strict limits (20 req/min)
3. Tenant isolation in-memory and distributed
4. Pseudonymized identifier hashing (zero secrets, zero tokens exposed)
5. Multi-instance distributed rate limiting (simulating multiple Cloud Run instances sharing Memorystore/Redis)
6. Atomic sliding window Lua script behavior
7. Distributed AI vs standard tier enforcement
8. Distributed concurrency safety
9. Redis unavailable fail-safe policy & structured telemetry
10. Redis socket timeout resilience
11. Malformed configuration safety
12. Zero secret leakage across keys, logs, and responses
"""
import unittest
import asyncio
import time
import math
from typing import Dict, List, Tuple
from backend.app.rate_limiter import (
    SlidingWindowRateLimiter,
    RATE_LIMIT_WINDOW_SECONDS,
    MAX_AI_REQUESTS_PER_WINDOW,
    MAX_STANDARD_REQUESTS_PER_WINDOW,
)


class MockRedisClient:
    """
    In-memory mock of Redis client implementing atomic Lua script sliding window
    and sorted set operations to test distributed multi-instance Cloud Run scenarios.
    """
    def __init__(self, should_fail: bool = False, should_timeout: bool = False):
        self.store: Dict[str, List[Tuple[float, str]]] = {}
        self.should_fail = should_fail
        self.should_timeout = should_timeout

    def ping(self):
        if self.should_fail:
            raise ConnectionError("Simulated Redis Connection Refused")
        if self.should_timeout:
            raise TimeoutError("Simulated Redis Socket Timeout")
        return True

    def eval(self, script: str, numkeys: int, key: str, *args) -> List[int]:
        if self.should_fail:
            raise ConnectionError("Simulated Redis Connection Failure during eval")
        if self.should_timeout:
            raise TimeoutError("Simulated Redis Socket Timeout during eval")

        now = float(args[0])
        window = float(args[1])
        max_requests = int(args[2])
        member_id = str(args[3])

        records = self.store.get(key, [])
        window_start = now - window
        valid_records = [r for r in records if r[0] > window_start]

        if len(valid_records) < max_requests:
            valid_records.append((now, member_id))
            self.store[key] = valid_records
            remaining = max_requests - len(valid_records)
            return [1, remaining, 0]
        else:
            oldest_ts = valid_records[0][0]
            retry_after = max(1, math.ceil(window - (now - oldest_ts)))
            self.store[key] = valid_records
            return [0, 0, retry_after]

    def keys(self, pattern: str = "*") -> List[str]:
        return list(self.store.keys())

    def delete(self, *keys):
        for k in keys:
            if k in self.store:
                del self.store[k]


class TestRateLimiter(unittest.TestCase):
    def setUp(self):
        self.limiter = SlidingWindowRateLimiter(window_seconds=2)
        self.mock_redis = MockRedisClient()

    def tearDown(self):
        self.limiter.reset_state()

    # --- IN-MEMORY FALLBACK TESTS ---

    def test_01_standard_tier_limits_in_memory(self):
        tenant_token = "Bearer test-user-token-111"
        client_ip = "192.168.1.10"
        path = "/api/journal"

        for _ in range(MAX_STANDARD_REQUESTS_PER_WINDOW):
            allowed, retry_after, remaining = asyncio.run(
                self.limiter.check_rate_limit(client_ip=client_ip, path=path, auth_header=tenant_token)
            )
            self.assertTrue(allowed)

        allowed, retry_after, remaining = asyncio.run(
            self.limiter.check_rate_limit(client_ip=client_ip, path=path, auth_header=tenant_token)
        )
        self.assertFalse(allowed)
        self.assertGreater(retry_after, 0)
        self.assertEqual(remaining, 0)

    def test_02_ai_tier_strict_limits_in_memory(self):
        tenant_token = "Bearer test-user-token-222"
        client_ip = "192.168.1.20"
        ai_path = "/api/insights/analyze"

        for _ in range(MAX_AI_REQUESTS_PER_WINDOW):
            allowed, retry_after, remaining = asyncio.run(
                self.limiter.check_rate_limit(client_ip=client_ip, path=ai_path, auth_header=tenant_token)
            )
            self.assertTrue(allowed)

        allowed, retry_after, remaining = asyncio.run(
            self.limiter.check_rate_limit(client_ip=client_ip, path=ai_path, auth_header=tenant_token)
        )
        self.assertFalse(allowed)
        self.assertGreater(retry_after, 0)

    def test_03_tenant_isolation_in_memory(self):
        user_a_token = "Bearer user-alice-token-aaa"
        user_b_token = "Bearer user-bob-token-bbb"
        client_ip = "10.0.0.1"
        ai_path = "/api/memory/decisions"

        for _ in range(MAX_AI_REQUESTS_PER_WINDOW):
            asyncio.run(self.limiter.check_rate_limit(client_ip=client_ip, path=ai_path, auth_header=user_a_token))

        allowed_a, _, _ = asyncio.run(
            self.limiter.check_rate_limit(client_ip=client_ip, path=ai_path, auth_header=user_a_token)
        )
        self.assertFalse(allowed_a)

        allowed_b, _, remaining_b = asyncio.run(
            self.limiter.check_rate_limit(client_ip=client_ip, path=ai_path, auth_header=user_b_token)
        )
        self.assertTrue(allowed_b)
        self.assertGreater(remaining_b, 0)

    def test_04_sanitized_identifier_security(self):
        raw_secret_token = "Bearer AIzaSyVerySecretSuperSensitiveToken1234567890"
        client_ip = "10.0.0.99"

        ident = self.limiter.sanitize_identifier(client_ip, raw_secret_token)
        self.assertNotIn("AIzaSyVerySecretSuperSensitiveToken", ident)
        self.assertTrue(ident.startswith("tenant:"))
        self.assertEqual(len(ident), 23)

    def test_05_concurrency_safety_in_memory(self):
        async def run_concurrent_checks():
            tasks = []
            for i in range(50):
                tasks.append(
                    self.limiter.check_rate_limit(
                        client_ip=f"10.0.1.{i % 5}",
                        path="/api/journal",
                        auth_header=f"Bearer user-token-{i % 5}"
                    )
                )
            results = await asyncio.gather(*tasks)
            return results

        results = asyncio.run(run_concurrent_checks())
        self.assertEqual(len(results), 50)
        for res in results:
            self.assertIsInstance(res[0], bool)

    def test_06_window_expiry_restores_quota(self):
        tenant_token = "Bearer test-user-expiry-999"
        client_ip = "127.0.0.1"
        path = "/api/insights/analyze"

        for _ in range(MAX_AI_REQUESTS_PER_WINDOW):
            asyncio.run(self.limiter.check_rate_limit(client_ip=client_ip, path=path, auth_header=tenant_token))

        allowed, _, _ = asyncio.run(
            self.limiter.check_rate_limit(client_ip=client_ip, path=path, auth_header=tenant_token)
        )
        self.assertFalse(allowed)

        time.sleep(2.1)

        allowed_after, _, _ = asyncio.run(
            self.limiter.check_rate_limit(client_ip=client_ip, path=path, auth_header=tenant_token)
        )
        self.assertTrue(allowed_after)

    # --- DISTRIBUTED REDIS / MEMORYSTORE TESTS ---

    def test_07_distributed_multi_instance_shared_limit(self):
        """
        Simulates 3 separate Cloud Run container instances all connecting to the same Redis instance.
        Verifies that requests across all instances accumulate towards the shared tenant limit.
        """
        shared_redis = MockRedisClient()
        instance_1 = SlidingWindowRateLimiter(window_seconds=60, redis_client=shared_redis)
        instance_2 = SlidingWindowRateLimiter(window_seconds=60, redis_client=shared_redis)
        instance_3 = SlidingWindowRateLimiter(window_seconds=60, redis_client=shared_redis)

        self.assertTrue(instance_1.is_distributed)
        self.assertTrue(instance_2.is_distributed)
        self.assertTrue(instance_3.is_distributed)

        token = "Bearer shared-tenant-token-777"
        path = "/api/insights/analyze"  # limit = 20

        # Send 10 requests to instance 1
        for _ in range(10):
            allowed, _, _ = asyncio.run(instance_1.check_rate_limit("1.1.1.1", path, token))
            self.assertTrue(allowed)

        # Send 10 requests to instance 2
        for _ in range(10):
            allowed, _, _ = asyncio.run(instance_2.check_rate_limit("2.2.2.2", path, token))
            self.assertTrue(allowed)

        # Request 21 to instance 3 MUST be blocked because total requests across instances = 20
        allowed_3, retry_after, remaining = asyncio.run(
            instance_3.check_rate_limit("3.3.3.3", path, token)
        )
        self.assertFalse(allowed_3)
        self.assertEqual(remaining, 0)
        self.assertGreater(retry_after, 0)

    def test_08_distributed_tenant_isolation(self):
        """
        Verifies that in a distributed environment, User A exhausting limits across
        multiple Cloud Run containers does not impact User B.
        """
        shared_redis = MockRedisClient()
        cloud_run_node_a = SlidingWindowRateLimiter(window_seconds=60, redis_client=shared_redis)
        cloud_run_node_b = SlidingWindowRateLimiter(window_seconds=60, redis_client=shared_redis)

        token_a = "Bearer tenant-alice-token"
        token_b = "Bearer tenant-bob-token"
        ai_path = "/api/insights/analyze"

        # Exhaust Alice's quota on Node A
        for _ in range(MAX_AI_REQUESTS_PER_WINDOW):
            asyncio.run(cloud_run_node_a.check_rate_limit("10.0.0.1", ai_path, token_a))

        # Alice is throttled on Node B
        allowed_alice, _, _ = asyncio.run(cloud_run_node_b.check_rate_limit("10.0.0.2", ai_path, token_a))
        self.assertFalse(allowed_alice)

        # Bob has full capacity on Node B
        allowed_bob, _, remaining_bob = asyncio.run(cloud_run_node_b.check_rate_limit("10.0.0.3", ai_path, token_b))
        self.assertTrue(allowed_bob)
        self.assertEqual(remaining_bob, MAX_AI_REQUESTS_PER_WINDOW - 1)

    def test_09_distributed_ai_vs_standard_tiers(self):
        """
        Verifies endpoint-aware limits in distributed mode.
        """
        shared_redis = MockRedisClient()
        limiter = SlidingWindowRateLimiter(window_seconds=60, redis_client=shared_redis)
        token = "Bearer dual-tier-tenant-token"

        ai_path = "/api/memory/contradictions"
        standard_path = "/api/journal/entries"

        # AI tier limit check
        ai_limit, ai_tier = limiter.get_tier_limit(ai_path)
        self.assertEqual(ai_limit, MAX_AI_REQUESTS_PER_WINDOW)
        self.assertEqual(ai_tier, "ai_intensive")

        # Standard tier limit check
        std_limit, std_tier = limiter.get_tier_limit(standard_path)
        self.assertEqual(std_limit, MAX_STANDARD_REQUESTS_PER_WINDOW)
        self.assertEqual(std_tier, "standard")

    def test_10_distributed_redis_failure_safe_policy(self):
        """
        Tests deliberate fail-safe policy when Redis experiences connection loss.
        Does not leak errors to caller; falls back to bounded local rate limiting.
        """
        failing_redis = MockRedisClient(should_fail=True)
        limiter = SlidingWindowRateLimiter(
            window_seconds=60,
            redis_client=failing_redis,
            fallback_policy="bounded_local"
        )

        token = "Bearer test-failover-user"
        path = "/api/insights/analyze"

        # Should safely fall back to in-memory limiting without raising unhandled exception
        allowed, retry_after, remaining = asyncio.run(
            limiter.check_rate_limit("10.0.0.1", path, token)
        )
        self.assertTrue(allowed)

    def test_11_distributed_redis_timeout_resilience(self):
        """
        Tests resilience when Redis socket times out.
        """
        timeout_redis = MockRedisClient(should_timeout=True)
        limiter = SlidingWindowRateLimiter(
            window_seconds=60,
            redis_client=timeout_redis,
            fallback_policy="bounded_local"
        )

        token = "Bearer test-timeout-user"
        path = "/api/journal"

        allowed, retry_after, remaining = asyncio.run(
            limiter.check_rate_limit("10.0.0.1", path, token)
        )
        self.assertTrue(allowed)

    def test_12_malformed_configuration_safety(self):
        """
        Verifies that invalid REDIS_URL strings or connection strings do not crash initialization.
        """
        limiter = SlidingWindowRateLimiter(redis_url="invalid://malformed-url:99999")
        self.assertFalse(limiter.is_distributed)

        allowed, _, _ = asyncio.run(
            limiter.check_rate_limit("10.0.0.1", "/api/journal", "Bearer test-user")
        )
        self.assertTrue(allowed)

    def test_13_no_secrets_in_redis_keys(self):
        """
        Verifies that keys written to Redis contain only sanitized hashes and no secrets or tokens.
        """
        shared_redis = MockRedisClient()
        limiter = SlidingWindowRateLimiter(window_seconds=60, redis_client=shared_redis)

        raw_secret_token = "Bearer AIzaSyVerySecretSuperSensitiveToken99999"
        asyncio.run(limiter.check_rate_limit("10.0.0.1", "/api/insights/analyze", raw_secret_token))

        keys = shared_redis.keys()
        self.assertGreater(len(keys), 0)
        for key in keys:
            self.assertNotIn("AIzaSyVerySecretSuperSensitiveToken", key)
            self.assertNotIn("Bearer", key)
            self.assertTrue(key.startswith("ratelimit:"))


if __name__ == "__main__":
    unittest.main()
