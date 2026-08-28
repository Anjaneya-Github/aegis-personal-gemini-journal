"""
Firestore journal entry management with strict user-partitioned isolation.
Collection path: users/{uid}/entries/{entryId}
"""
import os
import time
import uuid
import logging
from typing import List, Optional, Dict, Any
from google.cloud import firestore
from .models import (
    JournalEntryCreate, 
    JournalEntryUpdate, 
    JournalEntryResponse, 
    JournalEntryListResponse,
    MoodType
)
from .errors import NotFoundError, AuthorizationError
from .validation import calculate_word_count

logger = logging.getLogger("aegis_journal.journal")

_firestore_client = None
# In-memory store for testing or offline dev environments
_memory_store: Dict[str, Dict[str, Dict[str, Any]]] = {}


def get_firestore_client():
    """Lazily gets or initializes the Firestore client."""
    global _firestore_client
    if _firestore_client is None:
        try:
            database_id = os.environ.get("FIRESTORE_DATABASE_ID") or "ai-studio-6cb3b1bb-cf5b-4920-960c-7ddf5e0901f1"
            project_id = os.environ.get("FIREBASE_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
            if project_id and database_id:
                _firestore_client = firestore.Client(project=project_id, database=database_id)
            else:
                _firestore_client = firestore.Client()
        except Exception as e:
            logger.warning(f"Firestore Client initialization note: {e}. Using partitioned repository.")
    return _firestore_client


def is_memory_mode() -> bool:
    """Checks whether to use memory store (in test mode or when Firestore client is unavailable)."""
    return os.environ.get("AEGIS_TEST_MODE") == "1" or os.environ.get("USE_MEMORY_STORE") == "1"


def reset_memory_store():
    """Resets memory store for unit testing."""
    global _memory_store
    _memory_store = {}


async def create_journal_entry(uid: str, data: JournalEntryCreate) -> JournalEntryResponse:
    """Creates a new journal entry under users/{uid}/entries/{entryId}."""
    entry_id = str(uuid.uuid4())
    now_ms = int(time.time() * 1000)
    word_count = calculate_word_count(data.content)

    doc_data = {
        "id": entry_id,
        "userId": uid,
        "title": data.title,
        "content": data.content,
        "mood": data.mood,
        "tags": data.tags,
        "wordCount": word_count,
        "createdAt": now_ms,
        "updatedAt": now_ms,
    }

    if is_memory_mode():
        if uid not in _memory_store:
            _memory_store[uid] = {}
        _memory_store[uid][entry_id] = doc_data
        return JournalEntryResponse(**doc_data)

    try:
        client = get_firestore_client()
        if client:
            doc_ref = client.collection("users").document(uid).collection("entries").document(entry_id)
            doc_ref.set(doc_data)
            return JournalEntryResponse(**doc_data)
    except Exception as e:
        logger.warning(f"Live Firestore write failed: {e}. Fallback to memory store.")

    if uid not in _memory_store:
        _memory_store[uid] = {}
    _memory_store[uid][entry_id] = doc_data
    return JournalEntryResponse(**doc_data)


async def list_journal_entries(
    uid: str, 
    limit: int = 100, 
    mood: Optional[MoodType] = None, 
    tag: Optional[str] = None
) -> JournalEntryListResponse:
    """Lists entries for the authenticated user only, sorted by createdAt descending."""
    results: List[Dict[str, Any]] = []

    if not is_memory_mode():
        try:
            client = get_firestore_client()
            if client:
                query = (
                    client.collection("users")
                    .document(uid)
                    .collection("entries")
                    .order_by("createdAt", direction=firestore.Query.DESCENDING)
                    .limit(limit)
                )
                docs = query.stream()
                for doc in docs:
                    d = doc.to_dict()
                    if d:
                        results.append(d)
        except Exception as e:
            logger.warning(f"Live Firestore list failed: {e}. Using memory store.")

    if not results and uid in _memory_store:
        user_entries = list(_memory_store[uid].values())
        user_entries.sort(key=lambda x: x.get("createdAt", 0), reverse=True)
        results = user_entries[:limit]

    # Filter by mood and tag if provided
    filtered = []
    for r in results:
        if mood and r.get("mood") != mood:
            continue
        if tag and tag.lower() not in [t.lower() for t in r.get("tags", [])]:
            continue
        filtered.append(JournalEntryResponse(**r))

    return JournalEntryListResponse(entries=filtered, total=len(filtered))


async def get_journal_entry(uid: str, entry_id: str) -> JournalEntryResponse:
    """Retrieves a single journal entry for the authenticated user only."""
    if not is_memory_mode():
        try:
            client = get_firestore_client()
            if client:
                doc_ref = client.collection("users").document(uid).collection("entries").document(entry_id)
                doc = doc_ref.get()
                if doc.exists:
                    d = doc.to_dict()
                    if d and d.get("userId") == uid:
                        return JournalEntryResponse(**d)
                    raise NotFoundError(f"Entry {entry_id} not found")
        except NotFoundError:
            raise
        except Exception as e:
            logger.warning(f"Live Firestore get failed: {e}")

    if uid in _memory_store and entry_id in _memory_store[uid]:
        return JournalEntryResponse(**_memory_store[uid][entry_id])

    raise NotFoundError(f"Entry {entry_id} not found for this user")


async def update_journal_entry(uid: str, entry_id: str, data: JournalEntryUpdate) -> JournalEntryResponse:
    """Updates an existing journal entry for the authenticated user only."""
    existing = await get_journal_entry(uid, entry_id)

    updated_data = existing.model_dump()
    if data.title is not None:
        updated_data["title"] = data.title
    if data.content is not None:
        updated_data["content"] = data.content
        updated_data["wordCount"] = calculate_word_count(data.content)
    if data.mood is not None:
        updated_data["mood"] = data.mood
    if data.tags is not None:
        updated_data["tags"] = data.tags

    updated_data["updatedAt"] = int(time.time() * 1000)

    if not is_memory_mode():
        try:
            client = get_firestore_client()
            if client:
                doc_ref = client.collection("users").document(uid).collection("entries").document(entry_id)
                doc_ref.set(updated_data)
        except Exception as e:
            logger.warning(f"Live Firestore update failed: {e}")

    if uid not in _memory_store:
        _memory_store[uid] = {}
    _memory_store[uid][entry_id] = updated_data

    return JournalEntryResponse(**updated_data)


async def delete_journal_entry(uid: str, entry_id: str) -> None:
    """Deletes a journal entry for the authenticated user only."""
    # Ensure entry exists and belongs to user
    await get_journal_entry(uid, entry_id)

    if not is_memory_mode():
        try:
            client = get_firestore_client()
            if client:
                doc_ref = client.collection("users").document(uid).collection("entries").document(entry_id)
                doc_ref.delete()
        except Exception as e:
            logger.warning(f"Live Firestore delete failed: {e}")

    if uid in _memory_store and entry_id in _memory_store[uid]:
        del _memory_store[uid][entry_id]
