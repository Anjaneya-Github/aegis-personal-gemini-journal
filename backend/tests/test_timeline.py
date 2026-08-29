"""
Automated unit and integration tests for Timeline and Milestone Generation.
"""
import unittest
import asyncio
import os

os.environ["AEGIS_TEST_MODE"] = "1"
os.environ["USE_MEMORY_STORE"] = "1"

from backend.app.journal import reset_memory_store, create_journal_entry
from backend.app.models import JournalEntryCreate
from backend.app.timeline import generate_journal_timeline


class TestTimeline(unittest.TestCase):

    def setUp(self):
        reset_memory_store()

    def tearDown(self):
        reset_memory_store()

    def test_timeline_empty(self):
        res = asyncio.run(generate_journal_timeline(uid="alice"))
        self.assertEqual(res.totalEntries, 0)
        self.assertEqual(len(res.items), 0)
        self.assertEqual(len(res.milestones), 0)

    def test_timeline_with_entries(self):
        asyncio.run(create_journal_entry(
            "alice",
            JournalEntryCreate(
                title="First Day",
                content="Started the new job today. Excited for what is next.",
                mood="radiant",
                tags=["career", "milestone"]
            )
        ))

        asyncio.run(create_journal_entry(
            "alice",
            JournalEntryCreate(
                title="Reflecting on Progress",
                content="Finished week one successfully.",
                mood="serene",
                tags=["career", "growth"]
            )
        ))

        res = asyncio.run(generate_journal_timeline(uid="alice"))
        self.assertEqual(res.totalEntries, 2)
        self.assertEqual(len(res.items), 2)
        self.assertGreaterEqual(len(res.milestones), 1)
        self.assertIn("career", res.dominantThemes)
        self.assertEqual(res.moodDistribution["radiant"], 1)
        self.assertEqual(res.moodDistribution["serene"], 1)


if __name__ == "__main__":
    unittest.main()
