"""
Automated unit and integration tests for My Reflection longitudinal synthesis.
"""
import pytest
import json
from unittest.mock import patch
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
async def test_reflection_empty_journal():
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer test-token-alice"}

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/journal/reflect", headers=headers)

    assert res.status_code == 200
    data = res.json()
    assert data["totalEntriesAnalyzed"] == 0
    assert "waiting for its first reflections" in data["overallNarrative"]


@pytest.mark.asyncio
async def test_reflection_with_entries_and_citations():
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer test-token-alice"}

    entry1 = await create_journal_entry(
        "alice",
        JournalEntryCreate(
            title="Overcoming procrastination",
            content="Broke my project into 15-minute intervals. The friction vanished.",
            mood="serene",
            tags=["focus", "productivity"]
        )
    )

    mock_gemini_json = json.dumps({
        "overallNarrative": "Alice has demonstrated significant improvement in managing project inertia.",
        "sentimentArc": "From anxious overwhelm toward structured calm.",
        "growthThemes": [
            {
                "theme": "Granular Focus Habits",
                "insight": "Time-boxing reduced task startup anxiety.",
                "evidence": [
                    {
                        "entryId": entry1.id,
                        "quote": "Broke my project into 15-minute intervals."
                    },
                    {
                        "entryId": "hallucinated-id",
                        "quote": "Non-existent quote"
                    }
                ]
            }
        ],
        "suggestedPrompt": "How can you apply 15-minute intervals to other personal goals?"
    })

    with patch("app.reflection.generate_gemini_content", return_value=mock_gemini_json):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res = await ac.get("/api/journal/reflect", headers=headers)

    assert res.status_code == 200
    data = res.json()
    assert data["totalEntriesAnalyzed"] == 1
    assert len(data["growthThemes"]) == 1
    # Check that hallucinated citation was discarded while valid citation was kept
    evidence = data["growthThemes"][0]["evidence"]
    assert len(evidence) == 1
    assert evidence[0]["entryId"] == entry1.id
    assert evidence[0]["entryTitle"] == "Overcoming procrastination"
