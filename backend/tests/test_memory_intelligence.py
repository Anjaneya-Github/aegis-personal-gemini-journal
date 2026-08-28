"""
Unit tests for Aegis Memory Intelligence:
- Decision Memory extraction and candidate validation
- Contradiction Detection with dual-entry verification
- Personal Evolution trajectory synthesis and citation checks
- Memory Integrity metrics computation
"""
import unittest
import asyncio
from unittest.mock import patch, AsyncMock

from backend.app.models import (
    PersonalEvolutionRequest,
    JournalEntryResponse,
    JournalEntryListResponse,
)
from backend.app.memory_intelligence import (
    extract_decision_memory,
    detect_contradictions,
    analyze_personal_evolution,
    get_current_integrity_stats,
    get_security_soc_status,
)


class TestMemoryIntelligence(unittest.TestCase):
    def setUp(self):
        self.uid = "test-user-memory-123"
        self.mock_entries = [
            JournalEntryResponse(
                id="entry-1",
                userId=self.uid,
                title="Switched to FastAPI",
                content="I decided to use Python FastAPI for our backend instead of Node.js because of strict type validation and performance.",
                mood="serene",
                tags=["architecture", "decision"],
                wordCount=25,
                createdAt=1700000000000,
                updatedAt=1700000000000,
            ),
            JournalEntryResponse(
                id="entry-2",
                userId=self.uid,
                title="Reducing Side Projects",
                content="I need to reduce my side projects to focus on deep work and sleep.",
                mood="reflective",
                tags=["focus"],
                wordCount=15,
                createdAt=1700086400000,
                updatedAt=1700086400000,
            ),
            JournalEntryResponse(
                id="entry-3",
                userId=self.uid,
                title="Excited About 3 New Projects",
                content="I want to start three new side projects this month! One for AI, one for cryptography, and one for mobile.",
                mood="radiant",
                tags=["projects", "ideas"],
                wordCount=20,
                createdAt=1700172800000,
                updatedAt=1700172800000,
            ),
        ]

    def test_decision_memory_verified_evidence(self):
        """Valid decisions with authorized evidence IDs are accepted."""
        fake_llm_json = """
        {
          "summary": "User made architectural commitments.",
          "decisions": [
            {
              "decisionId": "dec-1",
              "decision": "Adopt Python FastAPI for backend",
              "reasoning": "Type safety and performance",
              "date": "2023-11-14",
              "status": "active",
              "evidenceIds": ["entry-1"],
              "evidenceQuote": "I decided to use Python FastAPI for our backend",
              "confidence": "high"
            }
          ]
        }
        """
        with patch("backend.app.memory_intelligence.list_journal_entries", new_callable=AsyncMock) as mock_list, \
             patch("backend.app.memory_intelligence.generate_gemini_content", new_callable=AsyncMock) as mock_llm:
            mock_list.return_value = JournalEntryListResponse(entries=self.mock_entries, total=3)
            mock_llm.return_value = fake_llm_json

            result = asyncio.run(extract_decision_memory(self.uid))
            self.assertTrue(result.sufficientContext)
            self.assertEqual(len(result.decisions), 1)
            self.assertEqual(result.decisions[0].decision, "Adopt Python FastAPI for backend")
            self.assertEqual(result.decisions[0].evidenceIds, ["entry-1"])
            self.assertEqual(result.verifiedEvidenceCount, 1)
            self.assertEqual(result.rejectedEvidenceCount, 0)

    def test_decision_memory_zero_evidence_discard(self):
        """Decisions referencing unauthorized or nonexistent IDs must be discarded."""
        fake_llm_json = """
        {
          "summary": "Hallucinated decision",
          "decisions": [
            {
              "decisionId": "dec-fake",
              "decision": "Decided to move to Mars",
              "reasoning": "Space exploration",
              "date": "2023-11-14",
              "status": "active",
              "evidenceIds": ["nonexistent-foreign-entry-999"],
              "confidence": "high"
            }
          ]
        }
        """
        with patch("backend.app.memory_intelligence.list_journal_entries", new_callable=AsyncMock) as mock_list, \
             patch("backend.app.memory_intelligence.generate_gemini_content", new_callable=AsyncMock) as mock_llm:
            mock_list.return_value = JournalEntryListResponse(entries=self.mock_entries, total=3)
            mock_llm.return_value = fake_llm_json

            result = asyncio.run(extract_decision_memory(self.uid))
            self.assertFalse(result.sufficientContext)
            self.assertEqual(len(result.decisions), 0)
            self.assertEqual(result.rejectedEvidenceCount, 1)

    def test_contradiction_detection_verified_dual_entry(self):
        """Contradiction detection accepts valid pairwise authorized citations."""
        fake_llm_json = """
        {
          "contradictions": [
            {
              "topic": "Workload & Side Project Commitments",
              "earlierStatement": "I need to reduce my side projects to focus",
              "laterStatement": "I want to start three new side projects this month",
              "earlierEntryId": "entry-2",
              "laterEntryId": "entry-3",
              "neutralAnalysis": "Earlier intention to streamline shifted toward taking on new creative projects.",
              "confidence": "high"
            }
          ]
        }
        """
        with patch("backend.app.memory_intelligence.list_journal_entries", new_callable=AsyncMock) as mock_list, \
             patch("backend.app.memory_intelligence.generate_gemini_content", new_callable=AsyncMock) as mock_llm:
            mock_list.return_value = JournalEntryListResponse(entries=self.mock_entries, total=3)
            mock_llm.return_value = fake_llm_json

            result = asyncio.run(detect_contradictions(self.uid))
            self.assertTrue(result.sufficientContext)
            self.assertEqual(len(result.contradictions), 1)
            self.assertEqual(result.contradictions[0].topic, "Workload & Side Project Commitments")
            self.assertEqual(result.verifiedEvidenceCount, 2)
            self.assertIn("entry-2", result.contradictions[0].evidenceIds)
            self.assertIn("entry-3", result.contradictions[0].evidenceIds)

    def test_contradiction_detection_rejects_hallucinated_entry(self):
        """Contradiction detection rejects items where either earlier or later ID is invalid."""
        fake_llm_json = """
        {
          "contradictions": [
            {
              "topic": "Phantom Conflict",
              "earlierStatement": "Earlier quote",
              "laterStatement": "Later quote",
              "earlierEntryId": "entry-2",
              "laterEntryId": "foreign-unauthorized-id-xyz",
              "neutralAnalysis": "Some analysis",
              "confidence": "high"
            }
          ]
        }
        """
        with patch("backend.app.memory_intelligence.list_journal_entries", new_callable=AsyncMock) as mock_list, \
             patch("backend.app.memory_intelligence.generate_gemini_content", new_callable=AsyncMock) as mock_llm:
            mock_list.return_value = JournalEntryListResponse(entries=self.mock_entries, total=3)
            mock_llm.return_value = fake_llm_json

            result = asyncio.run(detect_contradictions(self.uid))
            self.assertFalse(result.sufficientContext)
            self.assertEqual(len(result.contradictions), 0)
            self.assertEqual(result.rejectedEvidenceCount, 1)

    def test_personal_evolution_analysis(self):
        """Personal evolution verifies citations and extracts theme trajectories."""
        fake_llm_json = """
        {
          "synthesis": "The user demonstrates continuous technical maturation.",
          "trajectorySummary": "Shift from exploration to deliberate architecture.",
          "evolutionItems": [
            {
              "theme": "Engineering Discipline",
              "trend": "From reactive to disciplined",
              "earlierPhase": "Flexible experimentation",
              "laterPhase": "Defensive architectural choices",
              "timePeriod": "November 2023",
              "confidence": "high",
              "evidence": [
                {
                  "entryId": "entry-1",
                  "quote": "I decided to use Python FastAPI for our backend"
                }
              ]
            }
          ]
        }
        """
        with patch("backend.app.memory_intelligence.list_journal_entries", new_callable=AsyncMock) as mock_list, \
             patch("backend.app.memory_intelligence.generate_gemini_content", new_callable=AsyncMock) as mock_llm:
            mock_list.return_value = JournalEntryListResponse(entries=self.mock_entries, total=3)
            mock_llm.return_value = fake_llm_json

            req = PersonalEvolutionRequest(query="engineering focus")
            result = asyncio.run(analyze_personal_evolution(self.uid, req))
            self.assertTrue(result.sufficientContext)
            self.assertEqual(len(result.evolutionItems), 1)
            self.assertEqual(result.evolutionItems[0].theme, "Engineering Discipline")
            self.assertEqual(len(result.evolutionItems[0].supportingEvidence), 1)

    def test_security_soc_status(self):
        """Security SOC returns full architectural audits and zero-trust indicators."""
        soc = get_security_soc_status(self.uid)
        self.assertEqual(soc.systemStatus, "ALL SYSTEMS SECURE")
        self.assertGreaterEqual(len(soc.audits), 8)
        self.assertIn("ENFORCED", [a.status for a in soc.audits])
        self.assertIn("PASS", [a.status for a in soc.audits])


if __name__ == "__main__":
    unittest.main()
