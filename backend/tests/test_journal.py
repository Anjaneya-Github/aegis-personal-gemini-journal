"""
Automated unit and integration tests for Aegis Journal CRUD and Cross-User Isolation.
"""
import pytest
from httpx import AsyncClient, ASGITransport
import os

os.environ["AEGIS_TEST_MODE"] = "1"
os.environ["USE_MEMORY_STORE"] = "1"

from app.main import app
from app.journal import reset_memory_store


@pytest.fixture(autouse=True)
def setup_teardown():
    reset_memory_store()
    yield
    reset_memory_store()


@pytest.mark.asyncio
async def test_journal_crud_lifecycle():
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer test-token-user-alice"}

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Create Entry
        create_res = await ac.post(
            "/api/journal/entries",
            headers=headers,
            json={
                "title": "Morning Meditation",
                "content": "Felt grounded after 20 minutes of silent breathing and stretching.",
                "mood": "radiant",
                "tags": ["Mindfulness", "MorningRoutine", "#peace"],
            }
        )
        assert create_res.status_code == 201
        created = create_res.json()
        entry_id = created["id"]
        assert created["title"] == "Morning Meditation"
        assert created["userId"] == "user-alice"
        assert created["wordCount"] == 10
        # Check tag sanitization (lowercase, no #, deduplicated)
        assert "mindfulness" in created["tags"]
        assert "peace" in created["tags"]

        # 2. List Entries
        list_res = await ac.get("/api/journal/entries", headers=headers)
        assert list_res.status_code == 200
        entries = list_res.json()["entries"]
        assert len(entries) == 1
        assert entries[0]["id"] == entry_id

        # 3. Get Entry by ID
        get_res = await ac.get(f"/api/journal/entries/{entry_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["id"] == entry_id

        # 4. Update Entry
        update_res = await ac.put(
            f"/api/journal/entries/{entry_id}",
            headers=headers,
            json={
                "title": "Morning Meditation & Yoga",
                "mood": "serene"
            }
        )
        assert update_res.status_code == 200
        updated = update_res.json()
        assert updated["title"] == "Morning Meditation & Yoga"
        assert updated["mood"] == "serene"

        # 5. Delete Entry
        del_res = await ac.delete(f"/api/journal/entries/{entry_id}", headers=headers)
        assert del_res.status_code == 204

        # 6. Verify Deleted
        get_after_del = await ac.get(f"/api/journal/entries/{entry_id}", headers=headers)
        assert get_after_del.status_code == 404


@pytest.mark.asyncio
async def test_cross_user_isolation():
    transport = ASGITransport(app=app)
    alice_headers = {"Authorization": "Bearer test-token-alice"}
    bob_headers = {"Authorization": "Bearer test-token-bob"}

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Alice creates a confidential entry
        alice_create = await ac.post(
            "/api/journal/entries",
            headers=alice_headers,
            json={
                "title": "Alice's Secret Journal",
                "content": "Confidential reflections strictly for Alice.",
                "mood": "reflective",
                "tags": ["private"],
            }
        )
        assert alice_create.status_code == 201
        entry_id = alice_create.json()["id"]

        # Bob attempts to read Alice's entry
        bob_get = await ac.get(f"/api/journal/entries/{entry_id}", headers=bob_headers)
        assert bob_get.status_code == 404

        # Bob attempts to list entries - must see 0 entries
        bob_list = await ac.get("/api/journal/entries", headers=bob_headers)
        assert bob_list.status_code == 200
        assert bob_list.json()["total"] == 0

        # Bob attempts to update Alice's entry
        bob_update = await ac.put(
            f"/api/journal/entries/{entry_id}",
            headers=bob_headers,
            json={"title": "Hacked Title"}
        )
        assert bob_update.status_code == 404

        # Bob attempts to delete Alice's entry
        bob_delete = await ac.delete(f"/api/journal/entries/{entry_id}", headers=bob_headers)
        assert bob_delete.status_code == 404

        # Alice verifies her entry is intact
        alice_get = await ac.get(f"/api/journal/entries/{entry_id}", headers=alice_headers)
        assert alice_get.status_code == 200
        assert alice_get.json()["title"] == "Alice's Secret Journal"
