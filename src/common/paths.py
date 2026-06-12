"""Shared filesystem paths for the private and public Chroma indexes.

``private.ingest`` and ``orchestrator.retriever`` need to agree on where the
private documents and the persisted private index live; ``public.ingest`` and
``public.retriever`` need the same agreement for the public side.
"""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PRIVATE_DATA_DIR = Path(os.environ.get("PRIVATE_DATA_DIR", REPO_ROOT / "data" / "private"))
PRIVATE_INDEX_DIR = Path(
    os.environ.get("PRIVATE_INDEX_DIR", REPO_ROOT / "data" / "chroma" / "private")
)
PUBLIC_DATA_DIR = Path(os.environ.get("PUBLIC_DATA_DIR", REPO_ROOT / "data" / "public"))
PUBLIC_INDEX_DIR = Path(
    os.environ.get("PUBLIC_INDEX_DIR", REPO_ROOT / "data" / "chroma" / "public")
)
