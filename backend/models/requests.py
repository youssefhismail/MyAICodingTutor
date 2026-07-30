"""Request models for backend API endpoints."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request payload for submitting a chat question."""

    session_id: str = Field(..., description="Current conversation session ID")
    question: str = Field(..., description="Current user question")
