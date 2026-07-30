"""Response models for backend API endpoints."""

from pydantic import BaseModel, Field


class ChatResponse(BaseModel):
    """Response payload for chat submissions."""

    question: str = Field(..., description="Submitted question")
    answer: str = Field(..., description="Generated answer")


class ConversationSummary(BaseModel):
    """Summary row for one stored conversation."""

    session_id: str
    filename: str
    first_question: str
    created_at: str


class SessionMessage(BaseModel):
    """Stored message belonging to one session."""

    session_id: str
    filename: str
    question: str
    answer: str


class UploadResponse(BaseModel):
    """Response payload for file uploads."""

    document_id: str = Field(..., description="ID of the stored document")
    filename: str = Field(..., description="Original filename")
    message: str = Field(..., description="Human-readable status message")
