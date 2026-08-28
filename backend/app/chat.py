"""
Interactive Reflective Companion and Conversation Summarizer for Aegis Journal.
"""
import json
import logging
from typing import List, Optional
from .models import (
    ChatRequest, 
    ChatResponse, 
    SummarizeRequest, 
    SummarizeResponse,
    ChatMessage
)
from .gemini_service import generate_gemini_content
from .security_guard import assert_safe_query, PROMPT_SECURITY_PREAMBLE
from .validation import validate_chat_messages

logger = logging.getLogger("aegis_journal.chat")


async def handle_companion_chat(request_data: ChatRequest) -> ChatResponse:
    """
    Handles a multi-turn mindful companion dialogue turn.
    """
    # 1. Validate messages
    messages = validate_chat_messages(request_data.messages)

    # 2. Check for prompt injection in the latest user message
    for msg in messages:
        if msg.role == "user":
            assert_safe_query(msg.content)

    # 3. Format conversation history
    formatted_dialogue = []
    for msg in messages:
        speaker = "User" if msg.role == "user" else "Companion"
        formatted_dialogue.append(f"{speaker}: {msg.content}")

    dialogue_str = "\n".join(formatted_dialogue)
    draft_context = f"\nCurrent Draft Working Text:\n{request_data.currentDraft}" if request_data.currentDraft else ""

    system_instruction = (
        f"{PROMPT_SECURITY_PREAMBLE}\n\n"
        "You are an empathetic, insightful, and non-judgmental personal journaling companion.\n"
        "Your role is to help the user unpack their emotions, clarify their thoughts, and gain peace of mind through Socratic and compassionate inquiry.\n"
        "Rules:\n"
        "- Be concise, warm, and grounding (2-4 sentences).\n"
        "- Never judge, lecture, or tell the user how they should feel.\n"
        "- Offer 2 short, thoughtful follow-up questions to help them reflect deeper.\n"
        "- Output your response in structured JSON."
    )

    prompt = (
        f"Conversation History:\n{dialogue_str}{draft_context}\n\n"
        "Respond in JSON matching this schema:\n"
        "{\n"
        '  "content": "Warm reflective reply to the user",\n'
        '  "suggestedFollowUps": ["Follow-up question 1?", "Follow-up question 2?"]\n'
        "}"
    )

    raw_response = await generate_gemini_content(
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=0.7,
    )

    try:
        clean_json = raw_response.strip()
        if clean_json.startswith("```"):
            clean_json = clean_json.split("\n", 1)[1]
            if clean_json.endswith("```"):
                clean_json = clean_json.rsplit("```", 1)[0]
            clean_json = clean_json.strip()

        parsed = json.loads(clean_json)
        return ChatResponse(
            content=parsed.get("content", "I am here with you. What else comes up as you sit with this?"),
            suggestedFollowUps=parsed.get("suggestedFollowUps", []),
        )
    except Exception as e:
        logger.warning(f"Fallback to plain response parsing: {e}")
        return ChatResponse(
            content=raw_response.strip(),
            suggestedFollowUps=["How does that feel in your body right now?", "What would bring you ease today?"],
        )


async def handle_conversation_summary(request_data: SummarizeRequest) -> SummarizeResponse:
    """
    Summarizes a conversation session into a structured journal entry draft.
    """
    messages = request_data.messages
    for msg in messages:
        if msg.role == "user":
            assert_safe_query(msg.content)

    formatted_dialogue = []
    for msg in messages:
        speaker = "User" if msg.role == "user" else "Companion"
        formatted_dialogue.append(f"{speaker}: {msg.content}")

    dialogue_str = "\n".join(formatted_dialogue)

    system_instruction = (
        f"{PROMPT_SECURITY_PREAMBLE}\n\n"
        "You are an expert synthesizer of personal reflections.\n"
        "Distill the provided conversation into a beautifully written, first-person journal entry capturing the core insights, emotional tone, and takeaways.\n"
        "Select an appropriate mood from: ['radiant', 'serene', 'reflective', 'anxious', 'melancholy', 'grateful', 'neutral']."
    )

    prompt = (
        f"Conversation to Summarize:\n{dialogue_str}\n\n"
        "Respond in JSON matching this schema:\n"
        "{\n"
        '  "title": "Evocative, concise title",\n'
        '  "content": "Rich first-person journal entry synthesized from the dialogue",\n'
        '  "mood": "serene",\n'
        '  "tags": ["mindfulness", "growth"],\n'
        '  "keyTakeaways": ["Key insight 1", "Key insight 2"]\n'
        "}"
    )

    raw_response = await generate_gemini_content(
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=0.3,
    )

    try:
        clean_json = raw_response.strip()
        if clean_json.startswith("```"):
            clean_json = clean_json.split("\n", 1)[1]
            if clean_json.endswith("```"):
                clean_json = clean_json.rsplit("```", 1)[0]
            clean_json = clean_json.strip()

        parsed = json.loads(clean_json)
        mood_candidate = parsed.get("mood", "reflective").lower()
        valid_moods = ["radiant", "serene", "reflective", "anxious", "melancholy", "grateful", "neutral"]
        mood = mood_candidate if mood_candidate in valid_moods else "reflective"

        return SummarizeResponse(
            title=parsed.get("title", "Reflections from Companion Dialogue"),
            content=parsed.get("content", "Today I explored my thoughts with the journal companion..."),
            mood=mood,
            tags=parsed.get("tags", ["reflection"]),
            keyTakeaways=parsed.get("keyTakeaways", []),
        )
    except Exception as e:
        logger.error(f"Summarization parsing error: {e}")
        return SummarizeResponse(
            title="Reflections from Today",
            content="Summary of dialogue:\n" + "\n".join([f"- {m.content}" for m in messages if m.role == 'user']),
            mood="reflective",
            tags=["dialogue", "reflection"],
            keyTakeaways=["Captured raw conversational insights."],
        )
