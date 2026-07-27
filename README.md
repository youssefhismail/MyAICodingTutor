# FileAI

An AI-powered file assistant that enables users to upload code or text files and interact with them using natural language. The assistant analyzes the uploaded file and answers questions based solely on its contents, making it useful for understanding code, documentation, notes, and other text-based resources.

This project is being developed incrementally following modern AI engineering practices. The initial version focuses on a single uploaded file and a single conversation, with future versions introducing Retrieval-Augmented Generation (RAG), vector search, FastAPI, and Docker deployment.

---

## Features

### Version 1 (Current)

- Upload a single file (`.py`, `.js`, `.ts`, `.txt`, `.md`, etc.)
- Chat with the uploaded file
- AI responses grounded in the file's contents
- Editable system prompt
- Conversation history during the session
- Chat persistence using Supabase
- Modular architecture with reusable functions

### Planned Features

- Retrieval-Augmented Generation (RAG)
- Embedding generation
- Semantic search with pgvector
- Multi-file & repository support
- FastAPI backend
- Docker containerization
- Richer UI
- Authentication & user sessions
- Conversation memory

---

## Tech Stack

### Current

- Python
- Streamlit
- Azure AI Foundry
- Supabase (PostgreSQL)

### Planned

- Supabase Vector (pgvector)
- FastAPI
- Docker

---

## Architecture

```
                Streamlit
                    │
                    ▼
              Application Layer
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
   Supabase DB            Azure AI Foundry
(PostgreSQL)                 (LLM)
```

Future architecture:

```
                Streamlit
                    │
                    ▼
                FastAPI
                    │
                    ▼
          Retrieval Pipeline (RAG)
                    │
        ┌───────────┴────────────┐
        ▼                        ▼
 Supabase (PostgreSQL)    Supabase Vector
                              (pgvector)
                    │
                    ▼
             Azure AI Foundry
```

---

## Project Structure

```
file-ai/
│
├── app.py
├── config.py
│
├── services/
│   ├── file_service.py
│   ├── prompt_service.py
│   ├── llm_service.py
│   └── chat_service.py
│
├── database/
│   └── supabase.py
│
├── utils/
│   └── validators.py
│
└── requirements.txt
```

Each module has a single responsibility, making the project modular, reusable, and easy to extend.

---

## Development Roadmap

### ✅ V1

- Upload one file
- One conversation
- Ask questions about the file
- Streamlit UI
- Azure AI Foundry
- Supabase persistence

### 🚧 V2

- RAG
- Embeddings
- pgvector
- Semantic search

### 🚧 V3

- FastAPI backend
- Docker
- Multi-file support
- Repository analysis

---

## Future Ideas

- Explain functions and classes
- Detect potential bugs
- Summarize files
- Generate documentation
- Code review assistant
- Repository-wide search
- GitHub integration

---

## Getting Started

### Clone the repository

```bash
git clone https://github.com/<username>/FileAI.git
cd FileAI
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure environment variables

Create a `.env` file and add:

```env
AZURE_API_KEY=
AZURE_ENDPOINT=
AZURE_DEPLOYMENT_NAME=

SUPABASE_URL=
SUPABASE_KEY=
```

### Run

```bash
streamlit run app.py
```

---

## Goal

The purpose of this project is to explore modern AI application development by combining Large Language Models with modular software architecture, conversational interfaces, and scalable backend technologies. The project will progressively evolve from a simple file-aware assistant into a production-style AI application utilizing Retrieval-Augmented Generation (RAG) and semantic search.

---

## License

MIT License
