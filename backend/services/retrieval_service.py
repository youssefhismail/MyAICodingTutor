"""Retrieval service — orchestrates vector similarity search."""

import time
import logging

from backend.models.domain import RetrievedChunk
from backend.services.embedding_service import generate_embeddings
from backend.database.supabase import search_similar_chunks

logger = logging.getLogger(__name__)


def retrieve_chunks(
    session_id: str,
    query: str,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    """
    Retrieve the most relevant document chunks for a given query.
    
    Generates an embedding for the user's question, then searches the 
    database for the closest chunks within the current session.
    
    Args:
        session_id: The active session identifier.
        query: The user's question or search text.
        top_k: Maximum number of chunks to retrieve.

    Returns:
        A list of RetrievedChunk objects ordered by ascending distance (closest first).
        Returns an empty list if the session has no documents or no chunks match.

    Raises:
        RuntimeError: if embedding generation or database retrieval fails.
    """
    if not query.strip() or not session_id:
        return []

    t_start = time.perf_counter()
    logger.info("Starting retrieval for session_id=%s, top_k=%d, query='%s'", session_id, top_k, query)

    # 1. Generate query embedding
    # Note: If embedding generation fails, embedding_service raises a RuntimeError,
    # which correctly propagates upward so the caller knows it was an infra failure.
    embeddings = generate_embeddings([query])
    if not embeddings:
        return []
    query_embedding = embeddings[0]

    # 2. Vector search in database
    # Note: If the RPC fails, supabase.py raises a RuntimeError.
    results = search_similar_chunks(session_id, query_embedding, top_k)

    duration = time.perf_counter() - t_start

    if results:
        # Log metadata for debugging/tuning
        summary = ", ".join(f"'{r.filename}'(d={r.distance:.3f})" for r in results)
        logger.info(
            "Retrieved %d chunk(s) in %.3fs. Results: %s",
            len(results),
            duration,
            summary,
        )
    else:
        logger.info(
            "Retrieval completed in %.3fs. No relevant chunks found.",
            duration
        )

    return results
