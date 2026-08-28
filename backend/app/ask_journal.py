"""
Ask My Journal module with Bounded Retrieval and Strict Evidence Verification.
Security Guarantee:
- Gemini source IDs must be validated against the backend-authorized candidate set before being shown to the user.
- If an answer has zero valid evidence, discard the answer and return an insufficient-context response.
- Gemini must NEVER be an authorization authority.
"""
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

from .models import (
    AskJournalRequest, 
    AskJournalResponse, 
    EvidenceSource,
    JournalEntryResponse
)
from .journal import list_journal_entries
from .gemini_service import generate_gemini_content
from .security_guard import (
    assert_safe_query, 
    build_candidate_containment_corpus, 
    PROMPT_SECURITY_PREAMBLE
)
from .validation import validate_query, MAX_CANDIDATE_ENTRIES_LIMIT

logger = logging.getLogger("aegis_journal.ask")

INSUFFICIENT_CONTEXT_MESSAGE = (
    "I searched your journal entries, but couldn't find sufficient verified evidence to answer your query. "
    "Try asking about topics or events you have written about in your journal entries."
)


async def execute_ask_journal(uid: str, request_data: AskJournalRequest) -> AskJournalResponse:
    """
    Executes an evidence-backed inquiry across the authenticated user's private journal entries.
    """
    # 1. Input Validation and Security Guard
    clean_query = validate_query(request_data.query)
    assert_safe_query(clean_query)

    # 2. Bounded Retrieval (Max 30 candidate entries for this user)
    list_res = await list_journal_entries(uid=uid, limit=MAX_CANDIDATE_ENTRIES_LIMIT)
    candidates: List[JournalEntryResponse] = list_res.entries

    if not candidates:
        return AskJournalResponse(
            answer="You have not created any journal entries yet. Write a few entries, and I will be happy to help you explore them!",
            sources=[],
            sufficientContext=False,
            totalCandidatesAnalyzed=0,
            rejectedSourceCount=0,
        )

    # 3. Build Backend-Authorized Candidate Map
    # Candidate map is strictly determined by Firestore query under /users/{uid}/entries
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

    # 4. Construct Structured Gemini Prompt
    system_instruction = (
        f"{PROMPT_SECURITY_PREAMBLE}\n\n"
        "You are an analytical, deeply respectful personal journal companion.\n"
        "Your task is to answer the user's question USING ONLY the provided `<journal_entry_untrusted>` entries.\n"
        "Guidelines:\n"
        "- Every statement must be backed by a specific entry from the provided candidate set.\n"
        "- In the JSON output, provide a list of sources. Each source MUST contain `entryId`, `evidenceQuote`, and `relevanceReason`.\n"
        "- `entryId` MUST strictly match the exact `id` attribute of one of the provided `<journal_entry_untrusted>` tags.\n"
        "- If the provided entries do not contain sufficient evidence to answer the user's question, set `sufficientContext` to false and `sources` to empty array [].\n"
        "- Do NOT assume or invent facts not present in the entries."
    )

    prompt = (
        f"Available Journal Candidate Entries:\n{containment_corpus}\n\n"
        f"User Query:\n{clean_query}\n\n"
        "Respond with a JSON object with this exact schema:\n"
        "{\n"
        '  "answer": "string with clear, grounded answer",\n'
        '  "sufficientContext": true,\n'
        '  "sources": [\n'
        '    {\n'
        '      "entryId": "exact-entry-id",\n'
        '      "evidenceQuote": "exact quote from the entry content",\n'
        '      "relevanceReason": "why this entry supports the answer"\n'
        '    }\n'
        '  ]\n'
        "}"
    )

    # 5. Call Gemini
    raw_response = await generate_gemini_content(
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=0.1,
    )

    # 6. Parse and Validate Model Output
    try:
        # Strip potential markdown formatting (```json ... ```)
        clean_json = raw_response.strip()
        if clean_json.startswith("```"):
            clean_json = clean_json.split("\n", 1)[1]
            if clean_json.endswith("```"):
                clean_json = clean_json.rsplit("```", 1)[0]
            clean_json = clean_json.strip()

        parsed = json.loads(clean_json)
    except Exception as e:
        logger.error(f"Failed to parse Gemini JSON: {e}. Raw response: {raw_response[:200]}")
        return AskJournalResponse(
            answer=INSUFFICIENT_CONTEXT_MESSAGE,
            sources=[],
            sufficientContext=False,
            totalCandidatesAnalyzed=len(candidates),
            rejectedSourceCount=0,
        )

    model_answer = parsed.get("answer", "")
    model_sufficient = parsed.get("sufficientContext", False)
    raw_sources = parsed.get("sources", [])

    # 7. CRITICAL SECURITY VERIFICATION:
    # Gemini source IDs must be validated against the backend-authorized candidate set.
    # Gemini must NEVER be an authorization authority.
    verified_sources: List[EvidenceSource] = []
    rejected_count = 0

    if isinstance(raw_sources, list):
        for s in raw_sources:
            if not isinstance(s, dict):
                continue
            entry_id = str(s.get("entryId", "")).strip()

            # AUTHORIZATION CHECK: Is this entry ID in the backend-authorized candidate set?
            if entry_id in candidate_map:
                matched_entry = candidate_map[entry_id]
                date_str = datetime.fromtimestamp(matched_entry.createdAt / 1000).strftime("%b %d, %Y")
                quote = str(s.get("evidenceQuote", "")).strip()
                reason = str(s.get("relevanceReason", "")).strip()

                verified_sources.append(
                    EvidenceSource(
                        entryId=matched_entry.id,
                        title=matched_entry.title,
                        date=date_str,
                        evidenceQuote=quote if quote else matched_entry.content[:120] + "...",
                        relevanceReason=reason if reason else "Direct contextual reference",
                        mood=matched_entry.mood,
                    )
                )
            else:
                # Discarded: model returned an unverified or hallucinated ID
                logger.warning(f"Discarding unauthorized or hallucinated entry ID from Gemini response: {entry_id}")
                rejected_count += 1

    # 8. ZERO VALID EVIDENCE RULE:
    # If an answer has zero valid evidence, discard the answer and return an insufficient-context response.
    if len(verified_sources) == 0:
        logger.info(f"Zero verified evidence sources found for user {uid}. Discarding model answer.")
        return AskJournalResponse(
            answer=INSUFFICIENT_CONTEXT_MESSAGE,
            sources=[],
            sufficientContext=False,
            totalCandidatesAnalyzed=len(candidates),
            rejectedSourceCount=rejected_count,
        )

    return AskJournalResponse(
        answer=model_answer,
        sources=verified_sources,
        sufficientContext=model_sufficient and len(verified_sources) > 0,
        totalCandidatesAnalyzed=len(candidates),
        rejectedSourceCount=rejected_count,
    )
