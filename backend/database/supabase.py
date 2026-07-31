"""Supabase client factory and data-access helpers."""

from supabase import Client, create_client

from backend.config import SUPABASE_KEY, SUPABASE_URL
from backend.models.domain import DocumentChunk, DocumentContext


def get_supabase_client() -> Client:
    """Create a configured Supabase client."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ---------------------------------------------------------------------------
# Document helpers
# ---------------------------------------------------------------------------


def insert_document(session_id: str, filename: str, content: str) -> dict:
    """Insert a new document for the session.

    Returns the inserted row as a dict.
    """
    client = get_supabase_client()
    try:
        response = (
            client.table("documents")
            .insert(
                {
                    "session_id": session_id,
                    "filename": filename,
                    "content": content,
                }
            )
            .execute()
        )
    except Exception as error:
        raise RuntimeError(f"Supabase document insert failed: {error}") from error

    row = response.data[0] if response.data else {}
    if not row.get("id"):
        raise RuntimeError("Supabase did not return a document ID.")
    return row


def get_documents_by_session(session_id: str) -> list[DocumentContext]:
    """Return all documents associated with a session, ordered chronologically."""
    try:
        response = (
            get_supabase_client()
            .table("documents")
            .select("id, session_id, filename, content")
            .eq("session_id", session_id)
            .order("uploaded_at")
            .execute()
        )
    except Exception as error:
        raise RuntimeError(f"Supabase document lookup failed: {error}") from error

    if not response.data:
        return []

    return [
        DocumentContext(
            document_id=row["id"],
            filename=row["filename"],
            content=row["content"],
        )
        for row in response.data
    ]


def delete_document(document_id: str) -> None:
    """Delete a specific document by its ID."""
    try:
        get_supabase_client().table("documents").delete().eq("id", document_id).execute()
    except Exception as error:
        raise RuntimeError(f"Supabase document delete failed: {error}") from error


def insert_document_chunks(document_id: str, chunks: list[DocumentChunk]) -> None:
    """Insert multiple document chunks associated with a document ID."""
    if not chunks:
        return

    client = get_supabase_client()
    rows = [
        {
            "document_id": document_id,
            "sequence_number": chunk.sequence_number,
            "start_offset": chunk.start_offset,
            "end_offset": chunk.end_offset,
            "content": chunk.content,
        }
        for chunk in chunks
    ]

    try:
        client.table("document_chunks").insert(rows).execute()
    except Exception as error:
        raise RuntimeError(f"Supabase document chunks insert failed: {error}") from error


def get_chunks_by_document(document_id: str) -> list[DocumentChunk]:
    """Return all chunks for a document, ordered by sequence number."""
    try:
        response = (
            get_supabase_client()
            .table("document_chunks")
            .select("sequence_number, start_offset, end_offset, content")
            .eq("document_id", document_id)
            .order("sequence_number")
            .execute()
        )
    except Exception as error:
        raise RuntimeError(f"Supabase document chunks lookup failed: {error}") from error

    if not response.data:
        return []

    return [
        DocumentChunk(
            sequence_number=row["sequence_number"],
            start_offset=row["start_offset"],
            end_offset=row["end_offset"],
            content=row["content"],
        )
        for row in response.data
    ]


# ---------------------------------------------------------------------------
# Message helpers
# ---------------------------------------------------------------------------


def save_exchange(session_id: str, question: str, answer: str) -> None:
    """Atomically insert a user + assistant message pair via the RPC function.

    The database function acquires a session-scoped advisory lock and
    allocates consecutive sequence numbers inside a single transaction,
    so concurrent calls for the same session cannot produce duplicates.
    """
    try:
        get_supabase_client().rpc(
            "save_exchange",
            {
                "p_session_id": session_id,
                "p_user_content": question,
                "p_assistant_content": answer,
            },
        ).execute()
    except Exception as error:
        raise RuntimeError(f"Supabase save_exchange failed: {error}") from error


def load_messages(session_id: str) -> list[dict[str, str]]:
    """Load all messages for a session ordered by sequence.

    Returns a list of ``{"role": "...", "content": "..."}`` dicts.
    """
    try:
        response = (
            get_supabase_client()
            .table("messages")
            .select("role, content")
            .eq("session_id", session_id)
            .order("sequence")
            .execute()
        )
    except Exception as error:
        raise RuntimeError(f"Supabase message load failed: {error}") from error

    return response.data or []


def load_first_user_messages() -> list[dict]:
    """Load the earliest user message per session for sidebar summaries.

    Returns rows with ``session_id``, ``content``, and ``created_at``.
    Only ``role = 'user'`` messages with ``sequence = 0`` are returned
    (the first question in each session).
    """
    try:
        response = (
            get_supabase_client()
            .table("messages")
            .select("session_id, content, created_at")
            .eq("role", "user")
            .eq("sequence", 0)
            .order("created_at")
            .execute()
        )
    except Exception as error:
        raise RuntimeError(f"Supabase summary load failed: {error}") from error

    return response.data or []


def delete_messages(session_id: str) -> None:
    """Delete all messages for a session."""
    try:
        (
            get_supabase_client()
            .table("messages")
            .delete()
            .eq("session_id", session_id)
            .execute()
        )
    except Exception as error:
        raise RuntimeError(f"Supabase message delete failed: {error}") from error
