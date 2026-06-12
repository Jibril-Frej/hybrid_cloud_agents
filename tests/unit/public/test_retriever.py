"""Unit tests for public.retriever."""

from unittest.mock import patch

from public import retriever


class TestWarmUp:
    """Test the warm_up function."""

    def test_warm_up_builds_index_when_missing(self, tmp_path, monkeypatch):
        """warm_up() builds the index from PUBLIC_DATA_DIR if it doesn't exist."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "doc.md").write_text("Test document content")
        index_dir = tmp_path / "index"

        monkeypatch.setattr(retriever, "PUBLIC_DATA_DIR", data_dir)
        monkeypatch.setattr(retriever, "PUBLIC_INDEX_DIR", index_dir)

        # Index should not exist yet
        assert not index_dir.exists()

        retriever.warm_up()

        # Index should be created
        assert index_dir.exists()

    def test_warm_up_is_noop_when_index_exists(self, tmp_path, monkeypatch):
        """warm_up() does not rebuild the index if it already exists."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "doc.md").write_text("Original document")
        index_dir = tmp_path / "index"

        monkeypatch.setattr(retriever, "PUBLIC_DATA_DIR", data_dir)
        monkeypatch.setattr(retriever, "PUBLIC_INDEX_DIR", index_dir)

        retriever.warm_up()

        with patch.object(retriever, "build_index") as mock_build_index:
            retriever.warm_up()

        mock_build_index.assert_not_called()

    def test_warm_up_with_empty_data_directory(self, tmp_path, monkeypatch):
        """warm_up() handles empty PUBLIC_DATA_DIR gracefully."""
        data_dir = tmp_path / "empty_data"
        data_dir.mkdir()
        index_dir = tmp_path / "index"

        monkeypatch.setattr(retriever, "PUBLIC_DATA_DIR", data_dir)
        monkeypatch.setattr(retriever, "PUBLIC_INDEX_DIR", index_dir)

        # Should not raise an error
        retriever.warm_up()
        # Index should be created even if empty
        assert index_dir.exists()


class TestGetCollection:
    """Test the _get_collection helper function."""

    def test_get_collection_returns_existing_collection(self, tmp_path, monkeypatch):
        """_get_collection() returns the existing collection without rebuilding it."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "doc.md").write_text("Test document")
        index_dir = tmp_path / "index"

        monkeypatch.setattr(retriever, "PUBLIC_DATA_DIR", data_dir)
        monkeypatch.setattr(retriever, "PUBLIC_INDEX_DIR", index_dir)

        # First call builds it
        retriever._get_collection()

        with patch.object(retriever, "build_index") as mock_build_index:
            retriever._get_collection()

        mock_build_index.assert_not_called()


class TestRetrieve:
    """Test the retrieve function."""

    def test_retrieve_from_empty_directory_returns_empty_list(self, tmp_path, monkeypatch):
        """Retrieve returns [] when there are no documents."""
        data_dir = tmp_path / "empty_data"
        data_dir.mkdir()
        index_dir = tmp_path / "empty_index"

        monkeypatch.setattr(retriever, "PUBLIC_DATA_DIR", data_dir)
        monkeypatch.setattr(retriever, "PUBLIC_INDEX_DIR", index_dir)

        result = retriever.retrieve("test query")

        assert result == []

    def test_retrieve_lazily_builds_index_on_first_call(self, tmp_path, monkeypatch):
        """Retrieve builds the index if it doesn't exist yet."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "doc.md").write_text("Test document content")
        index_dir = tmp_path / "index"

        monkeypatch.setattr(retriever, "PUBLIC_DATA_DIR", data_dir)
        monkeypatch.setattr(retriever, "PUBLIC_INDEX_DIR", index_dir)

        # Index should not exist yet
        assert not index_dir.exists()

        result = retriever.retrieve("test query")

        # Index should be created
        assert index_dir.exists()
        assert len(result) > 0

    def test_retrieve_returns_top_k_results(self, tmp_path, monkeypatch):
        """Retrieve respects the top_k parameter."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "doc1.md").write_text("Document one")
        (data_dir / "doc2.md").write_text("Document two")
        (data_dir / "doc3.md").write_text("Document three")
        index_dir = tmp_path / "index"

        monkeypatch.setattr(retriever, "PUBLIC_DATA_DIR", data_dir)
        monkeypatch.setattr(retriever, "PUBLIC_INDEX_DIR", index_dir)

        result = retriever.retrieve("document", top_k=2)

        assert len(result) <= 2

    def test_retrieve_default_top_k_is_two(self, tmp_path, monkeypatch):
        """Retrieve defaults to top_k=2."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "doc1.md").write_text("Document one about test")
        (data_dir / "doc2.md").write_text("Document two about test")
        (data_dir / "doc3.md").write_text("Document three about test")
        index_dir = tmp_path / "index"

        monkeypatch.setattr(retriever, "PUBLIC_DATA_DIR", data_dir)
        monkeypatch.setattr(retriever, "PUBLIC_INDEX_DIR", index_dir)

        result = retriever.retrieve("test")

        # Default is top_k=2, so should get at most 2
        assert len(result) <= 2

    def test_retrieve_with_custom_top_k(self, tmp_path, monkeypatch):
        """Retrieve respects custom top_k values."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "doc1.md").write_text("Document one")
        (data_dir / "doc2.md").write_text("Document two")
        (data_dir / "doc3.md").write_text("Document three")
        index_dir = tmp_path / "index"

        monkeypatch.setattr(retriever, "PUBLIC_DATA_DIR", data_dir)
        monkeypatch.setattr(retriever, "PUBLIC_INDEX_DIR", index_dir)

        result1 = retriever.retrieve("document", top_k=1)
        result2 = retriever.retrieve("document", top_k=3)

        assert len(result1) <= 1
        assert len(result2) <= 3

    def test_retrieve_reuses_existing_index(self, tmp_path, monkeypatch):
        """Retrieve uses an existing index without rebuilding."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "doc.md").write_text("Test document")
        index_dir = tmp_path / "index"

        monkeypatch.setattr(retriever, "PUBLIC_DATA_DIR", data_dir)
        monkeypatch.setattr(retriever, "PUBLIC_INDEX_DIR", index_dir)

        # First call builds the index
        result1 = retriever.retrieve("test")
        assert len(result1) > 0

        # Remove the data dir to ensure we're not rebuilding
        import shutil

        shutil.rmtree(data_dir)

        # Second call should still work (index already exists)
        result2 = retriever.retrieve("test")
        assert len(result2) > 0

    def test_retrieve_returns_list_of_strings(self, tmp_path, monkeypatch):
        """Retrieve returns a list of document text strings."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "doc.md").write_text("Test document content")
        index_dir = tmp_path / "index"

        monkeypatch.setattr(retriever, "PUBLIC_DATA_DIR", data_dir)
        monkeypatch.setattr(retriever, "PUBLIC_INDEX_DIR", index_dir)

        result = retriever.retrieve("test")

        assert isinstance(result, list)
        if result:  # Only check if we got results
            assert all(isinstance(item, str) for item in result)

    def test_retrieve_handles_top_k_larger_than_collection(self, tmp_path, monkeypatch):
        """Retrieve handles top_k larger than the collection size."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "doc.md").write_text("Only document")
        index_dir = tmp_path / "index"

        monkeypatch.setattr(retriever, "PUBLIC_DATA_DIR", data_dir)
        monkeypatch.setattr(retriever, "PUBLIC_INDEX_DIR", index_dir)

        result = retriever.retrieve("test", top_k=100)

        # Should return only 1 doc, not an error
        assert len(result) <= 1
