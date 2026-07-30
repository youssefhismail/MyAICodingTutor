"""Domain models for backend services."""

from pydantic import BaseModel, Field


class DocumentContext(BaseModel):
    """Represents an uploaded document used as context for the LLM."""

    document_id: str = Field(..., description="Unique ID of the document")
    filename: str = Field(..., description="Original filename")
    content: str = Field(..., description="Text content of the document")
