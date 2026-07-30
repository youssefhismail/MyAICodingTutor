"""Orchestrate conversation interactions."""

from backend.database.supabase import (
    get_documents_by_session,
    save_exchange,
    load_first_user_messages,
    load_messages,
)
from backend.services.llm_service import ask_llm
from backend.services.prompt_service import build_prompt
from backend.utils.validators import require_text
from backend.config import DEFAULT_SYSTEM_PROMPT


def load_conversation_summaries() -> list[dict[str, str]]:
    """Load one summary row per session for the sidebar.

    Combines the first user message from each session with the filename(s)
    from the documents table.  Returns newest-first.
    """
    first_messages = load_first_user_messages()

    summaries: list[dict[str, str]] = []
    for message in first_messages:
        session_id = str(message["session_id"])

        documents = get_documents_by_session(session_id)
        if len(documents) == 0:
            filename = ""
        else:
            filename = ", ".join(doc.filename for doc in documents)

        summaries.append(
            {
                "session_id": session_id,
                "filename": filename,
                "first_question": message.get("content", ""),
                "created_at": message.get("created_at", ""),
            }
        )

    return list(reversed(summaries))


def submit_question(
    session_id: str,
    question: str,
) -> dict[str, str]:
    """
    Generate an answer grounded in the uploaded file,
    persist the interaction to Supabase,
    and return the message for the UI.

    The document and conversation history are retrieved server-side
    so the frontend only needs to provide session_id and question.
    """
    session_id = require_text(session_id, "Session ID")
    question = require_text(question, "Question")

    documents = get_documents_by_session(session_id)
    if not documents:
        raise ValueError("Upload a file before asking a question.")

    chat_history = load_messages(session_id)

    prompt = build_prompt(DEFAULT_SYSTEM_PROMPT, documents, chat_history, question)
    answer = ask_llm(prompt)
    save_exchange(session_id=session_id, question=question, answer=answer)
    return {
        "question": question,
        "answer": answer,
    }
