# AI-Powered Medical Assistant — Medical RAG Engine (Module 1)

A production-ready **Medical Retrieval-Augmented Generation (RAG)** backend built with FastAPI. This module ingests medical documents, generates embeddings, stores them in a vector database, retrieves relevant context for user questions, and produces grounded, source-cited answers using the Gemini LLM.

This service is designed as **Module 1 — the foundation** of a larger AI-Powered Medical Assistant platform (future modules: Symptom Checker, Medical Report Analysis, Doctor Recommendation, Appointment System, Authentication, Medical History Tracking, Healthcare Dashboard).

---

## 1. Project Overview

The Medical RAG Engine answers medical questions **only from uploaded medical documents** — it does not rely on the LLM's own background knowledge. This minimizes hallucination risk, a critical requirement for any AI system operating in a medical context.

Pipeline at a glance:

```
Medical Document (PDF/TXT)
        ↓
Document Loader        (PyPDFLoader / TextLoader)
        ↓
Chunking                (RecursiveCharacterTextSplitter, 1000/200)
        ↓
Embedding Generation     (sentence-transformers · all-MiniLM-L6-v2)
        ↓
ChromaDB Storage         (persistent, cosine similarity)
        ↓
Similarity Search        (top-k retrieval)
        ↓
Context Retrieval        (relevance scoring + source tracking)
        ↓
Gemini LLM                (context-grounded, medically-constrained prompt)
        ↓
Medical Response          (answer + cited sources)
```

## 2. Features

- **Document ingestion** — Upload PDF or TXT medical documents via a REST endpoint.
- **Automatic chunking & embedding** — Documents are split into overlapping chunks and embedded locally (no embedding API costs).
- **Persistent vector storage** — ChromaDB stores vectors on disk; data survives restarts.
- **Context-grounded Q&A** — `/ask` retrieves only the most relevant chunks and forces the LLM to answer strictly from that context.
- **Medical safety guardrails** — System prompt forbids invented diagnoses and medication prescriptions, and explicitly instructs the model to recommend professional consultation.
- **Source citation** — Every answer reports which document(s) the information came from.
- **Singleton services** — Embedding model and vector store client are loaded once and reused (no repeated model loads).
- **Robust error handling** — Custom exception hierarchy + global handlers return a consistent `{"status": "error", "message": "..."}` shape for every failure.
- **Security** — File extension whitelisting, file size limits, filename sanitization (path-traversal safe), and environment-variable based secrets.
- **Future-ready PostgreSQL** — Document metadata is best-effort persisted to Postgres without ever blocking the core RAG flow if the database is unavailable, so future modules can build on it.
- **Advanced symptom checker** — `/symptom-checker` extracts symptoms from free text (with typo tolerance), ranks 132 diseases across 14 categories by Jaccard similarity, predicts severity, detects medical emergencies, explains its reasoning, and recommends a specialist.
- **Symptom-aware RAG** — `/ask` automatically runs the same symptom-detection pipeline on the question and injects detected symptoms, disease predictions, severity, and emergency status into Gemini's context before answering.
- **Medical AI audit logging** — Every symptom-extraction, matching, severity, and emergency decision is logged to a dedicated `logs/medical_ai.log`, separate from general application logs.
- **Medical report analyzer** — `/analyze-report` extracts lab values from PDF/TXT reports (CBC, Blood Sugar, Lipid Profile, Thyroid Profile, Kidney Function Test, Liver Function Test), compares them against reference ranges, flags abnormal values, assesses health risks, and generates a plain-English AI explanation.
- **Report-aware RAG** — Once a report is analyzed, its findings are automatically injected into subsequent `/ask` answers, even for follow-up questions that don't repeat any symptoms.
- **JWT authentication** — `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/me` with bcrypt password hashing, HS256 JWTs with `jti` claims, and role-based access control (Patient/Doctor/Admin).
- **Patient history** — `/history/symptoms`, `/history/reports`, `/history/chat`, `/history/full-profile` automatically populated on every authenticated call to `/symptom-checker`, `/analyze-report`, and `/ask`.
- **Patient-history-aware RAG** — Authenticated `/ask` calls load the patient's recent symptom/report/chat history and inject it into Gemini's context ("Past Symptoms / Past Reports / Previous Questions") before answering.
- **Patient dashboard** — `/dashboard/summary` returns total reports, total symptom checks, high-risk-report count, and last report date.
- **Dedicated audit logs** — Five separate log files: `app.log`, `medical_ai.log`, `report_analysis.log`, `auth.log`, `history.log`.
- **Full Swagger/OpenAPI docs** — Available at `/docs` and `/redoc`.
- **Automated tests** — 122 `pytest` tests covering all five modules, including real JWT roundtrips, bcrypt verification, RBAC enforcement, automatic history saving, and dashboard aggregation — all run against a real PostgreSQL database (no mocking of auth or history).

## 3. Architecture

```
medical-assistant-backend/
├── alembic/                              # Database migration scripts
│   ├── env.py                            # Reads DATABASE_URL from app Settings (single source of truth)
│   └── versions/                         # Generated migration files
├── alembic.ini                           # Alembic config (URL overridden by env.py)
├── app/
│   ├── api/
│   │   ├── deps.py                       # All dependency-injection providers
│   │   └── routes/
│   │       ├── health.py                 # GET /health
│   │       ├── upload.py                 # POST /upload
│   │       ├── rag.py                    # POST /ask (optional auth -> history saving)
│   │       ├── symptom_checker.py        # POST /symptom-checker (optional auth -> history saving)
│   │       ├── report_analysis.py        # POST /analyze-report (optional auth -> history saving)
│   │       ├── auth.py                   # POST /auth/register|login|refresh, GET /auth/me
│   │       ├── history.py                # GET /history/symptoms|reports|chat|full-profile
│   │       └── dashboard.py              # GET /dashboard/summary
│   ├── core/
│   │   ├── config.py                     # Pydantic Settings + JWT settings
│   │   ├── constants.py                  # Prompts, messages, thresholds, log filenames
│   │   ├── exceptions.py                 # 10 custom exception types + global handlers
│   │   ├── logging.py                    # 5 dedicated log files
│   │   └── security.py                   # File validation & sanitization
│   ├── data/
│   │   ├── diseases.json                 # 132 diseases across 14 categories
│   │   ├── symptom_weights.json          # Severity-scoring weights per symptom
│   │   └── reference_ranges.json         # 30 lab parameters across 6 report types
│   ├── database/
│   │   ├── connection.py                 # SQLAlchemy engine, session (expire_on_commit=False)
│   │   └── models/
│   │       ├── __init__.py               # Re-exports all models (backward compatible)
│   │       ├── document.py               # Document (Module 1 ingestion metadata)
│   │       ├── user.py                   # User, UserRole (Module 4)
│   │       └── history.py                # PatientHistory, MedicalReportHistory, ChatHistory (Module 5)
│   ├── rag/
│   │   ├── document_loader.py            # PDF/TXT loading
│   │   ├── chunking.py                   # RecursiveCharacterTextSplitter wrapper
│   │   ├── vector_store.py               # ChromaDB persistent client wrapper
│   │   └── pipeline.py                   # Ingestion orchestration
│   ├── schemas/
│   │   ├── query.py                      # /ask request model
│   │   ├── response.py                   # /health, /upload, /ask response models
│   │   ├── disease.py                    # DiseaseRecord, PossibleDisease
│   │   ├── symptom.py                    # Symptom-checker request/response models
│   │   ├── report_request.py             # Report-analysis request model
│   │   ├── report_response.py            # ReportParameter, RiskAssessment, ReportAnalysisResponse
│   │   ├── auth.py                       # RegisterRequest/Response, LoginRequest, TokenResponse, UserProfileResponse
│   │   └── history.py                    # SymptomHistoryEntry, ReportHistoryEntry, ChatHistoryEntry, FullProfileResponse, DashboardSummaryResponse
│   └── services/
│       ├── embedding_service.py          # Singleton SentenceTransformer wrapper
│       ├── retrieval_service.py          # Top-k retrieval + relevance scoring
│       ├── llm_service.py                # Gemini API wrapper
│       ├── rag_service.py                # Orchestrates patient history + symptom intel + report context + retrieval + LLM
│       ├── symptom_extraction_service.py # Free text -> normalized symptom list (exact + fuzzy matching)
│       ├── disease_matching_service.py   # Module 2: simple overlap-ratio matching (kept for tests/backward compat)
│       ├── confidence_service.py         # 0-100 scoring + level banding
│       ├── recommendation_service.py     # Specialist recommendation
│       ├── symptom_checker_service.py    # Orchestrates the full /symptom-checker pipeline
│       ├── advanced_matching_service.py  # Module 2.5: Jaccard similarity matching
│       ├── severity_prediction_service.py# Weighted rule-based severity scoring
│       ├── emergency_detection_service.py# Life-threatening symptom pattern detection
│       ├── explanation_service.py        # "Why" reasoning for the top prediction
│       ├── report_extraction_service.py  # Module 3: PDF/TXT extraction (PyPDFLoader + pdfplumber fallback)
│       ├── report_parser_service.py      # Regex-based lab-parameter detection
│       ├── medical_range_service.py      # Reference-range comparison + report-type inference
│       ├── report_risk_service.py        # Value-aware risk rules, duplicate-risk merging
│       ├── report_analysis_service.py    # Orchestrates /analyze-report + ReportContextStore
│       ├── password_service.py           # Module 4: bcrypt hash/verify
│       ├── jwt_service.py                # HS256 JWT access/refresh token generation + validation
│       ├── auth_service.py               # register/login/refresh/authenticate orchestration
│       ├── role_service.py               # get_current_user, get_optional_current_user, require_role, resolve_target_patient
│       ├── history_service.py            # Module 5: save/read all 3 history tables
│       ├── patient_service.py            # Full-profile aggregation
│       └── medical_record_service.py     # Dashboard summary analytics
├── chroma_db/                            # Persisted vector store (gitignored contents)
├── uploads/                              # Saved uploaded documents (gitignored contents)
├── logs/                                 # 5 log files, all gitignored
├── tests/
│   ├── fixtures/                         # Static lab-report PDFs and TXTs for Module 3/5 tests
│   ├── conftest.py                       # FakeRAGService, db_session fixture, register_and_login helper
│   ├── test_health.py / test_upload.py / test_ask.py         # Module 1
│   ├── test_symptom_extraction.py / test_advanced_matching.py # Module 2/2.5
│   ├── test_severity_prediction.py / test_emergency_detection.py / test_symptom_checker.py / test_rag_symptom_integration.py
│   ├── test_report_parsing.py / test_medical_range.py / test_report_risk.py  # Module 3
│   ├── test_report_extraction.py / test_report_analysis_endpoint.py / test_report_rag_integration.py
│   ├── test_auth.py / test_jwt_service.py / test_role_access.py  # Module 4
│   └── test_history.py / test_dashboard.py                        # Module 5
├── .env.example
├── requirements.txt
├── main.py
└── README.md
```

**Design principles applied:** each service has a single responsibility (SRP), services are injected via FastAPI's dependency system rather than hard-imported into routes (DIP/DI), the vector store/LLM/matching/risk-rule logic are all abstracted behind service classes so any could be swapped later (OCP — e.g. `AdvancedMatchingService`'s Jaccard scoring could be replaced by a trained ML model, or `ReportRiskService`'s rules extended, without touching the rest of the pipeline), and every public function is fully type-hinted.

## 4. Installation

**Prerequisites:** Python 3.12+, a Gemini API key ([aistudio.google.com](https://aistudio.google.com/apikey)).

```bash
# 1. Clone / unzip the project, then enter it
cd medical-assistant-backend

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

> **Note:** `sentence-transformers` will download the `all-MiniLM-L6-v2` model (~90 MB) from Hugging Face on first use. Make sure the machine running this has normal internet access (no special config needed — this only matters if you run it inside a network-restricted sandbox).

## 5. Setup

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```
GEMINI_API_KEY=your_real_key_here
```

## 6. Environment Variables

| Variable | Description | Default |
|---|---|---|
| `APP_ENV` | Environment name (`development`/`production`) | `development` |
| `GEMINI_API_KEY` | **Required.** Your Gemini API key | — |
| `GEMINI_MODEL_NAME` | Gemini model used for answer generation | `gemini-2.5-flash` |
| `EMBEDDING_MODEL_NAME` | Sentence-transformers model | `all-MiniLM-L6-v2` |
| `CHROMA_DB_PATH` | Folder where ChromaDB persists vectors | `./chroma_db` |
| `UPLOAD_DIR` | Folder where uploaded files are saved | `./uploads` |
| `LOG_DIR` | Folder for `app.log` | `./logs` |
| `CHUNK_SIZE` | Characters per chunk | `1000` |
| `CHUNK_OVERLAP` | Overlap between chunks | `200` |
| `RETRIEVAL_TOP_K` | Default number of chunks retrieved per query | `5` |
| `MAX_FILE_SIZE_MB` | Max upload size | `10` |
| `ALLOWED_EXTENSIONS` | Comma-separated allowed file extensions | `.pdf,.txt` |
| `DATABASE_URL` | PostgreSQL connection string (future modules) | `postgresql://postgres:postgres@localhost:5432/medical_assistant` |
| `CORS_ORIGINS` | Comma-separated allowed origins, or `*` | `*` |

## 7. Running the Application

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## 8. API Endpoints

### `GET /health`
Health check.

```json
{
  "status": "running",
  "service": "medical-rag"
}
```

### `POST /upload`
Upload a medical document (`multipart/form-data`, field name `file`). Accepts `.pdf` and `.txt`.

**Response (201):**
```json
{
  "status": "success",
  "document": "diabetes.pdf",
  "chunks_stored": 120
}
```

### `POST /ask`
Ask a medical question against the ingested knowledge base. If the question contains
recognizable symptoms, the Module 2.5 intelligence pipeline (extraction, emergency detection,
Jaccard disease matching, severity prediction) runs automatically and its findings are
injected into Gemini's context before the answer is generated.

**Request:**
```json
{
  "question": "What are the symptoms of diabetes?"
}
```

**Response:**
```json
{
  "answer": "Common symptoms include increased thirst, frequent urination, fatigue...",
  "sources": ["diabetes.pdf"],
  "detected_symptoms": [],
  "possible_diseases": []
}
```

`detected_symptoms` and `possible_diseases` are populated only when the question itself
describes symptoms (e.g. "I have fever and chest pain, what could this be?").

Optional request fields: `top_k` (1–20, default 5) and `source_filter` (restrict retrieval to a specific filename).

### `POST /symptom-checker`
Analyze free-text symptoms: extracts known symptoms, detects medical emergencies, ranks
candidate diseases by Jaccard similarity, predicts an overall severity level, explains the
leading prediction, and recommends a specialist.

**Request:**
```json
{
  "text": "I have fever cough headache body pain"
}
```

**Response:**
```json
{
  "symptoms": ["fever", "cough", "headache", "body pain"],
  "possible_diseases": [
    {
      "disease": "Flu",
      "score": 0.8,
      "confidence": 80,
      "level": "High",
      "category": "Infectious Diseases",
      "specialist": "General Physician",
      "severity": "medium",
      "matched_symptoms": ["body pain", "cough", "fever", "headache"]
    }
  ],
  "severity": "Moderate",
  "emergency": false,
  "recommended_specialist": "General Physician",
  "reasoning": ["Matched symptom: fever", "Matched symptom: cough", "..."],
  "disclaimer": "This is an AI-generated health assessment and not a medical diagnosis. Consult a qualified healthcare professional for medical advice."
}
```

If a potentially life-threatening symptom is detected (e.g. chest pain, difficulty breathing,
facial drooping), `emergency` is `true`, `severity` is forced to `"Emergency"` regardless of the
weighted symptom score, and the response should be treated as urgent.

### `POST /analyze-report`
Upload a lab report (PDF or TXT) and receive parameter extraction, normal-range comparison,
abnormal value detection, risk assessment, and a plain-English AI explanation. Supports CBC,
Blood Sugar, Lipid Profile, Thyroid Profile, Kidney Function Test, and Liver Function Test
reports. Image-based reports are not yet supported (future-ready).

**Request:** `multipart/form-data` with a `file` field (PDF or TXT).

**Response:**
```json
{
  "report_type": "Blood Sugar Report",
  "parameters": [
    {
      "name": "glucose",
      "value": 145,
      "unit": "mg/dL",
      "status": "HIGH",
      "reference_min": 70,
      "reference_max": 99
    }
  ],
  "abnormal_parameters": ["glucose"],
  "risk_assessment": [
    {"risk": "Prediabetes Risk", "severity": "Moderate", "based_on": ["glucose"]}
  ],
  "ai_summary": "Your glucose level is higher than the typical fasting range...",
  "disclaimer": "This analysis is informational only and not a medical diagnosis."
}
```

Once a report has been analyzed, its findings (detected risks, abnormal parameters, and a
summary) are automatically injected into the context for subsequent `/ask` calls — see Module 3
below.

### Error responses
All errors share a consistent shape:
```json
{
  "status": "error",
  "message": "Invalid file format"
}
```

## 9. Module 2.5 — Advanced Medical Intelligence Engine

Module 2.5 upgrades the symptom checker from a basic overlap-ratio matcher into a full
medical-intelligence pipeline, tightly integrated with the RAG flow:

```
Question / Free Text
        ↓
Symptom Extraction        (SymptomExtractionService — exact + typo-tolerant matching)
        ↓
Emergency Detection        (EmergencyDetectionService — runs BEFORE disease matching)
        ↓
Disease Matching            (AdvancedMatchingService — Jaccard similarity)
        ↓
Severity Prediction          (SeverityPredictionService — weighted rule-based scoring)
        ↓
Explanation                   (ExplanationService — "why" reasoning for the top match)
        ↓
Specialist Recommendation      (RecommendationService)
        ↓
[/ask only] Retriever → Gemini → Final Medical Response
```

**Knowledge base** (`app/data/diseases.json`): 132 diseases across 14 categories
(Cardiology, Neurology, Respiratory, Gastroenterology, Dermatology, Endocrinology,
Orthopedics, Psychiatry, Nephrology, Hepatology, Infectious Diseases, Hematology, ENT,
Ophthalmology). Each record includes `disease`, `category`, `symptoms`, `risk_factors`,
`specialist`, `severity`, `description`, and `emergency_flags`.

**Jaccard similarity** (`app/services/advanced_matching_service.py`):
`score = |intersection(user_symptoms, disease_symptoms)| / |union(user_symptoms, disease_symptoms)|`.
This supersedes the simpler `matched / total_disease_symptoms` ratio used in Module 2
(`disease_matching_service.py`, kept in the codebase and still covered by its own tests for
backward compatibility, but no longer used by the live `/symptom-checker` or `/ask` pipelines).

**Severity prediction** (`app/services/severity_prediction_service.py` +
`app/data/symptom_weights.json`): each detected symptom contributes a configurable weight;
the summed score maps to Mild (0–5), Moderate (6–10), Severe (11–15), or Emergency (16+).

**Emergency detection** (`app/services/emergency_detection_service.py`): checks extracted
symptoms against a curated set of life-threatening patterns (chest pain, severe bleeding,
stroke symptoms, loss of consciousness, difficulty breathing, seizures, severe allergic
reaction, sudden vision loss, heart-attack symptoms, and more) — runs immediately after
extraction and **before** disease matching, independent of which disease (if any) ends up
matching.

**Medical AI audit log** (`logs/medical_ai.log`): every symptom-extraction, emergency,
severity, matching, and RAG context-injection decision is logged here, separately from the
general `logs/app.log`, for auditability.

## 10. Module 3 — Medical Report Analyzer

Module 3 adds the ability to upload a lab report and receive structured, explainable analysis,
tightly integrated with the RAG flow:

```
Report (PDF/TXT)
        ↓
Extraction          (ReportExtractionService — PyPDFLoader, pdfplumber fallback)
        ↓
Parameter Detection   (ReportParserService — configurable regex, alias-aware)
        ↓
Range Comparison        (MedicalRangeService — LOW / NORMAL / HIGH)
        ↓
Risk Assessment            (ReportRiskService — value-aware rule engine, merges
                            duplicate risks triggered by multiple parameters)
        ↓
AI Explanation                (existing LLMService/Gemini — no changes needed)
        ↓
Report Summary
        ↓
[Step 8] RAG Context Injection → subsequent /ask calls
```

**Supported reports:** CBC, Blood Sugar, Lipid Profile, Thyroid Profile, Kidney Function Test,
Liver Function Test — 30 parameters total, defined in `app/data/reference_ranges.json` with
`min`, `max`, `unit`, and `report_type` per parameter.

**PDF extraction fallback:** `ReportExtractionService` tries `PyPDFLoader` first (consistent
with Module 1's document loader); if it fails or returns no text, it falls back to `pdfplumber`,
which handles some malformed/table-heavy layouts PyPDFLoader cannot. Image-based reports
(scanned/OCR) are explicitly out of scope for now and return a clear "not yet supported" error.

**Risk rules** (`app/services/report_risk_service.py`) inspect the *raw value*, not just the
LOW/NORMAL/HIGH band, since clinically meaningful thresholds don't always line up with the
normal range — e.g. glucose's normal range tops out at 99, but the Prediabetes/Diabetes split
used for risk assessment sits at 100–125 / 126+. Risks triggered by more than one parameter
(e.g. both glucose and HbA1c indicating diabetes risk) are merged into a single entry rather
than reported twice.

**RAG integration (Step 8):** `ReportContextStore` (in `report_analysis_service.py`) is a
small, thread-safe, in-memory singleton holding the most recently analyzed report's findings.
`RAGService` reads from it on every `/ask` call and, if present, injects a "Medical Report
Analysis" context block ahead of retrieved document chunks — independent of whether the
question itself mentions symptoms, so "What does my report mean?" works correctly. This
mirrors the simplicity of the rest of the current architecture (no per-user session/auth layer
exists yet, so there is one shared "latest report" slot, not one per user).

**Report-analysis audit log** (`logs/report_analysis.log`): every upload, parsed parameter set,
detected risk, and error is logged here, separate from `app.log` and `medical_ai.log`.

## 11. Testing

```bash
pytest -v
```

79 tests covering: document upload/health (Module 1); the symptom-aware `/ask` flow with an
in-memory RAG fake (Module 1+2.5); symptom extraction, Jaccard disease matching, severity
prediction, emergency detection, and the `/symptom-checker` endpoint (Module 2.5); and report
extraction (PDF + TXT, with a real pdfplumber-fallback check), parameter parsing across all 6
report types, range comparison, risk detection (including the duplicate-risk merge), the
`/analyze-report` endpoint, and the Step 8 RAG context-injection integration (Module 3). The
## 11. Testing

```bash
pytest -v
```

**122 tests** across all five modules:

- **Modules 1-3 (79 tests):** document upload/health, symptom-aware `/ask`, symptom extraction, Jaccard matching, severity prediction, emergency detection, `/symptom-checker`, report extraction (PDF + TXT), parameter parsing for all 6 report types, range comparison, risk detection, `/analyze-report`, and RAG context-injection. Fully offline — no Gemini API key, internet access, or embedding-model download required.
- **Module 4 (24 tests):** register/login/refresh/me endpoints (including email validation, password strength, duplicate-email 409, wrong-password 401, malformed-token 401, access-token-used-as-refresh-token 401), JWT roundtrip, bcrypt hashing/verification, salt uniqueness, RBAC (patient can't view another patient's history, doctor/admin can, unauthenticated 401, non-existent patient 404).
- **Module 5 (19 tests):** automatic history saving from authenticated calls to all three endpoints (including verifying anonymous calls save nothing), per-patient isolation, full-profile combining all history types, dashboard summary (zero-activity baseline, symptom-check count, high-risk vs non-high-risk report counting).

Module 4/5 tests run against the **real PostgreSQL database** with full table cleanup between tests — no auth or history mocking. Run the database before running tests:

```bash
# Start Postgres (once per session):
service postgresql start   # or: pg_ctlcluster 16 main start

# Create the database (first time only):
createdb medical_assistant

# Apply migrations (first time only):
alembic upgrade head

# Then run the full suite:
pytest -v
```

## 12. Future Scope

The platform is now across five modules: RAG engine, Advanced Medical Intelligence, Report Analyzer, Auth/RBAC, and Patient History. Natural next extensions:

- **Per-user report context** — `ReportContextStore` currently holds one shared "latest report" slot (matching the single-user simplicity of the current architecture); now that `User` exists, this becomes a trivial `Dict[int, str]` keyed by `user.id` without touching `RAGService`'s call site at all.
- **Doctor-patient assignments** — `resolve_target_patient` in `role_service.py` currently allows any DOCTOR to view any patient; a `doctor_patient_assignments` table is the natural follow-up to scope this properly.
- **Token revocation/blacklisting** — Every JWT already carries a unique `jti` claim, which is exactly the standard anchor point for a Redis-backed revocation store; no token changes needed.
- **ML-based disease prediction** — `AdvancedMatchingService` is structured so its Jaccard scoring can be swapped for a trained classifier without touching extraction, severity, explanation, or any route.
- **Image-based report support (OCR)** — `ReportExtractionService` already rejects image files with a clear "not yet supported" message; adding Tesseract/OCR is a contained extension to that one method.
- **Appointment scheduling** — `database/models/` is ready for new tables (appointments, doctor_patient) without touching any existing service.

## 13. Notes on Technology Choices

## 13. Notes on Technology Choices

- **Gemini SDK:** This project uses the current unified `google-genai` SDK (`from google import genai`), which is Google's supported SDK going forward; the older `google-generativeai` package is deprecated. The default model is `gemini-2.5-flash` (configurable via `GEMINI_MODEL_NAME`).
- **LangChain's role:** LangChain is used for document loading (`PyPDFLoader`, `TextLoader`) and chunking (`RecursiveCharacterTextSplitter`). Embedding generation and vector storage are implemented directly against `sentence-transformers` and `chromadb` so `EmbeddingService` and `VectorStoreService` remain explicit, independently testable, swappable components.
- **PostgreSQL:** Required for Module 4 (auth) and Module 5 (patient history). The RAG, symptom-checker, and report-analyzer features remain operational if Postgres is unreachable — history saving on those endpoints is best-effort (non-blocking); only auth/history endpoints that explicitly call `get_db()` will 503 until the database is available.
- **Alembic:** Schema migrations live in `alembic/` and `alembic.ini`. `DATABASE_URL` is read from the app's own `Settings` class, so there is exactly one source of truth for the connection string (no duplication in `alembic.ini`). In production, run `alembic upgrade head` rather than relying on startup `create_all`.
- **bcrypt / python-jose:** `bcrypt` (via the `bcrypt` package, not `passlib`) for password hashing. `python-jose[cryptography]` for JWT generation/validation. Every JWT carries a `jti` (UUID) claim — this guarantees distinct tokens even when issued within the same second and provides the standard anchor point for future revocation support.
- **SQLAlchemy `expire_on_commit=False`:** Set explicitly on `SessionLocal` so ORM objects (specifically the authenticated `User` resolved by `get_optional_current_user`) remain readable after their originating session closes. This is required by the app's pattern of resolving a user in one short-lived session and then passing it to several independent best-effort DB operations (history saving, RAG context loading) that each open their own session. Without this, every one of those call sites raises `DetachedInstanceError`.

---

Built as the foundation module of a Final Year Major Project: **AI-Powered Medical Assistant**.
