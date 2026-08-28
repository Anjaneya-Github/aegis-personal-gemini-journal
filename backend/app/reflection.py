"""
My Reflection module: Evidence-backed longitudinal insights and growth themes.
"""
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

from .models import (
    ReflectionResponse,
    GrowthTheme,
    EvidenceCitation,
    JournalEntryResponse
)
from .journal import list_journal_entries
from .gemini_service import generate_gemini_content
from .security_guard import build_candidate_containment_corpus, PROMPT_SECURITY_PREAMBLE
from .validation import MAX_CANDIDATE_ENTRIES_LIMIT

logger = logging.getLogger("aegis_journal.reflection")


async def generate_journal_reflection(uid: str) -> ReflectionResponse:
    """
    Generates longitudinal self-reflection and growth themes grounded in authorized journal entries.
    """
    # 1. Retrieve Candidate Set (Bounded to max 30)
    list_res = await list_journal_entries(uid=uid, limit=MAX_CANDIDATE_ENTRIES_LIMIT)
    candidates: List[JournalEntryResponse] = list_res.entries

    if not candidates:
        return ReflectionResponse(
            overallNarrative="Your journal is waiting for its first reflections. Begin documenting your thoughts, milestones, and challenges to unlock deep emotional insights and longitudinal patterns.",
            sentimentArc="Neutral baseline — awaiting initial journal entries.",
            growthThemes=[],
            suggestedPrompt="What is one feeling, challenge, or victory on your mind today that you want to remember?",
            totalEntriesAnalyzed=0,
        )

    # 2. Build Backend-Authorized Candidate Map
    candidate_map: Dict[str, JournalEntryResponse] = {entry.id: entry for entry in candidates}

    # Format candidates for containment corpus
    candidate_dicts = []
    for c in candidates:
        date_str = datetime.fromtimestamp(c.createdAt / 1000).strftime("%Y-%m-%d %H:%M")
        candidate_dicts.append({
            "id": c.id,
            "title": c.title,
            "date": date_str,
            "mood": c.mood,
            "content": c.content,
        })

    containment_corpus = build_candidate_containment_corpus(candidate_dicts)

    # 3. Construct Structured Prompt
    system_instruction = (
        f"{PROMPT_SECURITY_PREAMBLE}\n\n"
        "You are an empathetic, insightful psychological reflection assistant.\n"
        "Analyze the provided historical entries to identify authentic emotional patterns, recurrent themes, and progress.\n"
        "Rules:\n"
        "- Every growth theme insight MUST cite one or more specific `entryId`s from the provided `<journal_entry_untrusted>` collection.\n"
        "- `entryId` must match the exact `id` attribute.\n"
        "- Provide direct quotes where relevant.\n"
        "- Generate a thoughtful, non-judgmental `suggestedPrompt`."
    )

    prompt = (
        f"Historical Journal Entries:\n{containment_corpus}\n\n"
        "Generate a structured psychological reflection in JSON format matching this schema:\n"
        "{\n"
        '  "overallNarrative": "A warm, cohesive 2-3 paragraph summary of the user\'s recent reflections and headspace",\n'
        '  "sentimentArc": "Brief description of the emotional trajectory (e.g. from anxiety toward calm resolution)",\n'
        '  "growthThemes": [\n'
        "    {\n"
        '      "theme": "Theme title (e.g. Navigating Creative Friction)",\n'
        '      "insight": "Observation on what helped or caused growth",\n'
        '      "evidence": [\n'
        "        {\n"
        '          "entryId": "exact-entry-id",\n'
        '          "quote": "relevant excerpt"\n'
        "        }\n"
        "      ]\n"
        "    }\n"
        "  ],\n"
        '  "suggestedPrompt": "A mindful journaling question tailored to current reflections"\n'
        "}"
    )

    # 4. Call Gemini
    raw_response = await generate_gemini_content(
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=0.2,
    )

    # 5. Parse and Validate Model Output
    try:
        clean_json = raw_response.strip()
        if clean_json.startswith("```"):
            clean_json = clean_json.split("\n", 1)[1]
            if clean_json.endswith("```"):
                clean_json = clean_json.rsplit("```", 1)[0]
            clean_json = clean_json.strip()

        parsed = json.loads(clean_json)
    except Exception as e:
        logger.error(f"Failed to parse reflection JSON: {e}")
        return ReflectionResponse(
            overallNarrative="Your recent entries reflect an ongoing journey of personal insight and self-discovery.",
            sentimentArc="Dynamic reflective equilibrium.",
            growthThemes=[],
            suggestedPrompt="What is one area of your life where you notice gradual growth or calm?",
            totalEntriesAnalyzed=len(candidates),
        )

    # 6. Verify and Validate Citations against Candidate Map
    verified_themes: List[GrowthTheme] = []
    raw_themes = parsed.get("growthThemes", [])

    if isinstance(raw_themes, list):
        for gt in raw_themes:
            if not isinstance(gt, dict):
                continue
            theme_title = str(gt.get("theme", "Observation")).strip()
            insight = str(gt.get("insight", "")).strip()
            raw_evidence = gt.get("evidence", [])

            verified_evidence: List[EvidenceCitation] = []
            if isinstance(raw_evidence, list):
                for ev in raw_evidence:
                    if not isinstance(ev, dict):
                        continue
                    entry_id = str(ev.get("entryId", "")).strip()
                    if entry_id in candidate_map:
                        matched = candidate_map[entry_id]
                        quote = str(ev.get("quote", "")).strip()
                        verified_evidence.append(
                            EvidenceCitation(
                                entryId=matched.id,
                                entryTitle=matched.title,
                                quote=quote if quote else matched.content[:100] + "...",
                            )
                        )
                    else:
                        logger.warning(f"Discarding unauthorized reflection entry ID: {entry_id}")

            verified_themes.append(
                GrowthTheme(
                    theme=theme_title,
                    insight=insight,
                    evidence=verified_evidence,
                )
            )

    return ReflectionResponse(
        overallNarrative=parsed.get("overallNarrative", "A meaningful period of self-reflection and personal growth."),
        sentimentArc=parsed.get("sentimentArc", "Reflective journey."),
        growthThemes=verified_themes,
        suggestedPrompt=parsed.get("suggestedPrompt", "What feeling or thought is calling for your attention today?"),
        totalEntriesAnalyzed=len(candidates),
    )
