"""Shared filesystem paths for the private Chroma index.

Both ``private.ingest`` (seeding) and ``orchestrator.retriever`` (querying)
need to agree on where the private documents and the persisted index live.
"""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PRIVATE_DATA_DIR = Path(os.environ.get("PRIVATE_DATA_DIR", REPO_ROOT / "data" / "private"))
PRIVATE_INDEX_DIR = Path(
    os.environ.get("PRIVATE_INDEX_DIR", REPO_ROOT / "data" / "chroma" / "private")
)
