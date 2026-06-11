"""Unit tests for public.main."""

from fastapi.testclient import TestClient

from public.main import app


class TestPublicWorker:
    """Test the public worker FastAPI app."""

    def test_query_endpoint_returns_canned_response(self):
        """POST /query returns canned response acknowledging the query."""
        client = TestClient(app)
        response = client.post("/query", json={"query": "what is 2+2?"})
        assert response.status_code == 200
        data = response.json()
        assert data == {"answer": "public worker received: what is 2+2?"}

    def test_query_endpoint_with_empty_string(self):
        """POST /query handles empty query string."""
        client = TestClient(app)
        response = client.post("/query", json={"query": ""})
        assert response.status_code == 200
        data = response.json()
        assert data == {"answer": "public worker received: "}

    def test_query_endpoint_with_special_characters(self):
        """POST /query handles special characters in query."""
        client = TestClient(app)
        query_text = "what's the 'price' of \"eggs\"?"
        response = client.post("/query", json={"query": query_text})
        assert response.status_code == 200
        data = response.json()
        assert data == {"answer": f"public worker received: {query_text}"}

    def test_query_endpoint_with_long_query(self):
        """POST /query handles long query strings."""
        client = TestClient(app)
        long_query = "a" * 1000
        response = client.post("/query", json={"query": long_query})
        assert response.status_code == 200
        data = response.json()
        assert data == {"answer": f"public worker received: {long_query}"}

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
