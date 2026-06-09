"""Public-cluster corpus ingestion.

Reads ``*.txt`` files from the public data directory and upserts them into the
public Chroma collection.  Run once before serving (``make seed``) or whenever
the public corpus changes.
"""

import os
from pathlib import Path

import chromadb

COLLECTION_NAME = "public_docs"
DEFAULT_DATA_DIR = "data/public"
DEFAULT_CHROMA_PATH = "data/chroma/public"


def ingest(
    data_dir: str = DEFAULT_DATA_DIR,
    chroma_path: str = DEFAULT_CHROMA_PATH,
    _collection: chromadb.Collection | None = None,
) -> int:
    """Ingest all ``*.txt`` files in *data_dir* into the public Chroma collection.

    Files are upserted (inserted or updated) using their filename stem as the
    document ID, so re-running is safe and idempotent.

    Args:
        data_dir: Path to the directory containing public ``*.txt`` documents.
        chroma_path: Path for the persistent Chroma store.  Ignored when
            *_collection* is provided.
        _collection: Optional pre-built Chroma collection.  Intended for
            testing only — skips ``PersistentClient`` creation.

    Returns:
        Number of documents upserted.
    """
    if _collection is None:
        client = chromadb.PersistentClient(path=chroma_path)
        col = client.get_or_create_collection(COLLECTION_NAME)
    else:
        col = _collection

    data_path = Path(data_dir)
    docs, ids = [], []
    for file in sorted(data_path.glob("*.txt")):
        docs.append(file.read_text(encoding="utf-8").strip())
        ids.append(file.stem)

    if docs:
        col.upsert(documents=docs, ids=ids)
    return len(docs)


def main() -> None:
    """Entry point for seeding the public Chroma index from the command line."""
    num_docs = ingest(
        data_dir=os.environ.get("PUBLIC_DATA_DIR", DEFAULT_DATA_DIR),
        chroma_path=os.environ.get("PUBLIC_CHROMA_PATH", DEFAULT_CHROMA_PATH),
    )
    print(f"Ingested {num_docs} public documents.")


if __name__ == "__main__":
    main()
