"""Unit tests for public.main."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from public.main import app


class TestLifespan:
    """Test the FastAPI lifespan hook."""

    def test_lifespan_calls_warm_up_on_startup(self):
        """The app's lifespan hook calls warm_up() at startup."""
        with patch("public.main.warm_up") as mock_warm_up:
            # TestClient as context manager triggers lifespan startup
            with TestClient(app):
                pass
            mock_warm_up.assert_called_once()


class TestPublicWorker:
    """Test the public worker FastAPI app."""

    def test_query_endpoint_returns_retrieved_chunks(self):
        """POST /query returns chunks retrieved from the public index."""
        client = TestClient(app)

        with patch("public.main.retrieve", return_value=["chunk1", "chunk2"]):
            response = client.post("/query", json={"query": "test query"})

        assert response.status_code == 200
        data = response.json()
        assert data == {"answer": "chunk1\nchunk2"}

    def test_query_endpoint_calls_retrieve_with_query(self):
        """POST /query calls retrieve() with the raw query string."""
        client = TestClient(app)

        with patch("public.main.retrieve", return_value=[]) as mock_retrieve:
            client.post("/query", json={"query": "what is 2+2?"})

            mock_retrieve.assert_called_once_with("what is 2+2?")

    def test_query_endpoint_with_empty_query(self):
        """POST /query handles empty query strings."""
        client = TestClient(app)

        with patch("public.main.retrieve", return_value=[]):
            response = client.post("/query", json={"query": ""})

        assert response.status_code == 200
        data = response.json()
        assert data == {"answer": ""}

    def test_query_endpoint_with_single_chunk(self):
        """POST /query returns a single chunk without extra newlines."""
        client = TestClient(app)

        with patch("public.main.retrieve", return_value=["single chunk"]):
            response = client.post("/query", json={"query": "test"})

        assert response.status_code == 200
        data = response.json()
        assert data == {"answer": "single chunk"}

    def test_query_endpoint_with_no_chunks(self):
        """POST /query returns empty answer when no chunks are retrieved."""
        client = TestClient(app)

        with patch("public.main.retrieve", return_value=[]):
            response = client.post("/query", json={"query": "no match"})

        assert response.status_code == 200
        data = response.json()
        assert data == {"answer": ""}

    def test_query_endpoint_with_special_characters_in_chunks(self):
        """POST /query preserves special characters in retrieved chunks."""
        client = TestClient(app)
        chunk1 = "First chunk with 'quotes' and \"double quotes\""
        chunk2 = "Second chunk\nwith newlines"

        with patch("public.main.retrieve", return_value=[chunk1, chunk2]):
            response = client.post("/query", json={"query": "test"})

        assert response.status_code == 200
        data = response.json()
        assert data == {"answer": f"{chunk1}\n{chunk2}"}

    def test_query_endpoint_missing_query_field(self):
        """POST /query returns 422 if query field is missing."""
        client = TestClient(app)
        response = client.post("/query", json={})
        assert response.status_code == 422

    def test_query_endpoint_invalid_json(self):
        """POST /query returns 422 if request body is invalid."""
        client = TestClient(app)
        response = client.post("/query", content="not json")
        assert response.status_code == 422

    def test_query_endpoint_with_real_data(self, tmp_path, monkeypatch):
        """POST /query retrieves real chunks from the public index when data exists."""
        # Set up a temp public data directory with known documents
        data_dir = tmp_path / "public_data"
        data_dir.mkdir()
        (data_dir / "product-overview.md").write_text("Our product is a hybrid cloud platform")
        (data_dir / "support-hours.md").write_text("Support is available 24/7")

        # Set up a temp index directory
        index_dir = tmp_path / "public_index"

        client = TestClient(app)

        # Monkeypatch the retriever to use our temp directories
        with patch("public.retriever.PUBLIC_DATA_DIR", data_dir):
            with patch("public.retriever.PUBLIC_INDEX_DIR", index_dir):
                response = client.post("/query", json={"query": "product and support information"})

        assert response.status_code == 200
        data = response.json()
        # Should retrieve something from our documents
        assert "answer" in data
        # The answer should be non-empty since we have matching documents
        assert len(data["answer"]) > 0
