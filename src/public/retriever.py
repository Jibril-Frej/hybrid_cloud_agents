"""Public-cluster Chroma retriever.

Queries the public Chroma collection using the built-in ``all-MiniLM-L6-v2``
ONNX embedding function.  The collection is initialised lazily and cached for
the lifetime of the process.
"""

import os
from functools import lru_cache

import chromadb

COLLECTION_NAME = "public_docs"
DEFAULT_CHROMA_PATH = "data/chroma/public"


@lru_cache(maxsize=1)
def _get_collection():
    """Return (and cache) the public Chroma collection.

    Uses ``PUBLIC_CHROMA_PATH`` env var to locate the persistent store, falling
    back to ``data/chroma/public``.  The collection is created if absent.
    """
    path = os.environ.get("PUBLIC_CHROMA_PATH", DEFAULT_CHROMA_PATH)
    client = chromadb.PersistentClient(path=path)
    # Uses all-MiniLM-L6-v2 via Chroma's built-in ONNX embedding function.
    return client.get_or_create_collection(COLLECTION_NAME)


def retrieve(
    query: str, n_results: int = 3, _collection: chromadb.Collection | None = None
) -> list[str]:
    """Return the top-``n_results`` public document chunks relevant to *query*.

    Args:
        query: The natural-language query to search for.
        n_results: Maximum number of chunks to return.  Capped automatically
            to the size of the collection so Chroma never raises an error on
            small indexes.
        _collection: Optional Chroma collection to use instead of the cached
            persistent one.  Intended for testing only.

    Returns:
        A list of document strings ordered by relevance (most relevant first).
        Returns an empty list when the collection contains no documents.
    """
    col = _collection or _get_collection()
    count = col.count()
    if count == 0:
        return []
    results = col.query(query_texts=[query], n_results=min(n_results, count))
    return results.get("documents", [[]])[0]
