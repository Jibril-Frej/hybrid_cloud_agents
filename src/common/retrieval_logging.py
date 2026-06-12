"""Shared logging for Chroma retrieval results.

Both ``orchestrator.retriever`` and ``public.retriever`` run the same
``collection.query()`` shape and want identical INFO-level log lines for each
result (query, rank, doc id, distance, chunk text).
"""

import logging
from collections.abc import Sequence


def log_retrieval_results(
    logger: logging.Logger,
    query: str,
    ids: Sequence[str],
    distances: Sequence[float],
    documents: Sequence[str],
) -> None:
    """Log one INFO record per result with its rank, id, distance, and text."""
    for rank, (doc_id, distance, text) in enumerate(
        zip(ids, distances, documents, strict=True), start=1
    ):
        logger.info(
            "retrieve query=%r rank=%d id=%r distance=%.4f text=%r",
            query,
            rank,
            doc_id,
            distance,
            text,
        )
