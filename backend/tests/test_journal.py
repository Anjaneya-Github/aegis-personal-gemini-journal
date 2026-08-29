"""
Automated unit and integration tests for Aegis Journal CRUD and Cross-User Isolation.
"""
import unittest
import asyncio
import os

os.environ["AEGIS_TEST_MODE"] = "1"
os.environ["USE_MEMORY_STORE"] = "1"

from backend.app.journal import (
    reset_memory_store,
    create_journal_entry,
    list_journal_entries,
    get_journal_entry,
    update_journal_entry,
    delete_journal_entry,
)
from backend.app.models import JournalEntryCreate, JournalEntryUpdate
from backend.app.errors import NotFoundError


class TestJournalCRUDAndIsolation(unittest.TestCase):

    def setUp(self):
        reset_memory_store()

    def tearDown(self):
        reset_memory_store()

    def test_journal_crud_lifecycle(self):
        # 1. Create Entry
        entry = asyncio.run(create_journal_entry(
            uid="user-alice",
            data=JournalEntryCreate(
                title="Morning Meditation",
                content="Felt grounded after 20 minutes of silent breathing and stretching.",
                mood="radiant",
                tags=["Mindfulness", "MorningRoutine", "#peace"],
            )
        ))
        entry_id = entry.id
        self.assertEqual(entry.title, "Morning Meditation")
        self.assertEqual(entry.userId, "user-alice")
        self.assertEqual(entry.wordCount, 10)
        self.assertIn("mindfulness", entry.tags)
        self.assertIn("peace", entry.tags)

        # 2. List Entries
        res = asyncio.run(list_journal_entries(uid="user-alice"))
        self.assertEqual(res.total, 1)
        self.assertEqual(res.entries[0].id, entry_id)

        # 3. Get Entry by ID
        fetched = asyncio.run(get_journal_entry(uid="user-alice", entry_id=entry_id))
        self.assertEqual(fetched.id, entry_id)

        # 4. Update Entry
        updated = asyncio.run(update_journal_entry(
            uid="user-alice",
            entry_id=entry_id,
            data=JournalEntryUpdate(
                title="Morning Meditation & Yoga",
                mood="serene"
            )
        ))
        self.assertEqual(updated.title, "Morning Meditation & Yoga")
        self.assertEqual(updated.mood, "serene")

        # 5. Delete Entry
        del_res = asyncio.run(delete_journal_entry(uid="user-alice", entry_id=entry_id))
        self.assertTrue(del_res.get("success", True))

        # 6. Verify Deleted
        with self.assertRaises(NotFoundError):
            asyncio.run(get_journal_entry(uid="user-alice", entry_id=entry_id))

    def test_cross_user_isolation(self):
        # Alice creates a confidential entry
        alice_entry = asyncio.run(create_journal_entry(
            uid="alice",
            data=JournalEntryCreate(
                title="Alice's Secret Journal",
                content="Confidential reflections strictly for Alice.",
                mood="reflective",
                tags=["private"],
            )
        ))
        entry_id = alice_entry.id

        # Bob attempts to read Alice's entry -> NotFoundError
        with self.assertRaises(NotFoundError):
            asyncio.run(get_journal_entry(uid="bob", entry_id=entry_id))

        # Bob attempts to list entries - must see 0 entries
        bob_entries = asyncio.run(list_journal_entries(uid="bob"))
        self.assertEqual(bob_entries.total, 0)
        self.assertEqual(len(bob_entries.entries), 0)

        # Bob attempts to update Alice's entry -> NotFoundError
        with self.assertRaises(NotFoundError):
            asyncio.run(update_journal_entry(
                uid="bob",
                entry_id=entry_id,
                data=JournalEntryUpdate(title="Hacked Title")
            ))

        # Bob attempts to delete Alice's entry -> NotFoundError
        with self.assertRaises(NotFoundError):
            asyncio.run(delete_journal_entry(uid="bob", entry_id=entry_id))

        # Alice verifies her entry is intact
        intact = asyncio.run(get_journal_entry(uid="alice", entry_id=entry_id))
        self.assertEqual(intact.title, "Alice's Secret Journal")


if __name__ == "__main__":
    unittest.main()
