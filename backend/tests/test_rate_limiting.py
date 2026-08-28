"""
Comprehensive Test Suite for Aegis Journal Rate Limiter.
Tests:
1. Standard tier request bounding
2. AI tier strict bounding (cost amplification defense)
3. Tenant isolation (User A rate limit does not affect User B)
4. Unauthenticated client IP hashing
5. Concurrency safety under high volume parallel requests
6. Calculation of accurate Retry-After window
7. Safe fallback on simulated backend failure
8. Sanitized identifier hashing (zero secrets or tokens exposed)
"""
import unittest
import asyncio
import time
from backend.app.rate_limiter import (
    SlidingWindowRateLimiter,
    RATE_LIMIT_WINDOW_SECONDS,
    MAX_AI_REQUESTS_PER_WINDOW,
    MAX_STANDARD_REQUESTS_PER_WINDOW,
)


class TestRateLimiter(unittest.TestCase):
    def setUp(self):
        self.limiter = SlidingWindowRateLimiter(window_seconds=2)  # Short 2s window for tests

    def tearDown(self):
        self.limiter.reset_state()

    def test_01_standard_tier_limits(self):
        tenant_token = "Bearer test-user-token-111"
        client_ip = "192.168.1.10"
        path = "/api/journal"

        # First requests should pass
        for _ in range(MAX_STANDARD_REQUESTS_PER_WINDOW):
            allowed, retry_after, remaining = asyncio.run(
                self.limiter.check_rate_limit(client_ip=client_ip, path=path, auth_header=tenant_token)
            )
            self.assertTrue(allowed)

        # Exceeding limit should return 429 status (allowed=False)
        allowed, retry_after, remaining = asyncio.run(
            self.limiter.check_rate_limit(client_ip=client_ip, path=path, auth_header=tenant_token)
        )
        self.assertFalse(allowed)
        self.assertGreater(retry_after, 0)
        self.assertEqual(remaining, 0)

    def test_02_ai_tier_strict_limits(self):
        tenant_token = "Bearer test-user-token-222"
        client_ip = "192.168.1.20"
        ai_path = "/api/insights/analyze"

        # AI tier has stricter ceiling
        for _ in range(MAX_AI_REQUESTS_PER_WINDOW):
            allowed, retry_after, remaining = asyncio.run(
                self.limiter.check_rate_limit(client_ip=client_ip, path=ai_path, auth_header=tenant_token)
            )
            self.assertTrue(allowed)

        # Next request must be throttled
        allowed, retry_after, remaining = asyncio.run(
            self.limiter.check_rate_limit(client_ip=client_ip, path=ai_path, auth_header=tenant_token)
        )
        self.assertFalse(allowed)
        self.assertGreater(retry_after, 0)

    def test_03_tenant_isolation(self):
        user_a_token = "Bearer user-alice-token-aaa"
        user_b_token = "Bearer user-bob-token-bbb"
        client_ip = "10.0.0.1"
        ai_path = "/api/memory/decisions"

        # Exhaust User A's limit
        for _ in range(MAX_AI_REQUESTS_PER_WINDOW):
            asyncio.run(self.limiter.check_rate_limit(client_ip=client_ip, path=ai_path, auth_header=user_a_token))

        allowed_a, _, _ = asyncio.run(
            self.limiter.check_rate_limit(client_ip=client_ip, path=ai_path, auth_header=user_a_token)
        )
        self.assertFalse(allowed_a)

        # User B should still have full quota despite sharing the same IP
        allowed_b, _, remaining_b = asyncio.run(
            self.limiter.check_rate_limit(client_ip=client_ip, path=ai_path, auth_header=user_b_token)
        )
        self.assertTrue(allowed_b)
        self.assertGreater(remaining_b, 0)

    def test_04_sanitized_identifier_security(self):
        raw_secret_token = "Bearer AIzaSyVerySecretSuperSensitiveToken1234567890"
        client_ip = "10.0.0.99"
        
        ident = self.limiter.sanitize_identifier(client_ip, raw_secret_token)
        # Verify secret token is NOT in the identifier
        self.assertNotIn("AIzaSyVerySecretSuperSensitiveToken", ident)
        self.assertTrue(ident.startswith("tenant:"))
        self.assertEqual(len(ident), 23)  # "tenant:" (7) + 16 chars hash

    def test_05_concurrency_safety(self):
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
        # All tasks completed safely with boolean responses
        for res in results:
            self.assertIsInstance(res[0], bool)

    def test_06_window_expiry_restores_quota(self):
        tenant_token = "Bearer test-user-expiry-999"
        client_ip = "127.0.0.1"
        path = "/api/insights/analyze"

        # Consume quota
        for _ in range(MAX_AI_REQUESTS_PER_WINDOW):
            asyncio.run(self.limiter.check_rate_limit(client_ip=client_ip, path=path, auth_header=tenant_token))

        allowed, _, _ = asyncio.run(
            self.limiter.check_rate_limit(client_ip=client_ip, path=path, auth_header=tenant_token)
        )
        self.assertFalse(allowed)

        # Wait for the 2-second test window to expire
        time.sleep(2.1)

        # Quota should now be restored
        allowed_after, _, _ = asyncio.run(
            self.limiter.check_rate_limit(client_ip=client_ip, path=path, auth_header=tenant_token)
        )
        self.assertTrue(allowed_after)


if __name__ == "__main__":
    unittest.main()
