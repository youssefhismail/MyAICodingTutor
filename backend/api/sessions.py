"""Session API routes."""

from fastapi import APIRouter, HTTPException

from backend.database.supabase import delete_messages, load_messages
from backend.models.responses import ConversationSummary, SessionMessage
from backend.services.chat_service import load_conversation_summaries


router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[ConversationSummary])
def get_sessions() -> list[ConversationSummary]:
    """Return one summary per conversation session."""
    try:
        summaries = load_conversation_summaries()
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    return [ConversationSummary(**summary) for summary in summaries]


@router.get("/{session_id}", response_model=list[SessionMessage])
def get_session_messages(session_id: str) -> list[SessionMessage]:
    """Return every stored message for one session.

    The internal storage uses role/content rows.  This endpoint pairs
    consecutive user + assistant messages back into question/answer
    objects so the existing frontend API contract is preserved.
    """
    try:
        messages = load_messages(session_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    pairs: list[SessionMessage] = []
    i = 0
    while i < len(messages) - 1:
        user_msg = messages[i]
        assistant_msg = messages[i + 1]

        if user_msg.get("role") == "user" and assistant_msg.get("role") == "assistant":
            pairs.append(
                SessionMessage(
                    session_id=session_id,
                    filename="",
                    question=user_msg.get("content", ""),
                    answer=assistant_msg.get("content", ""),
                )
            )
            i += 2
        else:
            i += 1

    return pairs


@router.delete("/{session_id}")
def delete_session(session_id: str) -> dict[str, str]:
    """Delete all stored messages for one session."""
    try:
        delete_messages(session_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    return {"status": "deleted"}
