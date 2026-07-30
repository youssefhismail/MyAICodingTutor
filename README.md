# MyAICodingTutor

An AI-powered coding tutor that allows users to upload source code or text files and ask natural language questions about them. The application uses Azure AI Foundry to generate context-aware responses while FastAPI handles the backend API and Supabase persists uploaded documents and conversation history.

This project was built as part of my Machine Learning internship to explore modern AI application architecture, backend development, and LLM integration.

---

# Features

## Current

- Upload a single source code or text file
- Ask questions about the uploaded document
- AI responses grounded in the uploaded file
- Persistent chat history stored in Supabase
- Session-based conversations
- FastAPI REST API backend
- Streamlit frontend
- Modular service-oriented architecture
- Azure AI Foundry integration
- Document persistence independent of the frontend

---

# Tech Stack

## Frontend

- Streamlit

## Backend

- FastAPI
- Pydantic

## AI

- Azure AI Foundry

## Database

- Supabase
- PostgreSQL

## Language

- Python

---

# Architecture

```
                Streamlit Frontend
                        │
                        ▼
                 FastAPI Backend
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
 Document Service   Chat Service    Session Service
        │               │
        └───────────────┼───────────────┐
                        ▼               ▼
                  Supabase        Azure AI Foundry
                 PostgreSQL            LLM
```

The frontend is responsible only for user interaction.

The backend owns:

- uploaded documents
- conversation history
- prompt construction
- communication with the LLM

This separation keeps the frontend lightweight while centralizing business logic inside the API.

---

# Project Structure

```
MyAICodingTutor/
│
├── backend/
│   ├── api/
│   │   ├── chat.py
│   │   ├── sessions.py
│   │   └── upload.py
│   │
│   ├── database/
│   │   └── supabase.py
│   │
│   ├── models/
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
│   ├── app.py
│   └── config.py
│
├── requirements.txt
└── README.md
```

The project follows a layered architecture where:

- API routes handle HTTP requests.
- Services contain business logic.
- Database helpers encapsulate all Supabase operations.
- Models define request and response schemas.

---

# Database Design

Conversation history is stored using a message-based schema similar to modern chat APIs.

Each message is stored as an individual record:

| role | content |
|------|---------|
| user | Question |
| assistant | Response |

This design makes conversations easier to extend with future roles such as:

- system
- tool

and aligns with the OpenAI/Azure chat message format.

Uploaded documents are stored separately and associated with a session.

---

# Running the Project

## 1. Clone the repository

```bash
git clone https://github.com/<your-username>/MyAICodingTutor.git

cd MyAICodingTutor
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

## 3. Configure environment variables

Create a `.env` file.

Example:

```env
AZURE_API_KEY=
AZURE_ENDPOINT=
AZURE_DEPLOYMENT_NAME=

SUPABASE_URL=
SUPABASE_KEY=

BACKEND_BASE_URL=http://localhost:8000
```

---

## 4. Start the backend

```bash
uvicorn backend.main:app --reload
```

---

## 5. Start the frontend

```bash
streamlit run frontend/app.py
```

---

# Current Workflow

1. Create a new chat session.
2. Upload a supported source code or text file.
3. The backend stores the document in Supabase.
4. Ask questions about the uploaded file.
5. Conversation history is automatically persisted.
6. Previous sessions can be revisited.

---

# Supported Files

Examples include:

- `.py`
- `.java`
- `.cpp`
- `.c`
- `.js`
- `.ts`
- `.html`
- `.css`
- `.md`
- `.txt`

Additional text-based formats can be added easily.

---

# Future Improvements

- Retrieval-Augmented Generation (RAG)
- Embeddings
- pgvector integration
- Repository-wide analysis
- Multi-file projects
- Authentication
- User accounts
- Streaming responses
- Docker deployment
- CI/CD pipeline

---

# Learning Objectives

This project was built to gain hands-on experience with:

- Large Language Model integration
- FastAPI backend development
- REST API design
- Service-oriented architecture
- PostgreSQL database design
- Supabase
- Prompt engineering
- AI application development
- Full-stack Python development

---

# License

This project is intended for educational and portfolio purposes.