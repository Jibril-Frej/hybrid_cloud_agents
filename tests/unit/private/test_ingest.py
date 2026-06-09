"""Unit tests for the private Chroma ingest pipeline."""

import uuid

import chromadb

from private.ingest import ingest


def _fresh_col():
    """Return a new, isolated EphemeralClient collection with a unique name."""
    client = chromadb.EphemeralClient()
    return client.get_or_create_collection(f"priv-{uuid.uuid4().hex}")


def test_ingest_adds_documents_to_collection(tmp_path):
    """ingest() returns the count of ingested files and persists them to the collection."""
    (tmp_path / "handbook.txt").write_text("Internal employee handbook content.")
    (tmp_path / "finance.txt").write_text("Q3 revenue figures — confidential.")

    col = _fresh_col()
    n = ingest(data_dir=str(tmp_path), _collection=col)

    assert n == 2
    assert col.count() == 2


def test_ingest_empty_directory(tmp_path):
    """ingest() returns 0 and leaves the collection empty when the directory has no files."""
    col = _fresh_col()
    n = ingest(data_dir=str(tmp_path), _collection=col)

    assert n == 0


def test_ingest_uses_filename_stem_as_id(tmp_path):
    """ingest() uses the file's stem (without extension) as the Chroma document ID."""
    (tmp_path / "employee_handbook.txt").write_text("Policy document text.")

    col = _fresh_col()
    ingest(data_dir=str(tmp_path), _collection=col)

    result = col.get(ids=["employee_handbook"])
    assert result["documents"] == ["Policy document text."]
