"""
Chronological Timeline and Emotional Progression Engine for Aegis Journal.
"""
import logging
from typing import Dict, List
from collections import Counter
from datetime import datetime

from .models import (
    TimelineResponse,
    TimelineItem,
    TimelineMilestone,
    JournalEntryResponse,
    MoodType
)
from .journal import list_journal_entries

logger = logging.getLogger("aegis_journal.timeline")


async def generate_journal_timeline(uid: str) -> TimelineResponse:
    """
    Computes chronological timeline, sentiment progression, dominant themes, and key milestones.
    """
    list_res = await list_journal_entries(uid=uid, limit=100)
    entries: List[JournalEntryResponse] = list_res.entries

    if not entries:
        return TimelineResponse(
            totalEntries=0,
            items=[],
            milestones=[],
            dominantThemes=[],
            moodDistribution={
                "radiant": 0,
                "serene": 0,
                "reflective": 0,
                "anxious": 0,
                "melancholy": 0,
                "grateful": 0,
                "neutral": 0,
            }
        )

    # Sort entries chronologically (oldest to newest for progression, or newest for feed)
    items: List[TimelineItem] = []
    mood_counter = Counter()
    tag_counter = Counter()

    for e in entries:
        mood_counter[e.mood] += 1
        for t in e.tags:
            tag_counter[t.lower()] += 1

        date_str = datetime.fromtimestamp(e.createdAt / 1000).strftime("%b %d, %Y")
        snippet = e.content[:140] + "..." if len(e.content) > 140 else e.content

        items.append(
            TimelineItem(
                entryId=e.id,
                title=e.title,
                snippet=snippet,
                mood=e.mood,
                date=date_str,
                timestamp=e.createdAt,
                tags=e.tags,
                wordCount=e.wordCount,
            )
        )

    dominant_themes = [tag for tag, _ in tag_counter.most_common(5)]

    # Generate milestones from highest significance or first/milestone entries
    milestones: List[TimelineMilestone] = []
    chronological = sorted(entries, key=lambda x: x.createdAt)

    if chronological:
        # First entry milestone
        first = chronological[0]
        first_date = datetime.fromtimestamp(first.createdAt / 1000).strftime("%b %d, %Y")
        milestones.append(
            TimelineMilestone(
                date=first_date,
                title="First Journal Reflection",
                description=f"Embarked on journaling journey with '{first.title}'.",
                mood=first.mood,
                relatedEntryId=first.id,
            )
        )

        # Grateful or Radiant breakthrough milestones
        for entry in chronological[1:]:
            if entry.mood in ["radiant", "grateful"] and len(milestones) < 4:
                m_date = datetime.fromtimestamp(entry.createdAt / 1000).strftime("%b %d, %Y")
                milestones.append(
                    TimelineMilestone(
                        date=m_date,
                        title=entry.title,
                        description=f"Moment of clarity and gratitude ({entry.mood}).",
                        mood=entry.mood,
                        relatedEntryId=entry.id,
                    )
                )

    mood_dist: Dict[str, int] = {
        "radiant": mood_counter.get("radiant", 0),
        "serene": mood_counter.get("serene", 0),
        "reflective": mood_counter.get("reflective", 0),
        "anxious": mood_counter.get("anxious", 0),
        "melancholy": mood_counter.get("melancholy", 0),
        "grateful": mood_counter.get("grateful", 0),
        "neutral": mood_counter.get("neutral", 0),
    }

    return TimelineResponse(
        totalEntries=len(entries),
        items=items,
        milestones=milestones,
        dominantThemes=dominant_themes,
        moodDistribution=mood_dist,
    )
