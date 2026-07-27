"""Persist and retrieve conversation messages."""

from database.supabase import get_supabase_client
from services.llm_service import ask_llm
from services.prompt_service import build_prompt
from utils.validators import require_text


def save_message(session_id: str, filename: str, question: str, answer: str) -> None:
    """Save one question-and-answer pair to the messages table."""
    session_id = require_text(session_id, "Session ID")
    filename = require_text(filename, "Filename")
    question = require_text(question, "Question")
    answer = require_text(answer, "Answer")
    try:
        get_supabase_client().table("messages").insert(
            {
                "session_id": session_id,
                "filename": filename,
                "question": question,
                "answer": answer,
            }
        ).execute()
    except Exception as error:
        raise RuntimeError(f"Supabase save failed: {error}") from error


def load_messages(session_id: str) -> list[dict[str, str]]:
    """Load persisted messages for one session in their creation order."""
    session_id = require_text(session_id, "Session ID")
    try:
        response = (
            get_supabase_client()
            .table("messages")
            .select("session_id, filename, question, answer")
            .eq("session_id", session_id)
            .order("created_at")
            .execute()
        )
    except Exception as error:
        raise RuntimeError(f"Supabase load failed: {error}") from error

    return response.data or []


def delete_messages(session_id: str) -> None:
    """Delete all persisted messages for one session."""
    session_id = require_text(session_id, "Session ID")
    try:
        get_supabase_client().table("messages").delete().eq("session_id", session_id).execute()
    except Exception as error:
        raise RuntimeError(f"Supabase delete failed: {error}") from error


def submit_question(
    session_id: str,
    filename: str,
    system_prompt: str,
    context: str,
    question: str,
) -> dict[str, str]:
    """
    Generate an answer grounded in the uploaded file,
    persist the interaction to Supabase,
    and return the message for the UI.
    """
    session_id = require_text(session_id, "Session ID")
    filename = require_text(filename, "Filename")
    question = require_text(question, "Question")
    if not context.strip():
        raise ValueError("Upload a UTF-8 text file before asking a question.")

    prompt = build_prompt(system_prompt, context, question)
    answer = ask_llm(prompt)
    save_message(session_id=session_id, filename=filename, question=question, answer=answer)
    return {
        "question": question,
        "answer": answer,
    }
