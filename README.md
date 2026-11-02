 <div align="center">

# CampusPilot AI

### Your Academic Journey, Powered by AI.

**An intelligent academic copilot that helps students understand their syllabus, learn from study materials, and prepare for examinations.**

[**Live Application**](https://campuspilotai.vercel.app/) · [**GitHub Repository**](https://github.com/GANDHIKALASI/CampusPilotAI)

</div>

---

## Overview

CampusPilot AI is an AI-powered academic companion designed to make university learning more organized, accessible, and effective.

Students often work with lengthy textbooks, scattered lecture notes, complex syllabi, and limited examination preparation time. General-purpose AI assistants can explain concepts, but their responses may not always align with a student's prescribed academic materials.

CampusPilot AI is being developed to address this gap through syllabus-aware learning and retrieval-augmented generation (RAG), connecting AI responses with relevant academic documents.

## What makes it different?

- **Syllabus-aware learning** — organize learning around academic subjects and topics.
- **Document-based assistance** — use academic materials as a knowledge source.
- **Retrieval-augmented generation** — retrieve relevant document passages before generating answers.
- **Source-oriented responses** — support verification against retrieved academic content.
- **Multi-turn conversations** — continue learning through contextual follow-up questions.
- **Student-focused experience** — bring academic assistance into one platform.

## How it works

```text
       STUDENT
          |
          v
   Ask an academic question
          |
          v
     FASTAPI BACKEND
          |
          v
    QUERY PROCESSING
          |
          v
   VECTOR RETRIEVAL
      PostgreSQL
       pgvector
          |
          v
   RELEVANT CONTEXT
          |
          v
      GEMINI AI
          |
          v
   GENERATED RESPONSE
          |
          v
   STUDENT INTERFACE
```

## Core capabilities

| Capability | Description |
|---|---|
| Academic AI assistant | Ask questions about academic subjects |
| Study material support | Work with uploaded academic documents |
| RAG architecture | Retrieve relevant context for AI responses |
| Vector search | Find semantically relevant document chunks |
| Source references | Help students inspect supporting material |
| Student authentication | Supabase-based authentication |
| Credit management | Configurable usage-credit system |
| Admin controls | Admin-oriented access configuration |

## Technology stack

| Layer | Technologies |
|---|---|
| Frontend | Next.js, TypeScript |
| Backend | Python, FastAPI |
| AI | Google Gemini API |
| Embeddings | Gemini Embedding API |
| Database | PostgreSQL, Supabase |
| Vector search | pgvector |
| Authentication | Supabase Auth |
| File storage | Supabase Storage |
| Deployment | AWS EC2 |
| Containerization | Docker, Docker Compose |
| Reverse proxy | Nginx |
| Temporary HTTPS | Cloudflare Quick Tunnel |
| Frontend hosting | Vercel |

## System architecture

```text
                    STUDENT
                       |
                       v
               NEXT.JS FRONTEND
                    VERCEL
                       |
                       v
              CLOUDFLARE TUNNEL
                       |
                       v
                  AWS EC2
                       |
                       v
                    NGINX
                       |
                       v
                FASTAPI BACKEND
                  /    |    \
                 /     |     \
                v      v      v
             GEMINI SUPABASE POSTGRES
                       |
                       v
                    PGVECTOR
```

## Retrieval-Augmented Generation

CampusPilot AI uses a RAG-oriented architecture to connect language-model responses with academic information.

### Document processing

1. Academic PDFs are processed using PyMuPDF.
2. Extracted text is divided into smaller chunks.
3. Chunks are converted into vector embeddings.
4. Embeddings and document metadata are stored in PostgreSQL with pgvector.

### Question answering

1. A student submits an academic question.
2. The question is converted into an embedding.
3. Relevant document chunks are retrieved using vector similarity.
4. Retrieved context is supplied to the language model.
5. Gemini generates a response using the available context.
6. Supporting source information can be presented for verification.

> RAG improves the connection between responses and source documents, but it does not guarantee that every generated answer is correct. Verification against the original material remains important.

## Deployment and infrastructure

CampusPilot AI has been deployed using a containerized backend architecture.

| Component | Deployment |
|---|---|
| Frontend | Vercel |
| Backend API | AWS EC2 |
| API server | FastAPI / Uvicorn |
| Container management | Docker Compose |
| Reverse proxy | Nginx |
| HTTPS connectivity | Cloudflare Quick Tunnel |
| Database services | Supabase |

**Infrastructure note:** The current Cloudflare Quick Tunnel provides temporary HTTPS connectivity. A permanent domain and stable production tunnel configuration remain future deployment improvements.

## Implementation status

| Area | Current status |
|---|---|
| Next.js frontend deployment | Deployed |
| FastAPI backend | Containerized and deployed |
| Docker Compose | Configured and running |
| Nginx reverse proxy | Configured |
| Backend health endpoint | Verified |
| Public API health endpoint | Verified |
| Supabase integration | Configured; full workflow verification pending |
| Gemini integration | Configured; end-to-end verification pending |
| RAG pipeline | Documented and under validation |
| Retrieval evaluation | Evaluation artifacts available |
| Payment integration | Deferred |
| Permanent domain | Planned |
| Local model inference | Planned |

*Status reflects the deployment and validation work completed so far, not a claim that every feature is production-ready.*

## Roadmap

### Phase 1 — Infrastructure and deployment
- [x] Set up the Next.js frontend
- [x] Build the FastAPI backend
- [x] Containerize backend services
- [x] Configure Docker Compose
- [x] Set up Nginx reverse proxy
- [x] Deploy backend on AWS EC2
- [x] Establish temporary HTTPS connectivity

### Phase 2 — Academic intelligence
- [x] Design the RAG architecture
- [x] Document PDF processing and chunking
- [x] Prepare retrieval evaluation artifacts
- [ ] Complete end-to-end RAG validation
- [ ] Improve retrieval quality and relevance
- [ ] Validate source citation accuracy

### Phase 3 — Product improvements
- [ ] Improve multi-turn learning experience
- [ ] Expand academic document management
- [ ] Improve admin workflows
- [ ] Add monitoring and error tracking
- [ ] Perform load and performance testing

### Phase 4 — Advanced AI infrastructure
- [ ] Explore local SLM integration
- [ ] Evaluate CPU-friendly inference
- [ ] Explore model quantization
- [ ] Investigate LoRA and fine-tuning
- [ ] Evaluate edge AI deployment options

### Phase 5 — Production readiness
- [ ] Configure a permanent domain
- [ ] Establish stable HTTPS infrastructure
- [ ] Complete security and access-control review
- [ ] Complete end-to-end testing
- [ ] Evaluate payment integration

## Learning and engineering experience

Building CampusPilot AI has been a practical learning journey across several areas of software engineering:

- Designing a full-stack application with Next.js and FastAPI.
- Building and deploying containerized services.
- Understanding AWS EC2, Linux administration, and EBS storage.
- Configuring Nginx as a reverse proxy.
- Working with Supabase and PostgreSQL.
- Exploring embeddings, vector databases, and RAG.
- Integrating external AI APIs.
- Understanding deployment, environment configuration, and service health checks.

## Meet the developer

**Gandhi Kalasi**

*Full-Stack Developer | AI Systems Enthusiast*

Building software products that combine modern web technologies, backend engineering, and practical AI systems.

CampusPilot AI is an independent project built around a simple idea: make academic learning more accessible and help students study with better context.

**Connect with me**

- [GitHub](https://github.com/GANDHIKALASI)
- [Instagram — @bug_gandhi](https://www.instagram.com/bug_gandhi/)
- [LinkedIn](https://www.linkedin.com/)

Email: `ffgandhi09@gmail.com`

---

## Support the project

If you find CampusPilot AI interesting:

- Star the repository.
- Share feedback and suggestions.
- Report issues through GitHub.
- Follow the project's development.

<div align="center">

**CampusPilot AI**

*Learn smarter. Understand deeper. Prepare better.*

Built with curiosity and a passion for technology.

[Live Application](https://campuspilotai.vercel.app/) · [Source Code](https://github.com/GANDHIKALASI/CampusPilotAI)

</div>
