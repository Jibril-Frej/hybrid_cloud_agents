"""Query the public Chroma index for the incoming query.

Runs in the public cluster. The chunks returned by ``retrieve`` are public
document excerpts and may be returned to the orchestrator freely (see
``.claude/skills/trust-boundary/SKILL.md`` — public-to-private flow is
unrestricted).
"""

import chromadb
from chromadb.errors import NotFoundError

from common.paths import PUBLIC_DATA_DIR, PUBLIC_INDEX_DIR
from public.ingest import COLLECTION_NAME, build_index


def _get_collection() -> chromadb.Collection:
    """Return the public Chroma collection, building it from ``PUBLIC_DATA_DIR`` if missing."""
    client = chromadb.PersistentClient(path=str(PUBLIC_INDEX_DIR))
    try:
        return client.get_collection(COLLECTION_NAME)
    except NotFoundError:
        return build_index(PUBLIC_DATA_DIR, PUBLIC_INDEX_DIR)


def warm_up() -> None:
    """Ensure the public Chroma index and its embedding model are ready.

    Building the index on first use downloads Chroma's ~80MB ONNX embedding
    model, which can take longer than a typical HTTP client timeout. Calling
    this once at application startup moves that cost out of the request path.
    """
    _get_collection()


def retrieve(query: str, top_k: int = 2) -> list[str]:
    """Return the ``top_k`` public document chunks most relevant to ``query``.

    Builds the index from ``PUBLIC_DATA_DIR`` on first use if it does not
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
