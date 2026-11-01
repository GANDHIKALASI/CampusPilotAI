# CampusPilot AI 🎓⚡

> **Production-Grade AI Academic Copilot & Intelligent Retrieval-Augmented Generation (RAG) Platform for University Engineering Students.**

[![Next.js](https://img.shields.io/badge/Next.js-16.4-black?logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.14-3776AB?logo=python)](https://python.org)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL%20%7C%20pgvector-3ECF8E?logo=supabase)](https://supabase.com)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-Flash%20Lite%20%7C%20Embedding--2-4285F4?logo=google)](https://ai.google.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?logo=typescript)](https://www.typescriptlang.org/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-v4-38B2AC?logo=tailwindcss)](https://tailwindcss.com/)

---

## 🌟 Overview

**CampusPilot AI** is an end-to-end, full-stack AI learning companion tailored for university engineering curricula. It allows students to upload textbooks, lecture slides, and syllabus documents, chat with their academic materials using state-of-the-art multimodal AI, and receive verified answers backed by grounded, interactive citations.

Designed for production resilience and cloud scale (AWS deployment ready), CampusPilot AI combines **Next.js 16 App Router**, **FastAPI**, **Supabase PostgreSQL with pgvector**, and **Google Gemini** into a secure, distributed, and multi-tenant academic assistant.

---

## 🏗️ System Architecture

```mermaid
graph TD
    User([🎓 Student Browser])
    
    subgraph Frontend ["Next.js 16 (App Router + Turbopack)"]
        UI[Interactive Chat UI & Sources Tray]
        AuthModal[Supabase Auth & Session]
        BadgeRenderer[Citation Badge Renderer [S1]]
    end

    subgraph Backend ["FastAPI Backend (Python 3.14)"]
        API[API Router /conversations]
        Heartbeat[Lease Heartbeat ~15s]
        Idempotency[Idempotency Service]
        RAG[RAG Orchestrator]
    end

    subgraph AI ["Google Gemini AI"]
        EmbedAPI[gemini-embedding-2]
        LLMAPI[gemini-3.5-flash-lite]
    end

    subgraph Database ["Supabase PostgreSQL + pgvector"]
        VectorDB[(document_chunks pgvector)]
        IdemTable[(idempotency_keys RPC)]
        BillingDB[(profiles & credit_transactions)]
        DocDB[(documents & messages)]
    end

    User <--> UI
    UI <--> API
    API <--> Idempotency
    Idempotency <--> IdemTable
    API --> Heartbeat
    API <--> RAG
    RAG <--> EmbedAPI
    RAG <--> VectorDB
    RAG <--> LLMAPI
    API <--> BillingDB
    API <--> DocDB
```

---

## 🚀 Key Features

### 1. 📚 Structure-Aware Ingestion & Semantic Chunking
- Automated PDF parsing via **PyMuPDF** (`pymupdf`).
- Contextual chunking with clean typography normalization, mathematical formula preservation, and header/footer artifact removal.
- Chunks tagged with academic metadata: `subject_code`, `module_number`, `page_number`, and `scope` (`student_personal` vs `shared_curriculum`).

### 2. 🎯 Precision RAG Pipeline & Threshold Calibration
- Vector embeddings computed via **Google Gemini `gemini-embedding-2`** (768-dimensional space).
- Cosine distance similarity search via pgvector RPC (`match_document_chunks`).
- Empirically calibrated similarity threshold at **`0.60`**:
  - **100.0% Negative Query Rejection:** Out-of-syllabus or unanswerable queries cleanly trigger model abstention without hallucinated answers.
  - **82.35% Top-5 Hit Rate & 0.7010 MRR** on complex multi-category engineering questions.
  - Sub-second retrieval latency and cost of under **$0.00013 per turn**.

### 3. 🔍 Interactive Citation UI & Grounded Sources
- Inline citation badges rendered in markdown (`[S1]`, `[S2]`).
- Hover and click interactions launch a glassmorphic **Source Detail Modal** displaying:
  - Document Title, Subject, and Exact Page Number.
  - Relevance Similarity Score badge.
  - High-fidelity **400-character context snippet** from the source document.
- Accessible **Sources Tray** footer with keyboard navigation and focus management.

### 4. 🛡️ Distributed Idempotency & Owner-Token Fencing
- Built for multi-instance horizontal scaling on AWS.
- Background **Lease Heartbeat** renews ownership approximately every 15 seconds for long-running AI queries.
- **Strict Fencing:** Stale workers losing ownership are prevented from saving messages, mutating state, or charging credits.
- **Fail-Closed in Production:** Never silently degrades to process-local SQLite in production environments (`APP_ENV=production`).

### 5. 💳 Atomic Single-Transaction Billing
- Zero credit loss guarantee: Credit balances are locked (`SELECT FOR UPDATE`) and deducted **only within the same PostgreSQL transaction** that commits the AI conversation turn.
- AI failure, RAG timeout, or network disconnect results in **zero credit deduction**.
- Duplicate retry requests return the exact cached response with zero additional charges and zero extra LLM API invocations.

---

## 📂 Project Structure

```
CampusPilotAI/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # FastAPI REST endpoints (conversations, chat, documents, admin)
│   │   ├── core/                # Auth, settings, curriculum, and prompt templates
│   │   ├── schemas/             # Pydantic v2 validation contracts (RAG, conversation, billing)
│   │   ├── services/            # Core business logic (RAG, idempotency, Gemini, Supabase)
│   │   └── main.py              # Application entrypoint & CORS middleware
│   ├── migrations/              # PostgreSQL schema migrations (001 to 007_idempotency_keys.sql)
│   ├── scripts/                 # Ingestion & embedding backfill utilities
│   ├── tests/                   # 50+ unit, live RAG, and concurrency test suites
│   ├── requirements.txt         # Python dependencies
│   └── .env.example             # Environment configuration template
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js App Router pages (Dashboard, Learning, Pricing, Admin)
│   │   ├── components/          # Reusable React components (CitationViewer, MarkdownRenderer)
│   │   ├── context/             # Global dashboard application state
│   │   ├── lib/                 # Supabase client & backend API HTTP client
│   │   └── types/               # TypeScript interfaces matching backend models
│   ├── package.json             # Frontend dependencies (React 19, Next.js 16, Tailwind v4)
│   └── tsconfig.json            # Strict TypeScript configuration
└── README.md                    # Root project documentation
```

---

## ⚡ Getting Started

### Prerequisites
- **Node.js:** `v20.x` or later
- **Python:** `3.11` or `3.14`
- **Docker:** (Optional, for running local pgvector test database)
- **Supabase Account:** (Free tier or hosted instance with pgvector enabled)
- **Google AI Studio API Key:** For Gemini LLM and embeddings

---

### Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your credentials:
   ```env
   APP_ENV=development
   GEMINI_API_KEY=your_gemini_api_key
   GEMINI_MODEL=gemini-3.5-flash-lite
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_PUBLISHABLE_KEY=your_supabase_anon_key
   SUPABASE_SECRET_KEY=your_supabase_service_role_key
   ```

5. **Run the FastAPI server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   API interactive documentation will be live at `http://localhost:8000/docs`.

---

### Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env.local
   ```
   Edit `.env.local`:
   ```env
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Start the Next.js development server:**
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🧪 Running Tests & Quality Verification

### 1. Backend Test Suite (50 Scenarios)
Execute the complete unit and integration test suite (covering multi-turn history, atomic credits, heartbeat lease renewal, and fencing):
```bash
PYTHONPATH=backend python -m unittest discover -s backend/tests -p "test_*.py"
```

### 2. Live RAG Conversation Concurrency Suite (38 Scenarios)
Run the dedicated conversational reliability and idempotency test suite:
```bash
PYTHONPATH=backend python -m unittest backend.tests.test_live_rag_conversation_suite
```

### 3. End-to-End RAG Evaluation Benchmark
Run the comprehensive multi-tenant RAG benchmark (evaluates 30 academic chunks across 5 engineering subjects):
```bash
PYTHONPATH=backend python backend/tests/test_e2e_rag_evaluation.py
```

### 4. Frontend Production Build Check
Verify TypeScript types, route generation, and Turbopack bundle:
```bash
cd frontend && npm run build
```

---

## 🗄️ Database Migrations

Database schemas and stored procedures are organized sequentially in `backend/migrations/`:

| Migration | Purpose |
| :--- | :--- |
| `001_phase3_3_schema.sql` | Baseline profiles, documents, and message tables |
| `002_shared_documents.sql` | Multi-tenant shared vs personal document isolation |
| `003_admin_billing_credits.sql` | Subscription tiers (`free`, `monthly`, `yearly`) & credit transactions |
| `004_pgvector_storage.sql` | Enables `vector` extension and creates `document_chunks` table |
| `005_match_document_chunks_rpc.sql`| Vector similarity search RPC (`match_document_chunks`) |
| `006_academic_curriculum_structure.sql`| University curricula, subject nodes, and syllabus hierarchy |
| `007_idempotency_keys.sql` | Distributed idempotency, owner tokens, lease renewal & atomic turn commit |

---

## 🔒 Security Best Practices

- **Zero Secrets Committed:** Credentials and API keys are strictly injected via environment variables; `.env*` files are excluded by `.gitignore`.
- **Row-Level Security (RLS):** All student documents and conversation records are protected by Supabase RLS policies.
- **Schema Isolation:** PostgreSQL functions enforce `SECURITY DEFINER` with fixed `search_path = public, pg_temp;` to prevent search-path injection.
- **Fail-Closed Architecture:** Multi-worker deployments refuse unauthenticated or unleased operations.

---

## 👤 Author

Developed by **[GANDHIKALASI](https://github.com/GANDHIKALASI)**.  
Feedback, contributions, and bug reports are welcome via GitHub Issues and Pull Requests!
