"""Orchestrate conversation interactions."""

import time
from collections.abc import Generator
from typing import Any

from backend.database.supabase import (
    get_documents_by_session,
    save_exchange,
    load_first_user_messages,
    load_messages,
)
from backend.services.llm_service import ask_llm, stream_llm
from backend.services.prompt_service import build_prompt
from backend.services.retrieval_service import retrieve_chunks
from backend.models.domain import StreamEvent, RetrievalMetadata
from backend.utils.validators import require_text
from backend.config import DEFAULT_SYSTEM_PROMPT, TOP_K_RETRIEVAL


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


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _prepare_conversation(session_id: str, question: str) -> tuple[str, str, str, RetrievalMetadata]:
    """Validate inputs and assemble the LLM prompt.

    Shared by the blocking (``submit_question``) and streaming
    (``stream_answer``) paths so that orchestration logic lives in exactly
    one place.

    Returns:
        A ``(session_id, question, prompt, retrieval_metadata)`` tuple ready to pass to the LLM.

    Raises:
        ValueError: if the inputs are invalid or no documents have been
            uploaded for the session.
        RuntimeError: if a Supabase call fails.
    """
    session_id = require_text(session_id, "Session ID")
    question = require_text(question, "Question")

    # Fast check: ensure the session actually has documents before doing vector math.
    documents = get_documents_by_session(session_id)
    if not documents:
        raise ValueError("Upload a file before asking a question.")

    # True RAG: retrieve chunks via semantic similarity rather than dumping the whole file.
    retrieval_metadata = retrieve_chunks(
        session_id=session_id, 
        query=question, 
        top_k=TOP_K_RETRIEVAL
    )

    chat_history = load_messages(session_id)
    prompt = build_prompt(DEFAULT_SYSTEM_PROMPT, retrieval_metadata.retrieved_chunks, chat_history, question)
    return session_id, question, prompt, retrieval_metadata


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def submit_question(
    session_id: str,
    question: str,
) -> dict[str, Any]:
    """Generate an answer grounded in the uploaded file,
    persist the interaction to Supabase,
    and return the message for the UI.

    The document and conversation history are retrieved server-side
    so the frontend only needs to provide session_id and question.
    """
    session_id, question, prompt, metadata = _prepare_conversation(session_id, question)
    answer = ask_llm(prompt)
    save_exchange(session_id=session_id, question=question, answer=answer)
    return {
        "question": question,
        "answer": answer,
        "metadata": metadata,
    }


def stream_answer(session_id: str, question: str) -> Generator[StreamEvent, None, None]:
    """Stream the assistant's answer token-by-token.

    Orchestrates document/history loading, prompt construction, LLM streaming,
    and — only after the stream completes in full — a single all-or-nothing
    write to Supabase.

    Persistence rules:
    - The exchange is saved **only** when the stream finishes without error.
    - If Azure raises an exception mid-stream, no partial write occurs.
    - If the client disconnects (``GeneratorExit``), no partial write occurs.

    Yields:
        Raw text chunks as they arrive from Azure AI Foundry.

    Raises:
        ValueError: if the inputs are invalid or no documents are uploaded.
        RuntimeError: if the LLM call or the database write fails.
    """
    session_id, question, prompt, metadata = _prepare_conversation(session_id, question)

    accumulated: list[str] = []
    stream_completed = False

    # [DBG] Track time from first yield to last yield inside stream_answer
    t_start = time.perf_counter()
    chunk_count = 0
    print(f"[DBG][stream_answer] Starting iteration over stream_llm()", flush=True)

    try:
        for chunk in stream_llm(prompt):
            now = time.perf_counter()
            chunk_count += 1
            print(
                f"[DBG][stream_answer] yielding chunk #{chunk_count} "
                f"t={(now - t_start):.3f}s len={len(chunk)} repr={chunk!r}",
                flush=True,
            )
            accumulated.append(chunk)
            yield StreamEvent(type="chunk", chunk=chunk)
        # Only set after the for-loop exits normally (all tokens received).
        stream_completed = True
        
        yield StreamEvent(type="metadata", metadata=metadata)
        
        print(
            f"[DBG][stream_answer] Stream complete. "
            f"chunks={chunk_count} total_time={(time.perf_counter() - t_start):.3f}s",
            flush=True,
        )
    except Exception:
        # Re-raise; stream_completed stays False so no partial save.
        raise
    finally:
        # GeneratorExit (client disconnect) is a BaseException, not caught
        # by `except Exception`, so stream_completed is still False — correct.
        full_answer = "".join(accumulated)
        if full_answer and stream_completed:
            save_exchange(
                session_id=session_id,
                question=question,
                answer=full_answer,
            )
