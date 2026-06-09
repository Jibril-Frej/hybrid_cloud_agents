import os
from functools import lru_cache

import chromadb

COLLECTION_NAME = "private_docs"
DEFAULT_CHROMA_PATH = "data/chroma/private"


@lru_cache(maxsize=1)
def _get_collection():
    path = os.environ.get("PRIVATE_CHROMA_PATH", DEFAULT_CHROMA_PATH)
    client = chromadb.PersistentClient(path=path)
    # Uses all-MiniLM-L6-v2 via Chroma's built-in ONNX embedding function.
    return client.get_or_create_collection(COLLECTION_NAME)


def retrieve(query: str, n_results: int = 3, _collection=None) -> list[str]:
    col = _collection or _get_collection()
    count = col.count()
    if count == 0:
        return []
    results = col.query(query_texts=[query], n_results=min(n_results, count))
    return results.get("documents", [[]])[0]
