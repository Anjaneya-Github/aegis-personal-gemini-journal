"""
Automated unit and integration tests for My Reflection longitudinal synthesis.
"""
import unittest
import asyncio
import json
from unittest.mock import patch
import os

os.environ["AEGIS_TEST_MODE"] = "1"
os.environ["USE_MEMORY_STORE"] = "1"

from backend.app.journal import reset_memory_store, create_journal_entry
from backend.app.models import JournalEntryCreate
from backend.app.reflection import generate_journal_reflection


class TestReflection(unittest.TestCase):

    def setUp(self):
        reset_memory_store()

    def tearDown(self):
        reset_memory_store()

    def test_reflection_empty_journal(self):
        res = asyncio.run(generate_journal_reflection(uid="alice"))
        self.assertEqual(res.totalEntriesAnalyzed, 0)
        self.assertIn("waiting for its first reflections", res.overallNarrative)

    def test_reflection_with_entries_and_citations(self):
        entry1 = asyncio.run(create_journal_entry(
            "alice",
            JournalEntryCreate(
                title="Overcoming procrastination",
                content="Broke my project into 15-minute intervals. The friction vanished.",
                mood="serene",
                tags=["focus", "productivity"]
            )
        ))

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

        with patch("backend.app.reflection.generate_gemini_content", return_value=mock_gemini_json):
            res = asyncio.run(generate_journal_reflection(uid="alice"))

        self.assertEqual(res.totalEntriesAnalyzed, 1)
        self.assertEqual(len(res.growthThemes), 1)
        # Check that hallucinated citation was discarded while valid citation was kept
        evidence = res.growthThemes[0].evidence
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].entryId, entry1.id)
        self.assertEqual(evidence[0].entryTitle, "Overcoming procrastination")


if __name__ == "__main__":
    unittest.main()
