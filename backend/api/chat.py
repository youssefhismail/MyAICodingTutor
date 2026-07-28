"""Chat API routes."""

from fastapi import APIRouter, HTTPException

from backend.models.requests import ChatRequest
from backend.models.responses import ChatResponse
from backend.services.chat_service import submit_question


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def create_chat_response(payload: ChatRequest) -> ChatResponse:
    """Generate and persist a grounded answer for the supplied question."""
    try:
        message = submit_question(
            session_id=payload.session_id,
            filename=payload.filename,
            system_prompt=payload.system_prompt,
            context=payload.context,
            chat_history=payload.chat_history,
            question=payload.question,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    return ChatResponse(**message)
