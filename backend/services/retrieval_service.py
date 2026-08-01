"""Retrieval service — orchestrates vector similarity search."""

import time
import logging

from backend.config import MAX_COSINE_DISTANCE
from backend.models.domain import RetrievedChunk, RetrievalMetadata, RetrievalStats
from backend.services.embedding_service import generate_embeddings
from backend.database.supabase import search_similar_chunks

logger = logging.getLogger(__name__)


def retrieve_chunks(
    session_id: str,
    query: str,
    top_k: int = 5,
) -> RetrievalMetadata:
    """
    Retrieve the most relevant document chunks for a given query.
    
    Generates an embedding for the user's question, then searches the 
    database for the closest chunks within the current session.
    
    Args:
        session_id: The active session identifier.
        query: The user's question or search text.
        top_k: Maximum number of chunks to retrieve.

    Returns:
        RetrievalMetadata encapsulating the final chunks and retrieval stats.

    Raises:
        RuntimeError: if embedding generation or database retrieval fails.
    """
    if not query.strip() or not session_id:
        return RetrievalMetadata(
            retrieved_chunks=[],
            stats=RetrievalStats(retrieved=0, after_threshold=0, duplicates_removed=0, top_k=top_k)
        )

    t_start = time.perf_counter()
    logger.info("Starting retrieval for session_id=%s, top_k=%d, query='%s'", session_id, top_k, query)

    embeddings = generate_embeddings([query])
    if not embeddings:
        return RetrievalMetadata(
            retrieved_chunks=[],
            stats=RetrievalStats(retrieved=0, after_threshold=0, duplicates_removed=0, top_k=top_k)
        )
    query_embedding = embeddings[0]

    # Fetch top_k * 2 to give buffer for deduplication
    fetch_count = top_k * 2
    raw_results = search_similar_chunks(session_id, query_embedding, fetch_count)
    num_retrieved = len(raw_results)

    # 1. Filter by threshold
    filtered_results = [r for r in raw_results if r.distance <= MAX_COSINE_DISTANCE]
    num_after_threshold = len(filtered_results)

    # 2. Deduplicate using (document_id, sequence_number)
    seen = set()
    unique_results = []
    for r in filtered_results:
        key = (r.document_id, r.chunk.sequence_number)
        if key not in seen:
            seen.add(key)
            unique_results.append(r)
    
    num_duplicates_removed = num_after_threshold - len(unique_results)

    # 3. Truncate to top_k
    final_results = unique_results[:top_k]

    duration = time.perf_counter() - t_start

    stats = RetrievalStats(
        retrieved=num_retrieved,
        after_threshold=num_after_threshold,
        duplicates_removed=num_duplicates_removed,
        top_k=top_k
    )

    metadata = RetrievalMetadata(
        retrieved_chunks=final_results,
        stats=stats
    )

    if final_results:
        summary = ", ".join(f"'{r.filename}'(d={r.distance:.3f})" for r in final_results)
        logger.info(
            "Retrieved %d chunk(s) in %.3fs. Results: %s. Stats: %s",
            len(final_results),
            duration,
            summary,
            stats.model_dump_json(),
        )
    else:
        logger.info(
            "Retrieval completed in %.3fs. No relevant chunks found. Stats: %s",
            duration,
            stats.model_dump_json()
        )

    return metadata
