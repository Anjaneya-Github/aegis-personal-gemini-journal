# Aegis Journal — Zero-Trust Personal AI Journal & Memory Intelligence

> **Production Hackathon Edition**  
> *Private, authenticated personal journal with AI-guided reflections, multi-tenant Firestore containment, and zero-trust memory intelligence.*

---

## 🏛️ Production Architecture

```
Browser (React / JavaScript SPA)
  ↓ Firebase Authentication (Google OAuth & JWT ID Tokens)
Firebase ID Token (Header: Authorization: Bearer <token>)
  ↓
Python FastAPI on Cloud Run (Production Container)
  ↓ Token Verification & UID-Derived Authorization (/users/{uid}/entries/*)
Firestore / Gemini (Bounded Candidate Set & Escaped XML Containment)
  ↓ Candidate Claims & Citations
Evidence Verification Engine (Zero-Evidence Rule)
  ↓
Grounded Response (Strictly Verified Quotes & Citations)
```

---

## 🔒 Security Posture & Guardrails

1. **Authentication & Identity Boundary**:
   - Cryptographic validation via Firebase Authentication.
   - Client-provided UIDs in request bodies or query parameters are discarded; the authenticated UID is derived strictly from the cryptographically verified JWT.

2. **Strict Multi-Tenant Isolation & IDOR Defense**:
   - Every Firestore query and document mutation is restricted to `/users/{uid}/entries/{entryId}`.
   - Cross-tenant access attempts return `404 Not Found`.

3. **Untrusted Cognitive Layer (Zero-Trust LLM)**:
   - **The LLM is never trusted with authorization or data access decisions.**
   - All entries passed to Gemini are enclosed in `<journal_entry_untrusted>` XML containment tags with tag breakout escaping (`[tag_escaped]`).

4. **Zero-Evidence Discard Rule**:
   - If Gemini returns a claim, decision, or contradiction referencing an entry ID outside the authorized candidate set, or with ungrounded citations, the claim is discarded and `sufficientContext` is marked `false`.

5. **Prompt Injection & Cost Defense**:
   - Pre-flight security filters block instruction overrides, jailbreak phrases, and system prompt leakage attempts before reaching the LLM.
   - Sliding-window rate limiter prevents cost amplification and denial-of-wallet vectors.

6. **Secret Manager & Credential Isolation**:
   - Gemini API credentials are stored securely in Google Cloud Secret Manager.
   - API keys are never exposed to the client browser and never committed to Git.

7. **Least Privilege IAM**:
   - Cloud Run runs under a dedicated service account granted only minimal required roles: Firestore User access and Secret Manager Secret Accessor.

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
   - Real-time SOC telemetry tracking claims analyzed, authorized evidence verified, and unauthorized citations rejected.

---

## 🛡️ Challenge Matrix

| Challenge Pillar | Evidence |
|---|---|
| **Authenticity** | Decision Memory, Contradiction Detection, Personal Evolution, Memory Integrity |
| **Usability** | Journal workflow, Gemini interaction, responsive React/JavaScript UI, Memory Intelligence and Security SOC |
| **Stability** | 49 automated tests, bounded AI context, rate limiting, graceful Gemini fallback, Docker and Cloud Run architecture |
| **Security** | Firebase authentication, UID-derived authorization, Firestore tenant isolation, IDOR defense, prompt injection containment, evidence verification, zero-evidence discard, Secret Manager, 22-point attack simulation |

---

## 🚀 Production Deployment (Google Cloud Run)

### Environment Specifications
- **Production Frontend**: Vite-built React / JavaScript static assets.
- **Production Backend**: Python 3.12 FastAPI (`backend/app/main.py`).
- **Production Container**: `backend/Dockerfile`.
- **Production Runtime**: Google Cloud Run (container listens on `0.0.0.0:${PORT}`).

### Deployment Steps

1. **Configure Google Cloud Project**:
   ```bash
   gcloud config set project [PROJECT_ID]
   ```

2. **Enable Required Google Cloud APIs**:
   ```bash
   gcloud services enable run.googleapis.com \
     artifactregistry.googleapis.com \
     secretmanager.googleapis.com \
     firestore.googleapis.com
   ```

3. **Store Gemini API Key in Secret Manager**:
   ```bash
   echo -n "[YOUR_GEMINI_API_KEY]" | gcloud secrets create GEMINI_API_KEY \
     --data-file=- \
     --replication-policy="automatic"
   ```

4. **Configure Dedicated Cloud Run Service Account**:
   ```bash
   gcloud iam service-accounts create aegis-backend-sa \
     --display-name="Aegis Journal Backend Service Account"

   # Grant Firestore access
   gcloud projects add-iam-policy-binding [PROJECT_ID] \
     --member="serviceAccount:aegis-backend-sa@[PROJECT_ID].iam.gserviceaccount.com" \
     --role="roles/datastore.user"

   # Grant Secret Manager access
   gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
     --member="serviceAccount:aegis-backend-sa@[PROJECT_ID].iam.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   ```

5. **Build and Deploy Backend Container to Cloud Run**:
   ```bash
   # Build image via Cloud Build or Artifact Registry
   gcloud builds submit --tag gcr.io/[PROJECT_ID]/aegis-backend ./backend

   # Deploy to Cloud Run
   gcloud run deploy aegis-backend \
     --image gcr.io/[PROJECT_ID]/aegis-backend \
     --platform managed \
     --region [REGION] \
     --service-account aegis-backend-sa@[PROJECT_ID].iam.gserviceaccount.com \
     --set-env-vars GOOGLE_CLOUD_PROJECT=[PROJECT_ID],FIREBASE_PROJECT_ID=[PROJECT_ID] \
     --allow-unauthenticated
   ```

6. **Configure Firebase Authentication & Firestore**:
   - Provision Firestore in Native Mode in the Firebase Console.
   - Deploy `firestore.rules` for client-side security.
   - Enable Google Sign-In / Email Auth in Firebase Authentication.

7. **Verify Deployment**:
   - Health Check: `GET https://[CLOUD_RUN_SERVICE_URL]/health`
   - Authenticated Endpoint: `GET https://[CLOUD_RUN_SERVICE_URL]/api/journal/entries` with `Authorization: Bearer [FIREBASE_ID_TOKEN]`

---

## 💻 Local Development Setup

For local testing and offline development:

### 1. Backend (Python 3.12 / FastAPI)
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend (Vite / React)
```bash
npm install
npm run dev
```

---

## ✅ Verification & Test Suite

The application has been verified across all core modules:

- **Backend tests**: 24/24
- **Security tests**: 7/7
- **Memory tests**: 6/6
- **Attack simulation tests**: 12/12
- **Total tests**: 49/49
- **Frontend build**: PASS
- **Backend import**: PASS
- **Docker**: PASS
