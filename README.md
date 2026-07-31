# MyAICodingTutor

An AI-powered coding tutor that helps learners understand code through natural language conversations.

The application allows users to upload one or more source code files, ask questions about them, and receive explanations powered by Azure AI Foundry. It is designed with a modular, production-style architecture using FastAPI, Streamlit, and Supabase, and is structured to support Retrieval-Augmented Generation (RAG) in future iterations.

---

# Features

- 🤖 AI-powered coding tutor using Azure AI Foundry
- 📂 Upload multiple files into a single chat session
- 📝 Supports Python scripts, Jupyter Notebooks, Markdown, and plain text files
- 💬 Persistent chat conversations
- 📄 Individual document management (upload & delete)
- 🗂 Session history with conversation restoration
- 🧱 Clean layered architecture (API → Services → Database)
- 🐳 Fully Dockerized with Docker Compose
- ☁️ Supabase PostgreSQL persistence
- 🚀 Designed for future Retrieval-Augmented Generation (RAG)

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
                     Azure AI Foundry
                           │
                           ▼
                     Supabase PostgreSQL
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

Supabase Database

↓

Session Documents
```

---

## Ask Questions

```text
User Question

↓

Retrieve Session Documents

↓

Prompt Builder

↓

Azure AI Foundry

↓

Assistant Response

↓

Conversation Saved
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
- Chat orchestration
- Prompt construction
- Azure AI interaction

Contains all business logic.

---

## Database Layer

Responsible only for:

- CRUD operations
- Supabase queries
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

Windows

```bash
.venv\Scripts\activate
```

Linux / macOS

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

AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_DEPLOYMENT=

BACKEND_BASE_URL=http://localhost:8000
```

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
- Multiple uploaded documents per conversation
- Persistent conversations
- Conversation history
- Individual document deletion
- Jupyter Notebook parsing
- Docker deployment
- Azure AI integration
- Supabase persistence

---

# Future Roadmap

## Retrieval-Augmented Generation (RAG)

Planned architecture:

```text
Session

↓

Documents

↓

Document Chunks

↓

Embeddings

↓

Vector Search

↓

Relevant Chunks

↓

Prompt Builder

↓

Azure AI Foundry
```

Future improvements include:

- Vector embeddings
- pgvector integration
- Semantic document retrieval
- Repository uploads
- Streaming LLM responses
- Authentication
- User accounts
- Conversation export
- Code execution sandbox
- Advanced document parsing

---

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
- Retrieval-Augmented Generation (upcoming)

---

# License

This project was developed as part of an internship and educational learning experience.

Feel free to use the architecture and ideas for learning purposes.