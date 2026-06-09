import uuid

import chromadb

from private.ingest import ingest


def _fresh_col():
    client = chromadb.EphemeralClient()
    return client.get_or_create_collection(f"priv-{uuid.uuid4().hex}")


def test_ingest_adds_documents_to_collection(tmp_path):
    (tmp_path / "handbook.txt").write_text("Internal employee handbook content.")
    (tmp_path / "finance.txt").write_text("Q3 revenue figures — confidential.")

    col = _fresh_col()
    n = ingest(data_dir=str(tmp_path), _collection=col)

    assert n == 2
    assert col.count() == 2


def test_ingest_empty_directory(tmp_path):
    col = _fresh_col()
    n = ingest(data_dir=str(tmp_path), _collection=col)

    assert n == 0


def test_ingest_uses_filename_stem_as_id(tmp_path):
    (tmp_path / "employee_handbook.txt").write_text("Policy document text.")

    col = _fresh_col()
    ingest(data_dir=str(tmp_path), _collection=col)

    result = col.get(ids=["employee_handbook"])
    assert result["documents"] == ["Policy document text."]
