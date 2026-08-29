"""
Automated unit and integration tests for Aegis Journal Authentication.
"""
import unittest
import asyncio
import os

os.environ["AEGIS_TEST_MODE"] = "1"
os.environ["USE_MEMORY_STORE"] = "1"

from backend.app.auth import verify_firebase_token, AuthenticatedUser
from backend.app.errors import AuthenticationError


class TestAuthentication(unittest.TestCase):

    def test_auth_missing_header(self):
        with self.assertRaises(AuthenticationError) as ctx:
            asyncio.run(verify_firebase_token(None))
        self.assertIn("Missing Authorization header", str(ctx.exception))

    def test_auth_malformed_header(self):
        with self.assertRaises(AuthenticationError) as ctx:
            asyncio.run(verify_firebase_token("Basic dXNlcjpwYXNz"))
        self.assertIn("Invalid Authorization header", str(ctx.exception))

    def test_auth_invalid_token(self):
        with self.assertRaises(AuthenticationError) as ctx:
            asyncio.run(verify_firebase_token("Bearer invalid-token"))
        self.assertIn("Invalid Firebase ID token", str(ctx.exception))

    def test_auth_valid_token_extraction(self):
        user = asyncio.run(verify_firebase_token("Bearer test-token-user-123:alice@example.com"))
        self.assertIsInstance(user, AuthenticatedUser)
        self.assertEqual(user.uid, "user-123")
        self.assertEqual(user.email, "alice@example.com")


if __name__ == "__main__":
    unittest.main()
