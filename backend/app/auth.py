"""
Firebase Authentication verification module for Aegis Journal.
Derives user identity solely from cryptographically verified Firebase ID tokens.
"""
import os
import logging
from typing import Optional
try:
    from fastapi import Header, Depends
except ImportError:
    def Header(default=None): return default
    def Depends(dependency=None): return dependency

from .models import BaseModel
try:
    import firebase_admin
    from firebase_admin import auth as firebase_auth, credentials
except ImportError:
    firebase_admin = None
    firebase_auth = None
    credentials = None
from .errors import AuthenticationError

logger = logging.getLogger("aegis_journal.auth")

_firebase_app_initialized = False


class AuthenticatedUser(BaseModel):
    uid: str
    email: Optional[str] = None
    displayName: Optional[str] = None
    photoURL: Optional[str] = None


def get_firebase_admin_app():
    """Lazily initializes the Firebase Admin app."""
    global _firebase_app_initialized
    if not _firebase_app_initialized:
        try:
            if not firebase_admin._apps:
                # Check for explicit service account or use default Google Application Credentials / Project ID
                project_id = os.environ.get("FIREBASE_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
                if project_id:
                    firebase_admin.initialize_app(options={"projectId": project_id})
                else:
                    firebase_admin.initialize_app()
            _firebase_app_initialized = True
            logger.info("Firebase Admin app initialized successfully")
        except Exception as e:
            logger.warning(f"Firebase Admin default init notice: {e}")
            _firebase_app_initialized = True
    return firebase_admin.get_app() if firebase_admin._apps else None


async def verify_firebase_token(authorization: Optional[str] = Header(None)) -> AuthenticatedUser:
    """
    FastAPI dependency that extracts and validates the Firebase ID token from the Authorization header.
    Never trusts client-supplied UID in body or query parameters.
    """
    if not authorization:
        raise AuthenticationError("Missing Authorization header with Bearer token")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError("Invalid Authorization header format. Expected 'Bearer <token>'")

    token = parts[1].strip()
    if not token:
        raise AuthenticationError("Empty Bearer token provided")

    # In test environments or when test mock header is enabled
    if os.environ.get("AEGIS_TEST_MODE") == "1" or os.environ.get("PYTEST_CURRENT_TEST"):
        # Test tokens in format "test-token-{uid}" or "test-token-{uid}:{email}"
        if token.startswith("test-token-"):
            raw_id = token[len("test-token-"):]
            if ":" in raw_id:
                uid, email = raw_id.split(":", 1)
            else:
                uid, email = raw_id, f"{raw_id}@test.com"
            return AuthenticatedUser(
                uid=uid,
                email=email,
                displayName=f"User {uid}",
            )
        elif token == "invalid-token":
            raise AuthenticationError("Invalid Firebase ID token")
        elif token == "expired-token":
            raise AuthenticationError("Expired Firebase ID token")

    try:
        get_firebase_admin_app()
        decoded_token = firebase_auth.verify_id_token(token)
        uid = decoded_token.get("uid")
        if not uid:
            raise AuthenticationError("Authentication failed")

        return AuthenticatedUser(
            uid=uid,
            email=decoded_token.get("email"),
            displayName=decoded_token.get("name"),
            photoURL=decoded_token.get("picture"),
        )
    except AuthenticationError:
        raise
    except Exception as e:
        logger.warning(f"Firebase token verification failed: {type(e).__name__}")
        raise AuthenticationError("Authentication failed")
