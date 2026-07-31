"""Chunk service — splits documents into smaller pieces for RAG."""

from backend.config import RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP
from backend.models.domain import DocumentChunk


def chunk_document(
    text: str,
    *,
    chunk_size: int = RAG_CHUNK_SIZE,
    overlap: int = RAG_CHUNK_OVERLAP,
) -> list[DocumentChunk]:
    """
    Split text into chunks with bounded size and overlap.

    A hierarchical text splitter that prefers paragraph boundaries (\\n\\n),
    then line boundaries (\\n), then word boundaries ( ), and finally
    character boundaries.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and < chunk_size")

    if not text:
        return []

    chunks: list[DocumentChunk] = []
    text_len = len(text)
    start = 0
    sequence_number = 0


    while start < text_len:
        # If the remaining text fits in the chunk, take it all
        if text_len - start <= chunk_size:
            end = text_len
            content = text[start:end]
            if content.strip():
                chunks.append(
                    DocumentChunk(
                        sequence_number=sequence_number,
                        start_offset=start,
                        end_offset=end,
                        content=content,
                    )
                )
            break

        # Find the best boundary within the window
        window = text[start : start + chunk_size]
        
        split_point = -1
        for sep in ["\n\n", "\n", " "]:
            idx = window.rfind(sep)
            if idx > 0:
                proposed_split = idx + len(sep)
                if proposed_split > split_point:
                    split_point = proposed_split

        # Defensive guard: if no separator was found, or if the best separator
        # is too early (<= overlap), fall back to a full character split.
        # This prevents tiny chunks and pathological one-character advancement.
        if split_point <= overlap:
            split_point = chunk_size

        end = start + split_point
        content = text[start:end]

        if content.strip():
            chunks.append(
                DocumentChunk(
                    sequence_number=sequence_number,
                    start_offset=start,
                    end_offset=end,
                    content=content,
                )
            )
            sequence_number += 1

        # Advance start, ensuring we move forward by at least 1 character
        next_start = end - overlap
        if next_start <= start:
            next_start = start + 1
            
        start = next_start

    return chunks
