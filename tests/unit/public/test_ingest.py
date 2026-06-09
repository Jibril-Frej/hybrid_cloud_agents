"""Unit tests for the public Chroma ingest pipeline."""

import uuid

import chromadb

from public.ingest import ingest


def _fresh_col():
    """Return a new, isolated EphemeralClient collection with a unique name."""
    client = chromadb.EphemeralClient()
    return client.get_or_create_collection(f"pub-{uuid.uuid4().hex}")


def test_ingest_adds_documents_to_collection(tmp_path):
    """ingest() returns the count of ingested files and persists them to the collection."""
    (tmp_path / "doc1.txt").write_text("Hello public document one.")
    (tmp_path / "doc2.txt").write_text("Hello public document two.")

    col = _fresh_col()
    n = ingest(data_dir=str(tmp_path), _collection=col)

    assert n == 2
    assert col.count() == 2


def test_ingest_empty_directory_returns_zero(tmp_path):
    """ingest() returns 0 and leaves the collection empty when the directory has no files."""
    col = _fresh_col()
    n = ingest(data_dir=str(tmp_path), _collection=col)

    assert n == 0
    assert col.count() == 0


def test_ingest_uses_filename_stem_as_id(tmp_path):
    """ingest() uses the file's stem (without extension) as the Chroma document ID."""
    (tmp_path / "ai_trends.txt").write_text("AI trends document.")

    col = _fresh_col()
    ingest(data_dir=str(tmp_path), _collection=col)

    result = col.get(ids=["ai_trends"])
    assert result["documents"] == ["AI trends document."]
