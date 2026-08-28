"""
Automated unit and integration tests for Aegis Journal Authentication.
"""
import pytest
from httpx import AsyncClient, ASGITransport
import os

os.environ["AEGIS_TEST_MODE"] = "1"
os.environ["USE_MEMORY_STORE"] = "1"

from app.main import app


@pytest.mark.asyncio
async def test_auth_missing_header():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/journal/entries")
    assert response.status_code == 401
    assert "Missing Authorization header" in response.json()["error"]


@pytest.mark.asyncio
async def test_auth_malformed_header():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/journal/entries", headers={"Authorization": "Basic dXNlcjpwYXNz"})
    assert response.status_code == 401
    assert "Invalid Authorization header format" in response.json()["error"]


@pytest.mark.asyncio
async def test_auth_invalid_token():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/journal/entries", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401
    assert "Invalid Firebase ID token" in response.json()["error"]


@pytest.mark.asyncio
async def test_auth_valid_token_extraction():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/api/journal/entries", 
            headers={"Authorization": "Bearer test-token-user-123:alice@example.com"}
        )
    assert response.status_code == 200
    data = response.json()
    assert "entries" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_auth_ignores_client_supplied_uid_in_body():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Attempt to spoof UID as "attacker-uid" in body
        response = await ac.post(
            "/api/journal/entries",
            headers={"Authorization": "Bearer test-token-real-user-456"},
            json={
                "title": "My Private Thoughts",
                "content": "Deep personal reflection.",
                "mood": "serene",
                "tags": ["peace"],
                "userId": "attacker-uid",
                "uid": "attacker-uid"
            }
        )
    assert response.status_code == 201
    entry = response.json()
    # The server MUST assign the entry to the authenticated user ID from the verified token
    assert entry["userId"] == "real-user-456"
    assert entry["userId"] != "attacker-uid"
