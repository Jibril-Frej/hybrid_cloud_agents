import os
from pathlib import Path

import chromadb

COLLECTION_NAME = "public_docs"
DEFAULT_DATA_DIR = "data/public"
DEFAULT_CHROMA_PATH = "data/chroma/public"


def ingest(
    data_dir: str = DEFAULT_DATA_DIR,
    chroma_path: str = DEFAULT_CHROMA_PATH,
    _collection=None,
) -> int:
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


if __name__ == "__main__":
    n = ingest(
        data_dir=os.environ.get("PUBLIC_DATA_DIR", DEFAULT_DATA_DIR),
        chroma_path=os.environ.get("PUBLIC_CHROMA_PATH", DEFAULT_CHROMA_PATH),
    )
    print(f"Ingested {n} public documents.")
