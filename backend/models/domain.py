"""Domain models for backend services."""

from typing import Literal
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


class RetrievedChunk(BaseModel):
    """Represents a chunk retrieved from the database, wrapped with retrieval metadata."""

    chunk: DocumentChunk = Field(..., description="The original document chunk")
    document_id: str = Field(..., description="The ID of the document this chunk belongs to")
    filename: str = Field(..., description="The name of the file this chunk belongs to")
    distance: float = Field(..., description="Cosine distance from the query embedding")


class RetrievalStats(BaseModel):
    """Lightweight retrieval statistics."""

    retrieved: int
    after_threshold: int
    duplicates_removed: int
    top_k: int


class RetrievalMetadata(BaseModel):
    """Encapsulates retrieval results and statistics."""

    retrieved_chunks: list[RetrievedChunk] = Field(..., description="The final chunks used for the prompt")
    stats: RetrievalStats = Field(..., description="Retrieval statistics")


class StreamEvent(BaseModel):
    """Represents a single typed event in the streaming pipeline."""

    type: Literal["chunk", "metadata", "done", "error"]
    
    chunk: str | None = None
    metadata: RetrievalMetadata | None = None
    message: str | None = None
