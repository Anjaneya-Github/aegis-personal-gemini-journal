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

| Challenge Pillar | Score Goal | Enforcement Implementation |
|---|---|---|
| **Authenticity** | **9.5/10** | Genuine personal reflection companion, authentic decision tracking, and thematic evolution synthesis |
| **Usability** | **9.5/10** | Responsive dark aesthetic, Newsreader serif typography, seamless real-time search, and instant SOC telemetry |
| **Stability** | **9.5/10** | Comprehensive error handling, graceful fallbacks, and resilient Firestore subscriptions |
| **Security** | **9.5/10** | 22-point security self-audit, zero-trust LLM boundary, IDOR defense, and multi-tenant Firestore scoping |

## Production Deployment

Aegis uses Python FastAPI as the only production API.

1. Build the backend container from backend/Dockerfile.
2. Push the image to Artifact Registry.
3. Deploy the container to Cloud Run.
4. Attach the production service account.
5. Grant the service account Secret Manager access to gemini-api-key.
6. Configure Firebase Authentication.
7. Configure Firestore.
8. Configure the frontend with the Cloud Run API endpoint.
9. Verify /health.
10. Verify authenticated journal creation.
11. Verify cross-user access is rejected.
12. Verify prompt-injection defense.
13. Verify evidence validation.

Production flow:

Browser
→ Firebase Auth
→ Firebase ID Token
→ Python FastAPI
→ Firestore/Gemini
→ Evidence Verification
→ Response

Secrets never reach the browser.
