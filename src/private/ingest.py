"""Seed the private Chroma vector store from ``data/private/``.

Runs entirely inside the private cluster (see
``.claude/skills/trust-boundary/SKILL.md``). Builds a persistent Chroma
collection with one entry per Markdown document under ``data/private/``,
embedded with Chroma's default ONNX ``all-MiniLM-L6-v2`` model.
"""

from pathlib import Path

import chromadb
from chromadb.errors import NotFoundError

COLLECTION_NAME = "private_docs"


def load_documents(data_dir: Path) -> dict[str, str]:
    """Return ``{doc_id: text}`` for every Markdown file under ``data_dir``."""
    return {path.stem: path.read_text() for path in sorted(data_dir.glob("*.md"))}


def build_index(data_dir: Path, persist_dir: Path) -> chromadb.Collection:
    """Build the private Chroma collection from the documents in ``data_dir``.

    Any existing collection at ``persist_dir`` is replaced.

    Args:
        data_dir: Directory containing the private Markdown documents.
        persist_dir: Directory where the Chroma index is persisted.

    Returns:
        The freshly populated Chroma collection.
    """
    client = chromadb.PersistentClient(path=str(persist_dir))
    try:
        client.delete_collection(COLLECTION_NAME)
    except NotFoundError:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    documents = load_documents(data_dir)
    if documents:
        collection.add(ids=list(documents.keys()), documents=list(documents.values()))
    return collection


if __name__ == "__main__":
    from common.paths import PRIVATE_DATA_DIR, PRIVATE_INDEX_DIR

    collection = build_index(PRIVATE_DATA_DIR, PRIVATE_INDEX_DIR)
    print(f"Seeded {collection.count()} document(s) into {PRIVATE_INDEX_DIR}")
