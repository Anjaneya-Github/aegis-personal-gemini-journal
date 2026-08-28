"""
Input bounds validation and sanitization for Aegis Journal.
"""
from typing import List
from .errors import ValidationError
from .models import ChatMessage

MAX_QUERY_LENGTH = 500
MIN_QUERY_LENGTH = 2
MAX_ENTRY_CONTENT_LENGTH = 50000
MAX_ENTRY_TITLE_LENGTH = 200
MAX_CHAT_TURNS = 12
MAX_MESSAGE_CONTENT_LENGTH = 1500
MAX_CANDIDATE_ENTRIES_LIMIT = 30


def validate_query(query: str) -> str:
    """Validates that a search/ask query meets length constraints."""
    if not query:
        raise ValidationError("Query cannot be empty")
    cleaned = query.strip()
    if len(cleaned) < MIN_QUERY_LENGTH:
        raise ValidationError(f"Query must be at least {MIN_QUERY_LENGTH} characters long")
    if len(cleaned) > MAX_QUERY_LENGTH:
        raise ValidationError(f"Query exceeds maximum length of {MAX_QUERY_LENGTH} characters")
    return cleaned


def validate_chat_messages(messages: List[ChatMessage]) -> List[ChatMessage]:
    """Validates multi-turn chat message history bounds."""
    if not messages:
        raise ValidationError("Chat message list cannot be empty")
    if len(messages) > MAX_CHAT_TURNS:
        # Take the most recent allowed turns
        messages = messages[-MAX_CHAT_TURNS:]
    for m in messages:
        if not m.content.strip():
            raise ValidationError("Message content cannot be empty or whitespace only")
        if len(m.content) > MAX_MESSAGE_CONTENT_LENGTH:
            raise ValidationError(f"Message content exceeds {MAX_MESSAGE_CONTENT_LENGTH} characters")
    return messages


def calculate_word_count(text: str) -> int:
    """Calculates word count of text."""
    if not text:
        return 0
    words = text.split()
    return len(words)
