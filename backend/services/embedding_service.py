"""Embedding service — generates vector embeddings for document chunks using Azure AI Foundry."""

import logging

from openai import OpenAI

from backend.config import (
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    FOUNDRY_API_KEY,
    FOUNDRY_ENDPOINT,
)

logger = logging.getLogger(__name__)


def _get_base_url(endpoint: str) -> str:
    """Return one OpenAI v1 base URL from either supported endpoint form."""
    normalized_endpoint = endpoint.rstrip("/")
    if normalized_endpoint.endswith("/openai/v1"):
        return f"{normalized_endpoint}/"
    return f"{normalized_endpoint}/openai/v1/"


def _make_client() -> OpenAI:
    """Create a configured Azure AI Foundry OpenAI client for embeddings.

    Raises:
        RuntimeError: if any required environment variable is missing.
    """
    if not FOUNDRY_ENDPOINT or not FOUNDRY_API_KEY or not AZURE_OPENAI_EMBEDDING_DEPLOYMENT:
        raise RuntimeError(
            "Azure AI Foundry is not configured for embeddings. Set FOUNDRY_ENDPOINT, "
            "FOUNDRY_API_KEY, and AZURE_OPENAI_EMBEDDING_DEPLOYMENT."
        )
    return OpenAI(
        base_url=_get_base_url(FOUNDRY_ENDPOINT),
        api_key=FOUNDRY_API_KEY,
        default_headers={"api-key": FOUNDRY_API_KEY},
    )


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a list of text chunks in a single batch request.

    Args:
        texts: A list of text strings to embed.

    Returns:
        A list of embedding vectors (list of floats) in the same order as the input.

    Raises:
        RuntimeError: if the Azure AI Foundry API request fails.
    """
    if not texts:
        return []

    num_chunks = len(texts)
    logger.info("Beginning embedding generation for %d chunk(s)", num_chunks)

    client = _make_client()

    try:
        response = client.embeddings.create(
            model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            input=texts,
        )
        logger.info("Successfully generated embeddings for %d chunk(s)", num_chunks)
    except Exception as error:
        logger.error("Failed to generate embeddings for %d chunk(s): %s", num_chunks, error)
        raise RuntimeError(
            f"Azure AI Foundry embedding request failed for {num_chunks} chunk(s): {error}"
        ) from error

    # The API returns an array of objects which contain the embedding and index.
    # We sort by index to absolutely guarantee the output order perfectly matches
    # the input list order, even if the API decides to return them out-of-order.
    sorted_data = sorted(response.data, key=lambda item: item.index)
    
    return [item.embedding for item in sorted_data]
