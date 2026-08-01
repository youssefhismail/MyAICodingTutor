# MyAICodingTutor

An AI-powered coding tutor that helps learners understand code through natural language conversations.

The application allows users to upload one or more source code files, ask questions about them, and receive explanations powered by Azure AI Foundry. It is built using a modular, production-style architecture with FastAPI, Streamlit, and Supabase. The project now implements a complete Retrieval-Augmented Generation (RAG) pipeline with document chunking, embeddings, semantic retrieval, and explainable AI responses.

---

# Features

- 🤖 AI-powered coding tutor using Azure AI Foundry
- ⚡ Streaming AI responses
- 📂 Upload multiple files into a single chat session
- 📝 Supports Python scripts, Jupyter Notebooks, Markdown, and plain text files
- 💬 Persistent chat conversations
- 📄 Individual document management (upload & delete)
- 🗂 Session history with conversation restoration
- 📑 Automatic document chunking for Retrieval-Augmented Generation (RAG)
- 🧱 Clean layered architecture (API → Services → Database)
- 🐳 Fully Dockerized with Docker Compose
- ☁️ Supabase PostgreSQL persistence
- 🚀 Complete RAG pipeline with explainable responses
- 🧩 Automatic document chunking
- 🧠 Azure OpenAI embeddings
- 🔍 Semantic vector search (pgvector)
- 📚 Retrieval-Augmented Generation (RAG)
- 📌 Source citations
- 🔎 Retrieval transparency
- 🛠 Debug retrieval mode
- 📊 Retrieval quality metrics
---

# Supported File Types

| File Type | Supported |
|------------|-----------|
| Python (.py) | ✅ |
| Jupyter Notebook (.ipynb) | ✅ |
| Markdown (.md) | ✅ |
| Plain Text (.txt) | ✅ |

Jupyter notebooks are automatically parsed into a clean textual representation by extracting Markdown and code cells while ignoring notebook metadata and outputs.

---

# Technology Stack

## Backend

- FastAPI
- Uvicorn
- Pydantic

## Frontend

- Streamlit

## AI

- Azure AI Foundry
- Azure OpenAI Chat Models

## Database

- Supabase
- PostgreSQL

## DevOps

- Docker
- Docker Compose

---

# Project Structure

```text
MyAICodingTutor/

├── backend/
│
│   ├── api/
│   │   ├── chat.py
│   │   ├── documents.py
│   │   ├── sessions.py
│   │   └── upload.py
│   │
│   ├── database/
│   │   └── supabase.py
│   │
│   ├── models/
│   │   ├── domain.py
│   │   ├── requests.py
│   │   └── responses.py
│   │
│   ├── services/
│   │   ├── chat_service.py
│   │   ├── chunk_service.py
│   │   ├── llm_service.py
│   │   ├── prompt_service.py
│   │   └── upload_service.py
│   │
│   ├── utils/
│   ├── config.py
│   └── main.py
│
├── frontend/
│   ├── api/
│   ├── services/
│   ├── ui/
│   ├── config.py
│   └── app.py
│
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# Architecture

```text
                    Streamlit Frontend
                           │
                           ▼
                    FastAPI Backend
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
     API Routes       Service Layer     Database Layer
                           │
                           ▼
               ┌────────────────────────┐
               │   Retrieval Pipeline   │
               └────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
    Chunk Service    Embedding Service   Retrieval Service
                           │
                           ▼
                    Azure AI Foundry
                           │
                           ▼
               Supabase PostgreSQL + pgvector
```

---

# Current Workflow

## Upload Documents

```text
User

↓

Upload one or more files

↓

FastAPI Upload Endpoint

↓

Document Parser

↓

Chunk Service

↓

Embedding Service

↓

Supabase Database

↓

Documents
+
Document Chunks
+
Vector Embeddings
```

---

## Ask Questions

```text
User Question

↓

Generate Query Embedding

↓

pgvector Semantic Search

↓

Retrieve Top-K Relevant Chunks

↓

Prompt Builder

↓

Azure AI Foundry

↓

Streaming Response

↓

Source Citations & Retrieval Metadata
```

---

# Database Design

## Sessions

Stores conversation metadata.

```text
sessions

id
title
created_at
updated_at
```

---

## Messages

Stores the conversation history.

```text
messages

id
session_id
role
content
sequence
created_at
```

Messages are stored sequentially.

Example:

```text
0 User
1 Assistant
2 User
3 Assistant
```

This structure supports an unlimited conversation history.

---

## Documents

Stores every uploaded file associated with a session.

```text
documents

id
session_id
filename
content
uploaded_at
```

Each session may contain multiple uploaded documents.

```text
Session

├── app.py
├── database.py
├── models.py
└── notebook.ipynb
```

---

## Document Chunks

Stores the individual chunks created from uploaded documents.

```text
document_chunks

id
document_id
sequence_number
start_offset
end_offset
content
embedding
created_at
```

Each uploaded document is automatically divided into overlapping chunks using a hierarchical text splitter that prefers:

- Paragraph boundaries
- Line boundaries
- Word boundaries
- Character boundaries (fallback)

The resulting chunks form the foundation of the Retrieval-Augmented Generation (RAG) pipeline and are embedded and indexed for semantic retrieval.
---

# Backend Architecture

The backend follows a layered architecture.

```text
API Layer

↓

Service Layer

↓

Database Layer
```

## API Layer

Responsible for:

- HTTP endpoints
- Request validation
- Response models

Contains no business logic.

---

## Service Layer

Responsible for:

- Upload workflow
- Document chunking
- Embedding generation
- Retrieval orchestration
- Prompt construction
- Azure AI interaction

Contains all business logic.

---

## Database Layer

Responsible only for:

- CRUD operations
- Supabase queries
- pgvector similarity search
- Data persistence

Contains no business logic.

---

# Docker

The application is fully containerized.

Services:

- Backend
- Frontend

Run everything with:

```bash
docker compose up --build
```

Stop:

```bash
docker compose down
```

---

# Local Development

## Clone

```bash
git clone <repository-url>
cd MyAICodingTutor
```

---

## Create Environment

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Environment

Create a `.env` file containing:

```env
SUPABASE_URL=
SUPABASE_KEY=

FOUNDRY_ENDPOINT=
FOUNDRY_API_KEY=
DEPLOYMENT_NAME=
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large

BACKEND_BASE_URL=http://localhost:8000
```

> [!NOTE]
> The chat (`DEPLOYMENT_NAME`) and embedding (`AZURE_OPENAI_EMBEDDING_DEPLOYMENT`) features utilize completely separate Azure AI Foundry deployments. Ensure both are correctly provisioned in your Azure environment.

---

## Run Backend

```bash
uvicorn backend.main:app --reload
```

---

## Run Frontend

```bash
streamlit run frontend/app.py
```

---

# Design Principles

The project follows several architectural principles:

- Separation of concerns
- Layered architecture
- Thin API routes
- Strong typing
- Modular services
- Single responsibility
- Docker-first development
- Extensible design for future AI capabilities

---

# Current Capabilities

- AI coding assistant
- Streaming AI responses
- Multiple uploaded documents per conversation
- Persistent conversations
- Conversation history
- Individual document deletion
- Automatic document chunking
- Hierarchical text splitting
- Jupyter Notebook parsing
- Azure embeddings
- Semantic retrieval
- Source citations
- Retrieval transparency
- Debug retrieval
- Retrieval statistics
- Docker deployment
- Azure AI integration
- Supabase persistence
---

# Future Roadmap

## ✅ Phase 1 — Document Chunking (Completed)

Implemented:

- Document ingestion pipeline
- Hierarchical document chunking
- Configurable chunk size and overlap
- Chunk metadata (sequence number, offsets)
- Automatic chunk generation during upload
- Transaction-safe upload workflow
- `document_chunks` database table

---

## ✅ Phase 2 — Embeddings (Completed)

Implemented:

- Azure AI Foundry embedding model
- pgvector integration
- Automatic embedding generation
- Store vector embeddings alongside document chunks

---

## ✅ Phase 3 — Semantic Retrieval (Completed)

Implemented:

- Embed user questions
- Vector similarity search
- Retrieve Top-K relevant chunks
- Context ranking

---

## ✅ Phase 4 — Explainable RAG (Completed)

Implemented:

- Prompt augmentation
- Ground responses using retrieved chunks
- Source citations
- Retrieval transparency
- Debug retrieval
- Reduce hallucinations

---

## 🚀 Phase 5 — Advanced Retrieval (Planned)

Planned:

- Hybrid search
- Cross-file retrieval diversification
- Reranking
- Adaptive retrieval
- Notebook-aware chunking
- Repository uploads
- Inline clickable citations

# Learning Objectives

This project was developed to gain hands-on experience with:

- FastAPI
- Streamlit
- Azure AI Foundry
- Prompt engineering
- Supabase
- PostgreSQL
- Docker
- REST API design
- Layered software architecture
- AI application development
- Retrieval-Augmented Generation (RAG)
- Document chunking
- Vector databases
- Semantic search
- Retrieval-Augmented Generation (RAG)
- Document chunking
- Vector embeddings
- Semantic search
- Explainable AI
- Streaming APIs (SSE)
---

# License

This project was developed as part of an internship and educational learning experience.

Feel free to use the architecture and ideas for learning purposes.