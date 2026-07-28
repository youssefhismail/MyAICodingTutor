"""Request models for backend API endpoints."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request payload for submitting a chat question."""

    session_id: str = Field(..., description="Current conversation session ID")
    filename: str = Field(..., description="Uploaded file name")
    system_prompt: str = Field(..., description="System prompt for the assistant")
    context: str = Field(..., description="Uploaded file content")
    chat_history: list[dict[str, str]] = Field(
        default_factory=list,
        description="Messages that occurred before the current question",
    )
    question: str = Field(..., description="Current user question")
