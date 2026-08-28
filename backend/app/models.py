"""
Pydantic data models for requests, responses, and internal entities.
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator


MoodType = Literal["radiant", "serene", "reflective", "anxious", "melancholy", "grateful", "neutral"]


class UserProfile(BaseModel):
    uid: str
    email: Optional[str] = None
    displayName: Optional[str] = None
    photoURL: Optional[str] = None


class JournalEntryCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Entry title")
    content: str = Field(..., min_length=1, max_length=50000, description="Entry body content")
    mood: MoodType = Field(default="serene", description="Sentiment indicator")
    tags: List[str] = Field(default_factory=list, max_length=20, description="Associated thematic tags")

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, v: List[str]) -> List[str]:
        cleaned = []
        for tag in v:
            clean = tag.strip().lower().replace("#", "")
            if clean and len(clean) <= 50 and clean not in cleaned:
                cleaned.append(clean)
        return cleaned[:20]


class JournalEntryUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1, max_length=50000)
    mood: Optional[MoodType] = None
    tags: Optional[List[str]] = Field(None, max_length=20)

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return None
        cleaned = []
        for tag in v:
            clean = tag.strip().lower().replace("#", "")
            if clean and len(clean) <= 50 and clean not in cleaned:
                cleaned.append(clean)
        return cleaned[:20]


class JournalEntryResponse(BaseModel):
    id: str
    userId: str
    title: str
    content: str
    mood: MoodType
    tags: List[str]
    wordCount: int
    createdAt: int
    updatedAt: int


class JournalEntryListResponse(BaseModel):
    entries: List[JournalEntryResponse]
    total: int


class ChatMessage(BaseModel):
    role: Literal["user", "model", "system"]
    content: str = Field(..., min_length=1, max_length=1500)


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., min_length=1, max_length=12)
    currentDraft: Optional[str] = Field(None, max_length=5000)


class ChatResponse(BaseModel):
    content: str
    suggestedFollowUps: Optional[List[str]] = Field(default_factory=list)


class SummarizeRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., min_length=1, max_length=24)


class SummarizeResponse(BaseModel):
    title: str
    content: str
    mood: MoodType
    tags: List[str]
    keyTakeaways: List[str] = Field(default_factory=list)


class AskJournalRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)


class EvidenceSource(BaseModel):
    entryId: str
    title: str
    date: str
    evidenceQuote: str
    relevanceReason: str
    mood: MoodType


class AskJournalResponse(BaseModel):
    answer: str
    sources: List[EvidenceSource]
    sufficientContext: bool
    totalCandidatesAnalyzed: int
    rejectedSourceCount: int = 0


class EvidenceCitation(BaseModel):
    entryId: str
    entryTitle: str
    quote: str


class GrowthTheme(BaseModel):
    theme: str
    insight: str
    evidence: List[EvidenceCitation] = Field(default_factory=list)


class ReflectionResponse(BaseModel):
    overallNarrative: str
    sentimentArc: str
    growthThemes: List[GrowthTheme]
    suggestedPrompt: str
    totalEntriesAnalyzed: int


class TimelineMilestone(BaseModel):
    date: str
    title: str
    description: str
    mood: MoodType
    relatedEntryId: Optional[str] = None


class TimelineItem(BaseModel):
    entryId: str
    title: str
    snippet: str
    mood: MoodType
    date: str
    timestamp: int
    tags: List[str]
    wordCount: int


class TimelineResponse(BaseModel):
    totalEntries: int
    items: List[TimelineItem]
    milestones: List[TimelineMilestone]
    dominantThemes: List[str]
    moodDistribution: Dict[str, int]


# -------------------------------------------------------------
# Aegis Memory Intelligence Models
# -------------------------------------------------------------

class DecisionItem(BaseModel):
    decisionId: str
    decision: str
    reasoning: str
    date: str
    status: Literal["active", "completed", "superseded", "revisited"] = "active"
    evidenceIds: List[str]
    confidence: Literal["high", "moderate", "tentative"] = "high"
    entryTitle: Optional[str] = None
    evidenceQuote: Optional[str] = None


class DecisionMemoryResponse(BaseModel):
    decisions: List[DecisionItem]
    totalDecisions: int
    verifiedEvidenceCount: int
    rejectedEvidenceCount: int
    sufficientContext: bool
    summary: str


class ContradictionItem(BaseModel):
    contradictionId: str
    topic: str
    earlierStatement: str
    laterStatement: str
    earlierEntryId: str
    laterEntryId: str
    earlierDate: str
    laterDate: str
    evidenceIds: List[str]
    confidence: Literal["high", "moderate", "tentative"] = "high"
    neutralAnalysis: str


class ContradictionDetectionResponse(BaseModel):
    contradictions: List[ContradictionItem]
    totalDetected: int
    verifiedEvidenceCount: int
    rejectedEvidenceCount: int
    sufficientContext: bool
    disclaimer: str = "Neutral algorithmic detection of evolving perspectives. Not psychological diagnosis."


class PersonalEvolutionItem(BaseModel):
    theme: str
    trend: str
    earlierPhase: str
    laterPhase: str
    timePeriod: str
    confidence: Literal["high", "moderate", "tentative"] = "high"
    supportingEvidence: List[EvidenceCitation] = Field(default_factory=list)


class PersonalEvolutionRequest(BaseModel):
    query: Optional[str] = Field(default=None, max_length=500)
    timeframeDays: Optional[int] = Field(default=90, ge=7, le=365)


class PersonalEvolutionResponse(BaseModel):
    synthesis: str
    trajectorySummary: str
    evolutionItems: List[PersonalEvolutionItem]
    totalEntriesAnalyzed: int
    verifiedEvidenceCount: int
    rejectedEvidenceCount: int
    sufficientContext: bool


class MemoryIntegrityStats(BaseModel):
    totalClaimsAnalyzed: int
    authorizedEvidenceVerified: int
    unauthorizedEvidenceRejected: int
    unsupportedClaimsDiscarded: int
    verifiedEvidencePercentage: float
    tenantIsolationStatus: str = "ENFORCED"
    zeroEvidenceEnforcement: str = "ACTIVE"


class SecurityAuditItem(BaseModel):
    category: str
    name: str
    status: Literal["PASS", "ACTIVE", "ENFORCED"]
    details: str
    testVerified: bool = True


class SecuritySOCStatusResponse(BaseModel):
    systemStatus: str
    timestamp: int
    audits: List[SecurityAuditItem]
    integrityStats: MemoryIntegrityStats


class ServerHealthResponse(BaseModel):
    status: str
    timestamp: int
    service: str
    geminiConfigured: bool
    firestoreConfigured: bool

