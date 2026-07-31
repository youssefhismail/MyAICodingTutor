"""Domain models for backend services."""

from pydantic import BaseModel, Field


class DocumentContext(BaseModel):
    """Represents an uploaded document used as context for the LLM."""

    document_id: str = Field(..., description="Unique ID of the document")
    filename: str = Field(..., description="Original filename")
    content: str = Field(..., description="Text content of the document")


class DocumentChunk(BaseModel):
    """Represents a discrete chunk of text from a document."""

    sequence_number: int = Field(..., description="Order of the chunk within the document")
    start_offset: int = Field(..., description="Starting character index in the original text")
    end_offset: int = Field(..., description="Ending character index in the original text")
    content: str = Field(..., description="Text content of the chunk")
