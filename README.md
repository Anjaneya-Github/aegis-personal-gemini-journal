# Aegis Journal — Zero-Trust Personal AI Journal & Memory Intelligence

> **Production Hackathon Edition**  
> *Private, authenticated personal journal with AI-guided reflections, multi-tenant Firestore containment, and zero-trust memory intelligence.*

---

## 🏛️ Core Architecture

Aegis Journal follows a strict **Zero-Trust Security & Evidence Bounding** architecture:

```
Browser (Pure JavaScript / React SPA)
  ↓ Firebase Auth (Google OAuth & Cryptographic ID Tokens)
Firebase ID Token (Header: Authorization: Bearer <token>)
  ↓
FastAPI Backend (Python 3.12)
  ↓ Token Verification & Tenant UID Derivation
Authorization Enforcement (/users/{uid}/entries/*)
  ↓ Bounded Candidate Set Retrieval
Prompt Injection Filtering & XML Containment (<journal_entry_untrusted>)
  ↓
Gemini 2.5 AI Synthesis
  ↓ Candidate Claims & Evidence IDs
FastAPI Verification Engine (Zero-Evidence Rule)
  ↓
Clean, Grounded Response with Verified Evidence Citations
```

---

## 🔒 Security Posture & Guardrails

1. **Authentication & Identity Boundary**:
   - Cryptographic validation via Firebase Auth.
   - Client-provided UIDs in payloads are discarded; the authenticated UID is derived strictly from the verified JWT.

2. **Strict Multi-Tenant Isolation**:
   - Every Firestore query and document mutation is hardcoded to `/users/{uid}/entries/{entryId}`.
   - Cross-tenant access attempts (IDOR) return `404 Not Found`.

3. **Untrusted Cognitive Layer (Zero-Trust LLM)**:
   - The LLM is **never** trusted with authorization or data access decisions.
   - All entries passed into Gemini are wrapped in `<journal_entry_untrusted>` XML containment tags with tag breakout escaping (`[tag_escaped]`).

4. **Zero-Evidence Discard Rule**:
   - If Gemini returns a claim or decision referencing an entry ID outside the candidate set, or with no valid citations, the entire claim is discarded and `sufficientContext` is marked `false`.

5. **Prompt Injection & Cost Defense**:
   - Regex-based pre-flight scanner blocks instruction overrides, jailbreak phrases, and system prompt leakage attempts before reaching the LLM.
   - Sliding-window rate limiter protects against denial-of-wallet / cost amplification attacks.

---

## 🧠 Memory Intelligence Capabilities

1. **Decision Memory**:
   - Automatically extracts technical, personal, and career decisions.
   - Links each decision to its source entry and verified quote.
   - Classifies decisions as `active`, `completed`, `superseded`, or `revisited`.

2. **Contradiction Detection**:
   - Identifies evolving stances and shifting priorities over time with dual-entry verified citations.
   - Provides objective, neutral comparison between earlier and later statements.

3. **Personal Evolution**:
   - Synthesizes thematic trajectories across customizable timeframes.
   - Breaks down growth trajectories across earlier vs. current phases with verified quotes.

4. **Memory Integrity Engine**:
   - Real-time telemetry tracking claims analyzed, authorized evidence verified, and unauthorized citations rejected.

---

## 🚀 Running & Deployment

### Production Backend (Python 3.12 / FastAPI)
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Production Frontend (Vite / React SPA)
```bash
npm install
npm run build
```

---

## 🛡️ Hackathon Challenge Matrix

Challenge Pillar | Evidence
Authenticity | Decision Memory, Contradiction Detection, Personal Evolution
Usability | Responsive journal, AI interaction, Memory Intelligence
Stability | 49 automated tests, bounded context, error handling, Docker
Security | 22-point attack audit, IDOR defense, tenant isolation, evidence validation

## 🚀 Production Deployment

### Architecture

Browser
  ↓
Firebase Authentication
  ↓
Firebase ID Token
  ↓
Python FastAPI on Cloud Run
  ↓
Firestore / Gemini
  ↓
Evidence Verification
  ↓
Grounded Response

### Backend

The production API is Python 3.12 + FastAPI.

The application container is built from:

backend/Dockerfile

Cloud Run provides the PORT environment variable.

The backend listens on:

0.0.0.0:${PORT}

### Secrets

Gemini credentials are retrieved through Google Cloud Secret Manager.

The Gemini API key is never exposed to the browser and is never committed to Git.

### Authentication

Firebase Authentication provides the user identity token.

FastAPI verifies the Firebase ID token and derives the authenticated UID server-side.

Client-provided UIDs are never trusted.

### Firestore

User data is isolated under:

/users/{uid}/entries/{entryId}

Cross-user access is rejected.

### Verification

Before final deployment verify:

- authenticated journal creation
- authenticated journal retrieval
- cross-user access rejection
- prompt-injection defense
- evidence validation
- zero-evidence discard
- rate limiting
- Gemini failure handling
- /health endpoint

### Local Development

Backend:

cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000

Frontend:

npm install
npm run build
