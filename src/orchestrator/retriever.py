"""Query the private Chroma index for locally retrieved context.

Runs entirely inside the private cluster. The chunks returned by
``retrieve`` are for local use only and must never be sent to the public
worker (see ``.claude/skills/trust-boundary/SKILL.md``).
"""

import chromadb
from chromadb.errors import NotFoundError

from common.paths import PRIVATE_DATA_DIR, PRIVATE_INDEX_DIR
from private.ingest import COLLECTION_NAME, build_index


def _get_collection() -> chromadb.Collection:
    """Return the private Chroma collection, building it from ``PRIVATE_DATA_DIR`` if missing."""
    client = chromadb.PersistentClient(path=str(PRIVATE_INDEX_DIR))
    try:
        return client.get_collection(COLLECTION_NAME)
    except NotFoundError:
        return build_index(PRIVATE_DATA_DIR, PRIVATE_INDEX_DIR)


def warm_up() -> None:
    """Ensure the private Chroma index and its embedding model are ready.

    Building the index on first use downloads Chroma's ~80MB ONNX embedding
    model, which can take longer than a typical HTTP client timeout. Calling
    this once at application startup moves that cost out of the request path.
    """
    _get_collection()


def retrieve(query: str, top_k: int = 2) -> list[str]:
    """Return the ``top_k`` private document chunks most relevant to ``query``.

    Builds the index from ``PRIVATE_DATA_DIR`` on first use if it does not
    exist yet.

    Args:
        query: The raw user query.
        top_k: Maximum number of chunks to return.

    Returns:
        A list of document texts, most relevant first.
    """
    collection = _get_collection()

    count = collection.count()
    if count == 0:
        return []

    results = collection.query(query_texts=[query], n_results=min(top_k, count))
    return results["documents"][0]
