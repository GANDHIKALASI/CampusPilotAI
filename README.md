# CampusPilot AI 🎓⚡
### The Intelligent AI Academic Copilot & Syllabus Study Companion

<p align="center">
  <strong>Learn smarter. Understand deeper. Prepare better.</strong>
</p>

<p align="center">
  <a href="https://campuspilotai.vercel.app/">
    <img src="https://img.shields.io/badge/Live%20Application-Visit%20CampusPilot-10B981?style=for-the-badge&logo=vercel" alt="Live Application" />
  </a>
  <a href="https://github.com/GANDHIKALASI/CampusPilotAI">
    <img src="https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github" alt="GitHub" />
  </a>
  <img src="https://img.shields.io/badge/AI-Gemini%20Powered-4285F4?style=for-the-badge&logo=google" alt="Gemini" />
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Cloud-AWS%20EC2-FF9900?style=for-the-badge&logo=amazonaws" alt="AWS EC2" />
</p>

<p align="center">
  <img src="frontend/public/logo.jpg" alt="CampusPilot AI Logo" width="130" />
</p>

---

## 📌 Project Overview

**CampusPilot AI** is an AI-powered academic companion designed to help university students understand complex technical subjects, interact with academic study materials, and prepare for examinations more effectively.

University students often deal with large textbooks, scattered lecture notes, lengthy syllabi, and limited preparation time. Generic AI assistants can provide useful explanations, but their answers may not always align with a student's prescribed curriculum or reference materials.

CampusPilot AI aims to bridge this gap through a combination of **Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), semantic search, and academic knowledge retrieval**.

Instead of relying exclusively on general-purpose AI responses, its intended document-grounded architecture retrieves relevant academic information and uses that context to generate more relevant, traceable answers.

**The vision:** An academic assistant that understands the student's learning context, connects answers to study materials, and makes learning more structured and verifiable.

🌐 **Live Application:** https://campuspilotai.vercel.app/

📦 **Source Code:** https://github.com/GANDHIKALASI/CampusPilotAI

---

## 💡 Why CampusPilot AI?

Consider a student preparing for an Operating Systems examination.

They need to understand:
- Process scheduling algorithms.
- Deadlocks and synchronization.
- Virtual memory and paging.
- CPU scheduling calculations.
- Concepts from their prescribed textbook.

Searching through hundreds of pages and combining information from different sources can be time-consuming.

A generic AI chatbot may explain these topics, but it may not necessarily follow the student's exact syllabus or reference material.

CampusPilot AI is designed to provide a more academic-focused experience through:

- Syllabus-oriented learning.
- Academic question answering.
- Document-based knowledge retrieval.
- Context-aware explanations.
- Source-level references.
- Structured examination preparation.

---

## 🎯 How Students Use CampusPilot AI

```text
  1. Explore Syllabus      2. Add Study Materials
  ┌──────────────────┐    ┌──────────────────┐
  │ Select academic  │ -> │ Upload relevant  │
  │ subject/module   │    │ notes and PDFs   │
  └──────────────────┘    └──────────────────┘

  3. Ask & Learn           4. Verify Sources
  ┌──────────────────┐    ┌──────────────────┐
  │ Ask questions    │ -> │ Inspect retrieved│
  │ and understand   │    │ source references│
  └──────────────────┘    └──────────────────┘
```

### 1. Explore Academic Curricula

Navigate through structured subject and module hierarchies.

The documented curriculum coverage includes:

- Operating Systems
- Computer Networks
- Database Management Systems
- Computer Organization and Architecture
- Data Structures and Algorithms

### 2. Work with Study Materials

The document-processing architecture is designed to support academic PDFs, lecture notes, textbooks, and other reference materials.

### 3. Ask Academic Questions

Students can ask questions such as:

- Explain Dijkstra's shortest path algorithm step by step.
- What are the four necessary conditions for deadlock?
- Explain database normalization with examples.
- Describe CPU pipelining and its hazards.

### 4. Understand and Verify Answers

The RAG architecture is designed to retrieve relevant academic passages and associate generated responses with their source documents.

### 5. Revise and Practice

The academic learning roadmap includes practice questions, revision flashcards, module comparisons, and follow-up learning conversations.

---

## ✨ Key Features

### 🔍 1. Academic Question Answering

An AI-powered academic interface for exploring technical concepts, understanding difficult topics, and asking subject-related questions.

### 📚 2. Retrieval-Augmented Generation (RAG)

A document-grounded architecture that combines academic knowledge retrieval with LLM-powered response generation.

Rather than relying only on the model's pre-trained knowledge, the intended pipeline retrieves relevant academic content to provide context for answering questions.

### 📖 3. Semantic Search & Vector Embeddings

Academic content and user queries are represented as numerical embeddings.

Semantic similarity search helps retrieve relevant information based on meaning rather than requiring exact keyword matches.

### 📄 4. Academic PDF Ingestion & Text Chunking

The documented ingestion pipeline uses:

- PDF text extraction with PyMuPDF.
- Text preprocessing.
- Document chunking.
- Chunk metadata and source references.
- Embedding generation.
- Vector storage for retrieval.

The proposed chunking configuration uses approximately 500 tokens per chunk with 75 tokens of overlap.

### 🎯 5. Context-Aware Retrieval

The retrieval layer is designed to identify relevant academic passages based on the student's question and available course materials.

The architecture supports the concept of combining shared academic resources with private student documents.

### 🧠 6. Grounded LLM Response Generation

Retrieved academic passages provide additional context to the language model.

The goal is to produce answers that are more relevant to the student's course materials and less dependent on unsupported general knowledge.

If sufficient supporting material is unavailable, the intended behaviour is to avoid presenting an unsupported answer as verified academic information.

### 🔗 7. Interactive Source-Level Citations

The documented citation design uses source references such as `[S1]` and `[S2]`.

A source reference is intended to provide:

- Original document or book title.
- Relevant page number.
- Extracted source snippet.
- Retrieval match information.

This makes it easier to trace an answer back to its academic reference.

### 🔐 8. Multi-Tenant Document Isolation

The architecture uses Supabase PostgreSQL and Row-Level Security (RLS) to support user-specific document access.

The intended model distinguishes between:

- Shared academic resources.
- Private student documents.
- User-specific retrieval permissions.

### 💬 9. Multi-Turn Conversational Context

The conversational architecture is designed to support follow-up questions and maintain the context of an ongoing academic discussion.

### 📊 10. Retrieval Evaluation & Testing

The repository includes retrieval-related evaluation artifacts and tests, including:

- `retrieval_evaluation_results.json`
- `test_milestone_3_2.py`

These support the evaluation and testing of retrieval behaviour.

### 💳 11. Credit-Based Usage Model

The application has a configured credit-based usage model.

The proposed usage policy includes:
- Initial free credit allocation.
- Credit deduction for successful AI responses.
- No deduction for failed requests.
- Low-credit threshold notifications.
- Subscription-based usage exemptions.

### 👀 12. Visitor Preview & Student Access

The application includes a limited visitor chatbot experience and an invite-only student access model.

Student authentication is handled through Supabase, with administrator-managed account access.

---

## 🧠 AI Architecture & RAG Pipeline

The core knowledge-grounding architecture follows a Retrieval-Augmented Generation workflow.

### Document Ingestion Pipeline

```text
       Academic PDF / Notes
                |
                v
       PDF Text Extraction
             PyMuPDF
                |
                v
        Text Preprocessing
                |
                v
         Text Chunking
       ~500 tokens / chunk
        75-token overlap
                |
                v
        Embedding Generation
         Gemini Embeddings
                |
                v
       Vector Representation
                |
                v
      PostgreSQL + pgvector
                |
                v
          Indexed Knowledge
```

### Question Answering Pipeline

```text
         Student Question
                |
                v
        Query Preprocessing
                |
                v
        Query Embedding
                |
                v
       Semantic Vector Search
                |
                v
      Relevant Context Retrieval
                |
                v
       Retrieved Academic Text
                |
                v
       Gemini LLM Integration
                |
                v
       Context-Grounded Answer
                |
                v
       Source-Level References
                |
                v
          Student Response
```

### Core RAG Components

| Component | Technology / Approach |
|---|---|
| PDF extraction | PyMuPDF |
| Text chunking | Token-based chunking |
| Chunk overlap | 75-token overlap (proposed configuration) |
| Embeddings | Gemini Embedding API |
| Vector dimensions | 768 (configured design target) |
| Vector storage | PostgreSQL + pgvector |
| Similarity retrieval | Cosine similarity |
| Response generation | Google Gemini |
| Knowledge isolation | Supabase RLS |
| Retrieval testing | Python tests and evaluation artifacts |

**Important:** This describes the project's documented RAG architecture and configuration. Individual ingestion, retrieval, citation, and isolation stages should be validated end-to-end before treating the complete pipeline as production-verified.

---

## 🏗️ System Architecture

CampusPilot AI uses a separated frontend and backend architecture.

```text
                 STUDENT / VISITOR
                         |
                         v
                 Next.js Frontend
                      Vercel
                         |
                         v
                Cloudflare Tunnel
                  Temporary HTTPS
                         |
                         v
                   AWS EC2
                    Ubuntu
                         |
                         v
                  Nginx Reverse
                      Proxy
                         |
                         v
                 FastAPI Backend
                    Python
                         |
              +----------+----------+
              |          |          |
              v          v          v
           Gemini     Supabase   pgvector
            LLM       Auth/DB    Retrieval
              |          |          |
              +----------+----------+
                         |
                         v
                 Academic Response
```

### Infrastructure Components

**Frontend**
- Next.js
- TypeScript
- Vercel hosting

**Backend**
- Python
- FastAPI
- REST API architecture

**Cloud Infrastructure**
- AWS EC2
- Ubuntu Linux
- Docker
- Docker Compose
- Nginx reverse proxy

**Connectivity**
- Cloudflare Quick Tunnel
- HTTPS access to the backend through a temporary tunnel hostname

**Data & AI Services**
- Supabase Authentication
- PostgreSQL
- Supabase Storage
- pgvector architecture
- Google Gemini APIs

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js |
| Programming Language | TypeScript |
| Backend | Python |
| API Framework | FastAPI |
| LLM | Google Gemini |
| Embedding Model | Gemini Embedding API |
| PDF Processing | PyMuPDF |
| Vector Database | PostgreSQL + pgvector |
| Authentication | Supabase Auth |
| Database | Supabase PostgreSQL |
| File Storage | Supabase Storage |
| Containerization | Docker |
| Container Management | Docker Compose |
| Reverse Proxy | Nginx |
| Cloud Hosting | AWS EC2 |
| Operating System | Ubuntu Linux |
| Frontend Deployment | Vercel |
| Temporary HTTPS | Cloudflare Quick Tunnel |

---

## ⚙️ Infrastructure Implementation

The project has involved practical deployment and server-management work.

### AWS EC2 Deployment

- Provisioned an AWS EC2 instance.
- Configured an Ubuntu server environment.
- Set up Docker Engine and Docker Compose.
- Built the backend Docker image.
- Deployed the backend and Nginx services.
- Configured container health checks.
- Verified backend availability through HTTP health checks.

### Docker & Nginx

The backend runs inside a Docker container, while Nginx handles incoming HTTP requests and forwards API traffic to FastAPI.

The backend container is not directly exposed through a public host port in the current deployment architecture.

### Cloudflare Tunnel

A Cloudflare Quick Tunnel provides temporary HTTPS connectivity to the EC2-hosted backend.

A systemd service runs the tunnel in the background, independently of the SSH session.

### API Health Verification

The backend exposes a health endpoint:

```bash
curl -i http://localhost/api/health
```

Expected response:

```json
{
  "status": "healthy",
  "app_name": "Campus Pilot AI",
  "version": "1.0.0",
  "env": "production"
}
```

---

## 📍 Project Implementation Status

CampusPilot AI is an evolving project. The following status distinctions are important.

| Area | Current status |
|---|---|
| Next.js frontend deployment | Deployed |
| Vercel hosting | Configured |
| FastAPI backend | Deployed on EC2 |
| Docker containerization | Implemented |
| Docker Compose services | Running |
| Nginx reverse proxy | Configured |
| Cloudflare Quick Tunnel | Running as a systemd service |
| Backend health endpoint | Verified |
| Gemini integration configuration | Configured |
| Supabase authentication integration | Implemented in project |
| Admin access-control logic | Implemented; end-to-end verification pending |
| Credit system | Configured; full user journey verification pending |
| RAG architecture | Documented and developed in project |
| PDF ingestion and vector retrieval | End-to-end production verification pending |
| Interactive source citations | End-to-end production verification pending |
| Multi-tenant RLS isolation | Requires end-to-end verification |
| Local LLM integration | Planned |
| Payment integration | Deferred |

---

## 🗺️ Future Roadmap

The next development phases focus on expanding the platform and improving its reliability.

### Phase 1 — Complete Core Application Flow
- Verify student login and administrator access.
- Complete the dashboard-to-AI interaction flow.
- Verify Gemini responses through the deployed backend.
- Validate credit deduction and balance tracking.
- Improve frontend and backend response performance.

### Phase 2 — Complete & Validate RAG
- Complete academic PDF ingestion.
- Validate embedding generation.
- Verify pgvector indexing and semantic retrieval.
- Improve retrieval relevance.
- Validate source-level citations.
- Test private document isolation.
- Expand retrieval evaluation.

### Phase 3 — Local LLM Integration
- Explore locally hosted language models.
- Evaluate CPU-friendly inference.
- Compare local inference with Gemini.
- Investigate quantization and memory optimization.
- Explore hybrid cloud and local model routing.

### Phase 4 — Academic Intelligence
- Expand syllabus coverage.
- Improve study material assistance.
- Develop practice question generation.
- Expand revision flashcards.
- Improve contextual study conversations.
- Explore personalized learning workflows.

### Phase 5 — Production Infrastructure
- Configure a permanent custom domain.
- Implement permanent HTTPS.
- Improve monitoring and observability.
- Optimize API latency and database performance.
- Strengthen deployment and backup procedures.
- Evaluate production scaling requirements.

---

## 📚 What I Learned Building CampusPilot AI

This project has been a practical learning experience across several areas of software engineering.

**Application Development**
- Building a full-stack application with Next.js and FastAPI.
- Connecting frontend and backend services.
- Designing API-based application workflows.

**AI & Data Systems**
- Understanding LLM integration.
- Learning Retrieval-Augmented Generation.
- Working with embeddings and vector search concepts.
- Exploring document processing and semantic retrieval.
- Understanding grounded generation and source traceability.

**Cloud & DevOps**
- Provisioning AWS EC2 infrastructure.
- Working with Ubuntu Linux servers.
- Containerizing applications with Docker.
- Managing services through Docker Compose.
- Configuring Nginx reverse proxy.
- Managing background processes with systemd.
- Testing deployed APIs and service health.

**Database & Security**
- Working with Supabase and PostgreSQL.
- Understanding authentication and JWT-based access.
- Exploring Row-Level Security.
- Managing environment variables and application configuration.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js and npm
- Git
- Docker and Docker Compose
- Supabase project
- Google Gemini API access

### Clone the Repository

```bash
git clone https://github.com/GANDHIKALASI/CampusPilotAI.git

cd CampusPilotAI
```

### Configure Environment Variables

Start with the example environment files:

```bash
cp .env.example .env
```

Configure the required backend and frontend environment variables using the example files and project configuration.

Typical configuration includes:

- Gemini API credentials.
- Supabase project URL.
- Supabase public and server-side credentials.
- Application environment settings.
- CORS and allowed-host configuration.

**Never commit `.env` files, API keys, service-role credentials, or other secrets to GitHub.**

### Start with Docker Compose

After configuring the required environment:

```bash
docker compose up -d --build
```

Check running services:

```bash
docker compose ps
```

View backend logs:

```bash
docker compose logs -f backend
```

Verify the health endpoint:

```bash
curl -i http://localhost/api/health
```

> Refer to the deployment documentation and environment examples in the repository for the complete configuration and deployment procedure.

---

## 🔒 Security Considerations

CampusPilot AI is designed with separated frontend and backend responsibilities.

Security-related implementation areas include:

- Supabase-based authentication.
- Backend-side token verification.
- Server-side user identity resolution.
- User-specific document access.
- PostgreSQL Row-Level Security architecture.
- Private server-side environment configuration.
- Backend service isolation behind Nginx.

Security and data-isolation guarantees must be validated through deployment-specific testing. Never expose service-role keys, JWT secrets, or API credentials in frontend code.

---

## 👥 Who Is CampusPilot AI For?

🎓 **University Students**

Students looking for academic explanations, syllabus-oriented learning, and more structured examination preparation.

👨‍🏫 **Educators & Teaching Assistants**

Educators exploring AI-assisted academic resources and structured learning support.

📖 **Self-Learners**

Learners interested in understanding foundational computer science and engineering concepts.

---

## 👨‍💻 Meet the Developer

<p align="center">
  <img src="https://github.com/GANDHIKALASI.png" width="130" alt="Gandhi Kalasi" />
</p>

<h3 align="center">Gandhi Kalasi</h3>

<p align="center">
  Full-Stack Developer | AI Systems Enthusiast
</p>

I'm Gandhi Kalasi, a Bachelor of Computer Applications (BCA) student based in Bhubaneswar, Odisha, India.

I enjoy building practical software applications that combine modern web technologies, backend systems, AI models, and cloud infrastructure.

CampusPilot AI is one of my ongoing projects, built to explore how AI can make academic learning more accessible and how complete applications can be engineered and deployed using modern technologies.

**My goal is to keep learning by building real-world systems.**

<p align="center">
  <a href="https://github.com/GANDHIKALASI">
    <img src="https://img.shields.io/badge/GitHub-GANDHIKALASI-181717?style=for-the-badge&logo=github" alt="GitHub" />
  </a>
  <a href="https://www.linkedin.com/in/gandhi-kalasi/">
    <img src="https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=for-the-badge&logo=linkedin" alt="LinkedIn" />
  </a>
  <a href="https://portfolio-one-dun-f2390maeuj.vercel.app/">
    <img src="https://img.shields.io/badge/Portfolio-Visit-000000?style=for-the-badge&logo=vercel" alt="Portfolio" />
  </a>
</p>

---

## 🌟 Support & Contributions

If you find CampusPilot AI interesting:

- ⭐ Star the [GitHub repository](https://github.com/GANDHIKALASI/CampusPilotAI).
- 📢 Share it with students and developers.
- 💡 Suggest new features and improvements.
- 🐛 Report issues and bugs.
- 🤝 Contribute ideas to improve the project.

---

<p align="center">
  <strong>CampusPilot AI 🎓⚡</strong>
  <br />
  Learn smarter. Understand deeper. Prepare better.
  <br /><br />
  Built with ❤️ by <a href="https://github.com/GANDHIKALASI">Gandhi Kalasi</a>
</p>

<p align="center">
  <sub>From an idea to an evolving AI-powered academic platform.</sub>
</p>
