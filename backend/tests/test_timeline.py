"""
Automated unit and integration tests for Timeline and Milestone Generation.
"""
import pytest
from httpx import AsyncClient, ASGITransport
import os

os.environ["AEGIS_TEST_MODE"] = "1"
os.environ["USE_MEMORY_STORE"] = "1"

from app.main import app
from app.journal import reset_memory_store, create_journal_entry
from app.models import JournalEntryCreate


@pytest.fixture(autouse=True)
def setup_teardown():
    reset_memory_store()
    yield
    reset_memory_store()


@pytest.mark.asyncio
async def test_timeline_empty():
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer test-token-alice"}

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/journal/timeline", headers=headers)

    assert res.status_code == 200
    data = res.json()
    assert data["totalEntries"] == 0
    assert len(data["items"]) == 0
    assert len(data["milestones"]) == 0


@pytest.mark.asyncio
async def test_timeline_with_entries():
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer test-token-alice"}

    await create_journal_entry(
        "alice",
        JournalEntryCreate(
            title="First Day",
            content="Started the new job today. Excited for what is next.",
            mood="radiant",
            tags=["career", "milestone"]
        )
    )

    await create_journal_entry(
        "alice",
        JournalEntryCreate(
            title="Reflecting on Progress",
            content="Finished week one successfully.",
            mood="serene",
            tags=["career", "growth"]
        )
    )

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/journal/timeline", headers=headers)

    assert res.status_code == 200
    data = res.json()
    assert data["totalEntries"] == 2
    assert len(data["items"]) == 2
    assert len(data["milestones"]) >= 1
    assert "career" in data["dominantThemes"]
    assert data["moodDistribution"]["radiant"] == 1
    assert data["moodDistribution"]["serene"] == 1
