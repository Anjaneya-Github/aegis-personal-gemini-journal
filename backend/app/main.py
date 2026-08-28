"""
Aegis Journal - Secure FastAPI Application Entrypoint.
Enforces authentic Firebase user identity, prompt injection defenses, and strict evidence verification.
"""
import os
import time
import logging
from typing import Optional
from fastapi import FastAPI, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .models import (
    JournalEntryCreate,
    JournalEntryUpdate,
    JournalEntryResponse,
    JournalEntryListResponse,
    ChatRequest,
    ChatResponse,
    SummarizeRequest,
    SummarizeResponse,
    AskJournalRequest,
    AskJournalResponse,
    ReflectionResponse,
    TimelineResponse,
    DecisionMemoryResponse,
    ContradictionDetectionResponse,
    PersonalEvolutionRequest,
    PersonalEvolutionResponse,
    Insight,
    SuggestedAction,
    EvidenceReference,
    ApprovedAction,
    InsightAnalysisRequest,
    InsightAnalysisResponse,
    InsightActionApprovalRequest,
    InsightActionRejectRequest,
    ApprovedActionListResponse,
    MemoryIntegrityStats,
    SecuritySOCStatusResponse,
    ServerHealthResponse,
    MoodType,
)
from .auth import verify_firebase_token, AuthenticatedUser
from .journal import (
    create_journal_entry,
    list_journal_entries,
    get_journal_entry,
    update_journal_entry,
    delete_journal_entry,
)
from .ask_journal import execute_ask_journal
from .reflection import generate_journal_reflection
from .chat import handle_companion_chat, handle_conversation_summary
from .timeline import generate_journal_timeline
from .memory_intelligence import (
    extract_decision_memory,
    detect_contradictions,
    analyze_personal_evolution,
    get_current_integrity_stats,
    get_security_soc_status,
)
from .action_engine import (
    analyze_personal_actions_and_insights,
    approve_personal_action,
    reject_personal_action,
    list_approved_actions,
    delete_approved_action,
)
from .gemini_service import get_gemini_api_key
from .errors import (
    AegisJournalException,
    RateLimitError,
    aegis_exception_handler,
    general_exception_handler,
)
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Configure sanitized logging - never log sensitive tokens or payload contents
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("aegis_journal.main")

app = FastAPI(
    title="Aegis Journal API",
    description="Secure, Evidence-Backed Personal AI Journal with Firebase Authentication",
    version="1.0.0",
)

# Exception Handlers
app.add_exception_handler(AegisJournalException, aegis_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

from .rate_limiter import (
    limiter,
    RATE_LIMIT_WINDOW_SECONDS,
    MAX_AI_REQUESTS_PER_WINDOW,
    MAX_STANDARD_REQUESTS_PER_WINDOW,
)


class SecurityAndRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Rate limiting on all application endpoints (stricter tier on AI routes)
        path = request.url.path
        if path.startswith("/api/") or path.startswith("/users/"):
            client_ip = request.client.host if request.client else "unknown"
            auth_header = request.headers.get("authorization", "")
            
            is_allowed, retry_after, remaining = await limiter.check_rate_limit(
                client_ip=client_ip,
                path=path,
                auth_header=auth_header
            )
            if not is_allowed:
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "detail": f"Too many requests. Please retry in {retry_after} seconds.",
                        "retryAfter": retry_after,
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(MAX_AI_REQUESTS_PER_WINDOW if "insights" in path or "memory" in path or "ask" in path or "reflect" in path or "chat" in path else MAX_STANDARD_REQUESTS_PER_WINDOW),
                        "X-RateLimit-Remaining": str(remaining),
                    }
                )

        # 2. Process request
        response = await call_next(request)

        # 3. Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        return response


app.add_middleware(SecurityAndRateLimitMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def root_health_check():
    """Unauthenticated health probe for Cloud Run and orchestrator probes."""
    return {"status": "ok"}


@app.get("/api/health", response_model=ServerHealthResponse)
async def health_check():
    """Returns server health and service configuration status without leaking keys."""
    gemini_configured = bool(get_gemini_api_key())
    firestore_configured = bool(
        os.environ.get("FIREBASE_PROJECT_ID") or 
        os.environ.get("GOOGLE_CLOUD_PROJECT") or 
        os.environ.get("FIRESTORE_DATABASE_ID")
    )
    return ServerHealthResponse(
        status="ok",
        timestamp=int(time.time() * 1000),
        service="Aegis Journal FastAPI Backend",
        geminiConfigured=gemini_configured,
        firestoreConfigured=firestore_configured,
    )



# -------------------------------------------------------------
# Journal Entries CRUD Endpoints
# -------------------------------------------------------------

@app.get("/api/journal/entries", response_model=JournalEntryListResponse)
async def get_entries(
    limit: int = Query(default=100, ge=1, le=100),
    mood: Optional[MoodType] = None,
    tag: Optional[str] = None,
    user: AuthenticatedUser = Depends(verify_firebase_token),
):
    """Lists entries for the authenticated user only."""
    return await list_journal_entries(uid=user.uid, limit=limit, mood=mood, tag=tag)


@app.post("/api/journal/entries", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_entry(
    payload: JournalEntryCreate,
    user: AuthenticatedUser = Depends(verify_firebase_token),
):
    """Creates a new journal entry under users/{uid}/entries/{id}."""
    logger.info(f"Creating journal entry for user {user.uid}")
    return await create_journal_entry(uid=user.uid, data=payload)


@app.get("/api/journal/entries/{entry_id}", response_model=JournalEntryResponse)
async def get_entry_by_id(
    entry_id: str,
    user: AuthenticatedUser = Depends(verify_firebase_token),
):
    """Retrieves a specific journal entry for the authenticated user only."""
    return await get_journal_entry(uid=user.uid, entry_id=entry_id)


@app.put("/api/journal/entries/{entry_id}", response_model=JournalEntryResponse)
async def update_entry_by_id(
    entry_id: str,
    payload: JournalEntryUpdate,
    user: AuthenticatedUser = Depends(verify_firebase_token),
):
    """Updates a journal entry for the authenticated user only."""
    logger.info(f"Updating entry {entry_id} for user {user.uid}")
    return await update_journal_entry(uid=user.uid, entry_id=entry_id, data=payload)


@app.delete("/api/journal/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry_by_id(
    entry_id: str,
    user: AuthenticatedUser = Depends(verify_firebase_token),
):
    """Deletes a journal entry for the authenticated user only."""
    logger.info(f"Deleting entry {entry_id} for user {user.uid}")
    await delete_journal_entry(uid=user.uid, entry_id=entry_id)
    return None


# -------------------------------------------------------------
# AI Intelligence Endpoints
# -------------------------------------------------------------

@app.post("/api/journal/chat", response_model=ChatResponse)
async def companion_chat_endpoint(
    payload: ChatRequest,
    user: AuthenticatedUser = Depends(verify_firebase_token),
):
    """Multi-turn reflective dialogue with the personal journal companion."""
    logger.info(f"Processing companion chat turn for user {user.uid}")
    return await handle_companion_chat(payload)


@app.post("/api/journal/summarize", response_model=SummarizeResponse)
async def summarize_dialogue_endpoint(
    payload: SummarizeRequest,
    user: AuthenticatedUser = Depends(verify_firebase_token),
):
    """Summarizes a companion dialogue into a structured journal draft."""
    logger.info(f"Summarizing dialogue for user {user.uid}")
    return await handle_conversation_summary(payload)


@app.post("/api/journal/ask", response_model=AskJournalResponse)
async def ask_journal_endpoint(
    payload: AskJournalRequest,
    user: AuthenticatedUser = Depends(verify_firebase_token),
):
    """Evidence-backed inquiry across bounded candidate entries with strict authorization verification."""
    logger.info(f"Executing Ask My Journal for user {user.uid}")
    return await execute_ask_journal(uid=user.uid, request_data=payload)


@app.api_route("/api/journal/reflect", methods=["GET", "POST"], response_model=ReflectionResponse)
async def reflection_endpoint(
    user: AuthenticatedUser = Depends(verify_firebase_token),
):
    """Generates longitudinal insights and growth themes backed by verified entry citations."""
    logger.info(f"Generating reflection insights for user {user.uid}")
    return await generate_journal_reflection(uid=user.uid)


@app.get("/api/journal/timeline", response_model=TimelineResponse)
async def timeline_endpoint(
    user: AuthenticatedUser = Depends(verify_firebase_token),
):
    """Computes emotional progression, milestones, and theme distribution."""
    logger.info(f"Generating timeline for user {user.uid}")
    return await generate_journal_timeline(uid=user.uid)


# -------------------------------------------------------------
# Aegis Memory Intelligence Endpoints
# -------------------------------------------------------------

@app.api_route("/api/memory/decisions", methods=["GET", "POST"], response_model=DecisionMemoryResponse)
async def decision_memory_endpoint(
    user: AuthenticatedUser = Depends(verify_firebase_token),
):
    """Extracts explicit user decisions backed strictly by verified candidate journal entries."""
    logger.info(f"Extracting Decision Memory for user {user.uid}")
    return await extract_decision_memory(uid=user.uid)


@app.api_route("/api/memory/contradictions", methods=["GET", "POST"], response_model=ContradictionDetectionResponse)
async def contradictions_endpoint(
    user: AuthenticatedUser = Depends(verify_firebase_token),
):
    """Detects potential evolving stances/tensions with dual-entry verified evidence."""
    logger.info(f"Detecting Contradictions for user {user.uid}")
    return await detect_contradictions(uid=user.uid)


@app.post("/api/memory/evolution", response_model=PersonalEvolutionResponse)
async def personal_evolution_endpoint(
    payload: PersonalEvolutionRequest = PersonalEvolutionRequest(),
    user: AuthenticatedUser = Depends(verify_firebase_token),
):
    """Synthesizes longitudinal personal evolution with verified citations."""
    logger.info(f"Analyzing Personal Evolution for user {user.uid}")
    return await analyze_personal_evolution(uid=user.uid, request_data=payload)


@app.get("/api/memory/integrity", response_model=MemoryIntegrityStats)
async def memory_integrity_endpoint(
    user: AuthenticatedUser = Depends(verify_firebase_token),
):
    """Returns real evidence verification metrics and integrity counters."""
    return get_current_integrity_stats()


@app.get("/api/security/soc", response_model=SecuritySOCStatusResponse)
async def security_soc_endpoint(
    user: AuthenticatedUser = Depends(verify_firebase_token),
):
    """Returns live security posture, architectural audit checks, and zero-trust verification status."""
    return get_security_soc_status(uid=user.uid)


# -------------------------------------------------------------
# Personal AI Action & Insight Engine Endpoints
# -------------------------------------------------------------

@app.post("/api/insights/analyze", response_model=InsightAnalysisResponse)
@app.post("/users/me/insights/analyze", response_model=InsightAnalysisResponse)
async def analyze_insights_endpoint(
    payload: InsightAnalysisRequest = InsightAnalysisRequest(),
    user: AuthenticatedUser = Depends(verify_firebase_token),
):
    """
    Executes Personal AI Action & Insight Engine on authenticated user's bounded entries.
    Zero-evidence rule enforced; Gemini cannot authorize documents or bypass verification.
    """
    logger.info(f"Analyzing AI Actions & Insights for user {user.uid}")
    return await analyze_personal_actions_and_insights(uid=user.uid, request_data=payload)


@app.get("/api/insights", response_model=ApprovedActionListResponse)
@app.get("/users/me/insights", response_model=ApprovedActionListResponse)
@app.get("/api/insights/actions", response_model=ApprovedActionListResponse)
@app.get("/users/me/insights/actions", response_model=ApprovedActionListResponse)
async def list_actions_endpoint(
    user: AuthenticatedUser = Depends(verify_firebase_token),
):
    """Lists persisted, user-approved action commitments."""
    return await list_approved_actions(uid=user.uid)


@app.post("/api/insights/{insight_id}/approve", response_model=ApprovedAction)
@app.post("/users/me/insights/{insight_id}/approve", response_model=ApprovedAction)
async def approve_action_endpoint(
    insight_id: str,
    payload: Optional[InsightActionApprovalRequest] = None,
    user: AuthenticatedUser = Depends(verify_firebase_token),
):
    """
    Human-in-the-loop: Approves or modifies a suggested action, persisting it to user's actions collection.
    """
    logger.info(f"User {user.uid} approving insight action {insight_id}")
    return await approve_personal_action(uid=user.uid, insight_id=insight_id, request_data=payload)


@app.post("/api/insights/{insight_id}/reject")
@app.post("/users/me/insights/{insight_id}/reject")
async def reject_action_endpoint(
    insight_id: str,
    payload: Optional[InsightActionRejectRequest] = None,
    user: AuthenticatedUser = Depends(verify_firebase_token),
):
    """
    Human-in-the-loop: Explicitly rejects a suggested action.
    """
    logger.info(f"User {user.uid} rejecting insight action {insight_id}")
    return await reject_personal_action(uid=user.uid, insight_id=insight_id, request_data=payload)


@app.delete("/api/insights/actions/{action_id}")
@app.delete("/users/me/insights/actions/{action_id}")
async def delete_action_endpoint(
    action_id: str,
    user: AuthenticatedUser = Depends(verify_firebase_token),
):
    """
    Deletes an approved user action. Scoped strictly to authenticated UID.
    """
    logger.info(f"User {user.uid} deleting action {action_id}")
    return await delete_approved_action(uid=user.uid, action_id=action_id)


# Static frontend hosting if dist directory exists (e.g. in container deployment)
dist_dir = os.path.join(os.getcwd(), "dist")
if os.path.isdir(dist_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(dist_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_dir, "index.html"))
