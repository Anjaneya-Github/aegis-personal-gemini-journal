"""
Gemini AI service integration using the official Google GenAI Python SDK.
Safely retrieves GEMINI_API_KEY from environment or Secret Manager.
"""
import os
import json
import logging
from typing import Optional, Dict, Any
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None
from .errors import GeminiServiceError

logger = logging.getLogger("aegis_journal.gemini")

_genai_client = None
DEFAULT_MODEL = "gemini-3.7-flash"


def get_gemini_api_key() -> Optional[str]:
    """
    Retrieves the Gemini API key from the environment.
    Falls back to Google Cloud Secret Manager if in a GCP environment.
    """
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key

    # Attempt to fetch from Google Cloud Secret Manager
    try:
        from google.cloud import secretmanager
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("FIREBASE_PROJECT_ID")
        if project_id:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project_id}/secrets/GEMINI_API_KEY/versions/latest"
            response = client.access_secret_version(request={"name": name})
            secret_value = response.payload.data.decode("UTF-8").strip()
            if secret_value:
                os.environ["GEMINI_API_KEY"] = secret_value
                return secret_value
    except Exception as e:
        logger.debug(f"Secret Manager lookup note: {e}")

    return None


def get_gemini_client() -> Any:
    """Lazily initializes and returns the Google GenAI client."""
    global _genai_client
    if _genai_client is None:
        api_key = get_gemini_api_key()
        if not api_key:
            # Allow instantiation without key for mock/test runs if needed
            if os.environ.get("AEGIS_TEST_MODE") == "1":
                return None
            raise GeminiServiceError("GEMINI_API_KEY is not configured on the server")
        _genai_client = genai.Client(api_key=api_key)
    return _genai_client


async def generate_gemini_content(
    prompt: str, 
    system_instruction: Optional[str] = None,
    temperature: float = 0.2,
    response_schema: Optional[Any] = None
) -> str:
    """
    Executes a content generation request with the Google GenAI SDK.
    """
    client = get_gemini_client()
    if client is None:
        # In test mode without API key, return a mock JSON structure
        return json.dumps({
            "answer": "Test response derived from verified candidate entries.",
            "sources": [],
            "sufficientContext": False
        })

    try:
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction,
            response_mime_type="application/json" if response_schema else None,
            response_schema=response_schema,
        )

        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=prompt,
            config=config,
        )

        if not response or not response.text:
            raise GeminiServiceError("Empty response returned by Gemini model")

        return response.text
    except Exception as e:
        logger.error(f"Gemini generation error: {e}")
        raise GeminiServiceError(f"Gemini synthesis failed: {str(e)}")
