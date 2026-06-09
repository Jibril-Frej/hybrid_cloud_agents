"""Private-cluster Chroma retriever.

Queries the private Chroma collection using the built-in ``all-MiniLM-L6-v2``
ONNX embedding function.  Private chunks retrieved here **never leave this
module** — they are passed only to the local synthesizer.
"""

import os
from functools import lru_cache

import chromadb

COLLECTION_NAME = "private_docs"
DEFAULT_CHROMA_PATH = "data/chroma/private"


@lru_cache(maxsize=1)
def _get_collection():
    """Return (and cache) the private Chroma collection.

    Uses ``PRIVATE_CHROMA_PATH`` env var to locate the persistent store,
    falling back to ``data/chroma/private``.  The collection is created if
    absent.
    """
    path = os.environ.get("PRIVATE_CHROMA_PATH", DEFAULT_CHROMA_PATH)
    client = chromadb.PersistentClient(path=path)
    # Uses all-MiniLM-L6-v2 via Chroma's built-in ONNX embedding function.
    return client.get_or_create_collection(COLLECTION_NAME)


def retrieve(
    query: str, n_results: int = 3, _collection: chromadb.Collection | None = None
) -> list[str]:
    """Return the top-``n_results`` private document chunks relevant to *query*.

    The returned chunks must stay within the private cluster and must never be
    forwarded to the public worker.

    Args:
        query: The natural-language query to search for.
        n_results: Maximum number of chunks to return.  Capped to the
            collection size so Chroma never raises on small indexes.
        _collection: Optional Chroma collection to use instead of the cached
            persistent one.  Intended for testing only.

    Returns:
        A list of private document strings ordered by relevance.
        Returns an empty list when the collection contains no documents.
    """
    col = _collection or _get_collection()
    count = col.count()
    if count == 0:
        return []
    results = col.query(query_texts=[query], n_results=min(n_results, count))
    return results.get("documents", [[]])[0]
