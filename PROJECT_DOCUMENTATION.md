# Healthcare RAG System — Project Documentation

Last updated: 2026-08-15

This document summarizes the Healthcare RAG (Retrieval-Augmented Generation) prototype: purpose, architecture, database design, API flows, and developer/run instructions. Use this as a single reference for onboarding and local development.

---

## 1. Project overview

The Healthcare Knowledge RAG project is a clinician-/patient-facing local prototype that performs secure, patient-aware retrieval of medical documents and uses LLMs to produce grounded answers. Key goals:

- Ingest documents (PDFs, images with OCR), chunk and embed them, and index into a vector store (default local: Postgres + pgvector).
- Enforce strict patient-doctor access: only approved doctors can retrieve a patient's documents and ask the system questions grounded in those documents.
- Provide a React frontend for clinicians and patients to register/login, upload documents, request/approve access, and chat with the RAG system.
- Be runnable locally with environment-driven configuration and a background ingestion worker that simulates production-like behavior.

Major components:
- Backend: FastAPI + Async SQLAlchemy, services for ingestion, retrieval, patient access, and auth.
- Vector backend abstraction: memory, Qdrant, or pgvector (pgvector is the default for local development).
- Frontend: Vite + React + Axios, with pages for auth, dashboards, documents, access, chat, and admin.

Important files (entry points):
- Backend app entry: [backend/app/main.py](/healthcare-rag-system/backend/app/main.py)
- Backend configuration: [backend/app/core/config.py](/healthcare-rag-system/backend/app/core/config.py)
- Vector store service: [backend/app/services/vector_store_service.py](/healthcare-rag-system/backend/app/services/vector_store_service.py)
- Ingestion service: [backend/app/services/document_ingestion_service.py](/healthcare-rag-system/backend/app/services/document_ingestion_service.py)
- Medical document orchestration: [backend/app/services/medical_document_service.py](/healthcare-rag-system/backend/app/services/medical_document_service.py)
- Retrieval service: [backend/app/services/retrieval_service.py](/healthcare-rag-system/backend/app/services/retrieval_service.py)
- Frontend entry & auth: [frontend/src/App.jsx](/healthcare-rag-system/frontend/src/App.jsx), [frontend/src/context/AuthContext.jsx](/healthcare-rag-system/frontend/src/context/AuthContext.jsx)

---

## 2. Database design & relationships

The app uses a relational database (Postgres by default). Models are defined with SQLAlchemy in `backend/app/models/`.

High-level entity summary:

- User
  - Stores authentication data, role (PATIENT, DOCTOR, ADMIN), email, names, and basic metadata.
  - One-to-one/one-to-many relationships to Patient/Doctor profiles.

- Patient
  - Profile and link to user. Holds patient-specific identifiers and metadata.
  - Has many MedicalDocument and many PatientAccess records.

- Doctor
  - Profile and link to user. Holds license and registration numbers, specialization, and contact details.
  - Has many PatientAccess, Encounters.

- MedicalDocument
  - Represents an uploaded file (PDF / image). Contains metadata: original filename, storage location (S3 key or local path), content hash, processing status, and references to embedded chunks once processed.
  - Each document belongs to a patient (patient_id foreign key).

- DocumentChunk (embedded text chunk)
  - Stores chunk text metadata and embedding vector reference (stored in vector backend). Each chunk references the source MedicalDocument.

- PatientAccess
  - Represents access requests and approvals between a patient and a doctor. Has status (PENDING/APPROVED/REJECTED), created/updated timestamps.

- Encounter, Diagnosis, Medication, Lab
  - Structured patient facts used to enrich retrieval context. These support the LLM prompt with known structured facts about the patient.

- Audit/Processing tables
  - Ingestion queue entries, processing state, error logs to track document ingestion.

Relationships (simplified):

- User 1<->1 Patient (a user may be a patient)
- User 1<->1 Doctor (a user may be a doctor)
- Patient 1<->N MedicalDocument
- MedicalDocument 1<->N DocumentChunk
- Doctor 1<->N PatientAccess (requests to patients)
- Patient 1<->N PatientAccess (incoming requests)
- Doctor 1<->N Encounter
- Patient 1<->N Encounter

ER Diagram (ASCII):

User (id)
 |--< Patient (id, user_id)
 |       |--< MedicalDocument (id, patient_id)
 |               |--< DocumentChunk (id, document_id)
 |
 |--< Doctor (id, user_id)
         |--< PatientAccess (id, doctor_id, patient_id)
         |--< Encounter (id, patient_id, doctor_id)

Notes about constraints and uniqueness:
- Some doctor fields are unique (license_number, registration_number). The repository logic avoids inserting duplicate empty strings by saving NULL for empty registration numbers and temporary unique placeholders for license_number during initial creation.
- Document content deduplication is performed by hashing file content and checking existing hashes before enqueuing ingestion.

Schema files and model definitions:
- [backend/app/models/user.py](/healthcare-rag-system/backend/app/models/user.py)
- [backend/app/models/doctor.py](/healthcare-rag-system/backend/app/models/doctor.py)
- [backend/app/models/patient.py](/healthcare-rag-system/backend/app/models/patient.py)
- [backend/app/models/medical_document.py](/healthcare-rag-system/backend/app/models/medical_document.py)
- [backend/app/models/document_chunk.py](/healthcare-rag-system/backend/app/models/document_chunk.py)

---

## 3. Project architecture

High-level architecture components:

1. Frontend (React)
   - Vite-powered single page app at `frontend/`.
   - Pages: Login, Register, Dashboard (role-aware), Chat, Documents (upload + confirm), Access (request/approve), Admin.
   - Uses Axios [frontend/src/services/api.js](/healthcare-rag-system/frontend/src/services/api.js) to communicate with the backend.
   - Auth flow: stores access token in localStorage and includes it in Authorization header.

2. Backend API (FastAPI)
   - Main entry: [backend/app/main.py](/healthcare-rag-system/backend/app/main.py)
   - Routers for auth, patients, doctors, medical_documents, patient_access, chat, etc., under `/api/v1`.
   - Middlewares: request id, logging, timing, CORS (configurable via env).
   - Exception handlers: convert internal errors and validation errors into a consistent ErrorResponse shape.

3. Database (Postgres + pgvector)
   - SQLAlchemy models and async session (backend/app/db).
   - pgvector extension is used for storing/retrieving embeddings when `VECTOR_DB_BACKEND=pgvector`.

4. Vector backend abstraction
   - Implementations: memory (for tests), Qdrant (remote vector DB), pgvector (Postgres local vector store).
   - Managed by [backend/app/services/vector_store_service.py](/healthcare-rag-system/backend/app/services/vector_store_service.py).

5. Ingestion worker
   - Background worker started with the FastAPI lifespan (can be toggled via env settings). It polls unprocessed documents and runs parsing (PDF/OCR), chunking, embedding, and indexing.
   - Document orchestration handled in [backend/app/services/document_ingestion_service.py](/healthcare-rag-system/backend/app/services/document_ingestion_service.py) and [backend/app/services/medical_document_service.py](/healthcare-rag-system/backend/app/services/medical_document_service.py).

6. LLM provider
   - Config-driven LLM/embedding provider (OpenAI by default). Embeddings and LLM completions are used during indexing and chat generation. Requires `OPENAI_API_KEY` (or alternate provider settings).

7. Object storage (S3)
   - Document uploads are handled through presigned URLs. S3 credentials and bucket are configured via env variables. For local testing, developers can use MinIO or local mocks.

Component interaction overview
- Frontend requests presigned upload URL from backend → client uploads file directly to S3 → client calls confirm-upload → backend enqueues/marks document for ingestion → ingestion worker processes document, creates chunks, computes embeddings, indexes into vector backend.
- Retrieval: user (doctor with approved access) asks question → backend validates access, performs hybrid retrieval (vector + optional metadata), enriches context with structured facts (encounters, meds, labs) → constructs prompt and calls LLM → returns grounded answer.

---

## 4. API flow (important endpoints & sequences)

Base path: `/api/v1`

Authentication
- POST /auth/register
  - Request: { first_name, last_name, email, password, role }
  - Response: ApiResponse/ErrorResponse; on success returns access_token or user data.
  - Notes: server validates password complexity and name lengths. Validation errors are returned in ErrorResponse.error.details.

- POST /auth/login
  - Request: { email, password }
  - Response: { access_token, token_type: "bearer" }

- GET /auth/me
  - Authenticated endpoint to fetch the current user profile.

Document upload (client flow)
1. POST /medical_documents/upload-url (or similar - see file)
   - Client requests a presigned PUT URL for S3 (includes metadata: patient_id, file_name, size, content_type)
   - Backend returns presigned URL and an upload id.

2. Client performs PUT to S3 using the presigned URL (direct upload).

3. POST /medical_documents/confirm
   - Client notifies backend that upload finished (upload id / S3 key)
   - Backend validates, stores metadata in MedicalDocument row, computes file hash, and enqueues for ingestion if not duplicate.

Ingestion worker flow
- Background worker picks up pending medical documents (status=PENDING)
- For each document:
  - Download (or read) from S3/local storage
  - If PDF: parse text pages; if image: run OCR (Tesseract configurable)
  - Chunk text using configured chunk size and overlap
  - Compute embeddings for each chunk via embedding provider
  - Store chunk metadata in DocumentChunk and index vectors into vector backend (pgvector or Qdrant)
  - Mark document as PROCESSED or FAILED with logs

Retrieval & Chat
- POST /chat/ask (or /chat)
  - Request: { patient_id, question, options }
  - Backend steps:
    1. Validate requester has approved access to patient_id (via PatientAccess service)
    2. Query vector backend for top-k relevant chunks for the question (hybrid scoring may include metadata filters: patient_id)
    3. Enrich with structured patient facts (recent encounters, meds, labs) via [backend/app/services/retrieval_service.py](/healthcare-rag-system/backend/app/services/retrieval_service.py)
    4. Construct a compact prompt with retrieved chunks + facts + question
    5. Call LLM (completion) to generate the final answer; include citations/refs to chunk ids when possible
    6. Return the response to client and optionally log conversation in Chat model

Patient access flow
- POST /patient_access/request
  - Doctor requests access to a patient; creates PatientAccess status=PENDING
- POST /patient_access/{id}/approve or /reject
  - Patient or admin approves or rejects the request; status updated accordingly
- Retrieval checks consult PatientAccess to ensure only approved doctors can retrieve patient data.

Admin & monitoring
- Admin endpoints exist to list ingestion jobs, re-enqueue failed documents, and view system metrics.

---

## Running & common troubleshooting

1. Environment
- Copy `.env.example` to `.env` in `backend/` and set required values:
  - JWT_SECRET_KEY (required)
  - DATABASE_URL (postgres with pgvector if using pgvector)
  - AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / S3_BUCKET_NAME (for upload)
  - OPENAI_API_KEY (for LLMs)
  - Optional: CORS_ALLOW_ALL=true for local debugging (see `.env.example`).

2. Start Postgres (docker-compose is provided at repo root):
   docker-compose up -d
   # Ensure pgvector extension exists if using pgvector backend

3. Backend
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

4. Frontend
   cd frontend
   npm install
   npm run dev

Common problems & tips
- CORS preflight errors: ensure the backend CORS config (CORS_ALLOW_ALL or CORS_ALLOWED_ORIGINS) matches the frontend origin (http://localhost:5173).
- Duplicate doctor registration errors: handled by creating NULL registration_number and generated temporary license placeholders for initial rows. Avoid empty-string unique collisions.
- Missing OPENAI_API_KEY: LLM generation will fail; embeddings/completions are skipped or error.
- S3 uploads failing: ensure S3 credentials/bucket are set or run a local MinIO instance.

---

## Security & production notes
- Do not leave `CORS_ALLOW_ALL=true` in production. Use explicit origin allowlists.
- Secrets (JWT_SECRET_KEY, AWS keys, OPENAI_API_KEY) must be managed via a secret manager in production.
- In production consider using a persistent queue for ingestion jobs (e.g., Redis + RQ/Celery/Kafka) rather than an in-process periodic worker.
- Add rate limiting, authentication hardening, request/response logging scrubbing PHI, and monitoring/alerting.

---

## Where to find code
- Backend: `backend/app/` — main modules:
  - [app/main.py](/healthcare-rag-system/backend/app/main.py)
  - [app/core/config.py](/healthcare-rag-system/backend/app/core/config.py)
  - [app/services](/healthcare-rag-system/backend/app/services) — ingestion, retrieval, vector store, patient access
  - [app/models](/healthcare-rag-system/backend/app/models) — DB models
  - [app/api](/healthcare-rag-system/backend/app/api) — routers

- Frontend: `frontend/src/` — main modules:
  - [src/App.jsx](/healthcare-rag-system/frontend/src/App.jsx)
  - [src/context/AuthContext.jsx](/healthcare-rag-system/frontend/src/context/AuthContext.jsx)
  - [src/services/api.js](/healthcare-rag-system/frontend/src/services/api.js)
  - [src/pages](/healthcare-rag-system/frontend/src/pages) — UI pages

---

If you want, next steps I can take:
- Export this file to a PDF or Word document and attach it to a PR or release artifact.
- Add a brief architecture diagram (SVG) and include it in the docs directory.
- Generate a shorter onboarding README for new devs with exact commands and common issues.

If you want any section expanded (ER diagram with full table columns, API request/response examples for each endpoint, or a separate runbook), tell me which and I'll add it.
