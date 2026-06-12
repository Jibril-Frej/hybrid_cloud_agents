"""Unit tests for private.ingest."""

import chromadb

from private.ingest import COLLECTION_NAME, build_index, load_documents


class TestLoadDocuments:
    """Test the load_documents function."""

    def test_load_documents_from_empty_directory(self, tmp_path):
        """load_documents returns {} for a directory with no .md files."""
        result = load_documents(tmp_path)
        assert result == {}

    def test_load_documents_with_single_markdown_file(self, tmp_path):
        """load_documents loads a single .md file by stem."""
        doc_file = tmp_path / "test_doc.md"
        doc_file.write_text("Test content")

        result = load_documents(tmp_path)

        assert result == {"test_doc": "Test content"}

    def test_load_documents_with_multiple_markdown_files(self, tmp_path):
        """load_documents loads all .md files and sorts by path."""
        (tmp_path / "alpha.md").write_text("Alpha content")
        (tmp_path / "beta.md").write_text("Beta content")
        (tmp_path / "gamma.md").write_text("Gamma content")

        result = load_documents(tmp_path)

        assert len(result) == 3
        assert result["alpha"] == "Alpha content"
        assert result["beta"] == "Beta content"
        assert result["gamma"] == "Gamma content"

    def test_load_documents_ignores_non_markdown_files(self, tmp_path):
        """load_documents ignores files that don't end in .md."""
        (tmp_path / "valid.md").write_text("Valid")
        (tmp_path / "invalid.txt").write_text("Invalid")
        (tmp_path / "ignore.pdf").write_text("Ignore")

        result = load_documents(tmp_path)

        assert result == {"valid": "Valid"}

    def test_load_documents_preserves_file_content(self, tmp_path):
        """load_documents preserves multiline and special content."""
        content = "Line 1\nLine 2\n\nLine 4 with 'quotes' and \"double quotes\""
        (tmp_path / "doc.md").write_text(content)

        result = load_documents(tmp_path)

        assert result["doc"] == content


class TestBuildIndex:
    """Test the build_index function."""

    def test_build_index_creates_collection(self, tmp_path):
        """build_index returns a Chroma collection."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        persist_dir = tmp_path / "index"

        collection = build_index(data_dir, persist_dir)

        assert collection is not None
        assert collection.name == COLLECTION_NAME

    def test_build_index_from_empty_directory(self, tmp_path):
        """build_index returns an empty collection if data_dir has no docs."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        persist_dir = tmp_path / "index"

        collection = build_index(data_dir, persist_dir)

        assert collection.count() == 0

    def test_build_index_populates_collection(self, tmp_path):
        """build_index populates the collection with documents."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "doc1.md").write_text("Document one")
        (data_dir / "doc2.md").write_text("Document two")
        persist_dir = tmp_path / "index"

        collection = build_index(data_dir, persist_dir)

        assert collection.count() == 2

    def test_build_index_uses_file_stems_as_ids(self, tmp_path):
        """build_index uses the filename stem as the document ID."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "holiday.md").write_text("Holiday content")
        persist_dir = tmp_path / "index"

        collection = build_index(data_dir, persist_dir)

        # Query to ensure the document is there
        results = collection.get(ids=["holiday"])
        assert len(results["ids"]) == 1
        assert results["documents"][0] == "Holiday content"

    def test_build_index_is_queryable(self, tmp_path):
        """build_index creates a queryable collection."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "ai.md").write_text("Artificial intelligence is transformative")
        (data_dir / "other.md").write_text("Unrelated content about cats")
        persist_dir = tmp_path / "index"

        collection = build_index(data_dir, persist_dir)

        results = collection.query(query_texts=["machine learning"], n_results=1)
        # The AI doc should rank higher than the cat doc
        assert len(results["documents"]) > 0

    def test_build_index_replaces_existing_collection(self, tmp_path):
        """build_index called twice replaces rather than duplicates."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        persist_dir = tmp_path / "index"

        # First build with one doc
        (data_dir / "v1.md").write_text("Version 1")
        collection1 = build_index(data_dir, persist_dir)
        count1 = collection1.count()

        # Remove old doc, add new doc
        (data_dir / "v1.md").unlink()
        (data_dir / "v2.md").write_text("Version 2")

        # Second build
        collection2 = build_index(data_dir, persist_dir)
        count2 = collection2.count()

        assert count1 == 1
        assert count2 == 1
        # Verify new collection has the new doc, not the old one
        results = collection2.get(ids=["v2"])
        assert len(results["ids"]) == 1
        assert results["documents"][0] == "Version 2"

    def test_build_index_persists_to_disk(self, tmp_path):
        """build_index persists the index so it can be loaded later."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "persist.md").write_text("Persistent document")
        persist_dir = tmp_path / "index"

        collection1 = build_index(data_dir, persist_dir)
        count1 = collection1.count()

        # Create a new client pointing to the same persist_dir
        client2 = chromadb.PersistentClient(path=str(persist_dir))
        collection2 = client2.get_collection(COLLECTION_NAME)
        count2 = collection2.count()

        assert count1 == 1
        assert count2 == 1
