"""Unit tests for orchestrator.main."""

import ssl
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

import orchestrator.main
from orchestrator.main import app


class TestOrchestratorWorker:
    """Test the orchestrator FastAPI app."""

    def test_query_endpoint_returns_public_worker_response(self):
        """POST /query forwards query to public worker and returns response."""
        client = TestClient(app)

        mock_response = MagicMock()
        mock_response.json.return_value = {"answer": "test answer"}

        with patch("orchestrator.main.httpx.post", return_value=mock_response) as mock_post:
            response = client.post("/query", json={"query": "test query"})

            assert response.status_code == 200
            data = response.json()
            assert data == {"answer": "test answer"}
            mock_post.assert_called_once()

    def test_query_endpoint_calls_public_worker_with_correct_payload(self):
        """POST /query sends only the query to public worker."""
        client = TestClient(app)

        mock_response = MagicMock()
        mock_response.json.return_value = {"answer": "response"}

        with patch("orchestrator.main.httpx.post", return_value=mock_response) as mock_post:
            client.post("/query", json={"query": "what is 2+2?"})

            # Verify the exact payload sent to the public worker
            call_args = mock_post.call_args
            assert call_args[1]["json"] == {"query": "what is 2+2?"}

    def test_query_endpoint_uses_default_public_worker_url(self):
        """POST /query uses default PUBLIC_WORKER_URL if not set."""
        client = TestClient(app)

        mock_response = MagicMock()
        mock_response.json.return_value = {"answer": "response"}

        with patch("orchestrator.main.httpx.post", return_value=mock_response) as mock_post:
            client.post("/query", json={"query": "test"})

            # Verify the default URL is used
            call_args = mock_post.call_args
            assert call_args[0][0] == "https://localhost:8001/query"

    def test_query_endpoint_handles_http_error(self):
        """POST /query raises HTTPStatusError if public worker returns error."""
        client = TestClient(app)

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 error", request=MagicMock(), response=MagicMock()
        )

        with patch("orchestrator.main.httpx.post", return_value=mock_response):
            with pytest.raises(httpx.HTTPStatusError):
                client.post("/query", json={"query": "test"})

    def test_query_endpoint_missing_query_field(self):
        """POST /query returns 422 if query field is missing."""
        client = TestClient(app)
        response = client.post("/query", json={})
        assert response.status_code == 422

    def test_query_endpoint_invalid_json(self):
        """POST /query returns 422 if request body is invalid JSON."""
        client = TestClient(app)
        response = client.post("/query", content="not json")
        assert response.status_code == 422

    def test_query_endpoint_with_empty_query(self):
        """POST /query forwards empty query strings unchanged."""
        client = TestClient(app)

        mock_response = MagicMock()
        mock_response.json.return_value = {"answer": "response"}

        with patch("orchestrator.main.httpx.post", return_value=mock_response) as mock_post:
            client.post("/query", json={"query": ""})

            call_args = mock_post.call_args
            assert call_args[1]["json"] == {"query": ""}

    def test_mtls_kwargs_empty_when_certs_not_configured(self, monkeypatch):
        """_mtls_kwargs() returns {} when cert env vars are not set."""
        monkeypatch.setattr(orchestrator.main, "PUBLIC_WORKER_CERT", None)
        monkeypatch.setattr(orchestrator.main, "PUBLIC_WORKER_KEY", None)
        monkeypatch.setattr(orchestrator.main, "PUBLIC_WORKER_CA", None)

        assert orchestrator.main._mtls_kwargs() == {}

    def test_mtls_kwargs_populated_when_certs_configured(self, monkeypatch, temp_certs_dir):
        """_mtls_kwargs() returns SSLContext as verify kwarg when env vars are set."""
        good_dir = temp_certs_dir["good"]
        monkeypatch.setattr(orchestrator.main, "PUBLIC_WORKER_CERT", str(good_dir / "client.crt"))
        monkeypatch.setattr(orchestrator.main, "PUBLIC_WORKER_KEY", str(good_dir / "client.key"))
        monkeypatch.setattr(orchestrator.main, "PUBLIC_WORKER_CA", str(good_dir / "ca.crt"))

        result = orchestrator.main._mtls_kwargs()

        assert result.keys() == {"verify"}
        assert isinstance(result["verify"], ssl.SSLContext)

    def test_query_endpoint_passes_mtls_kwargs_to_httpx(self, monkeypatch, temp_certs_dir):
        """POST /query passes SSLContext as verify kwarg to httpx.post when certs are configured."""
        good_dir = temp_certs_dir["good"]
        monkeypatch.setattr(orchestrator.main, "PUBLIC_WORKER_CERT", str(good_dir / "client.crt"))
        monkeypatch.setattr(orchestrator.main, "PUBLIC_WORKER_KEY", str(good_dir / "client.key"))
        monkeypatch.setattr(orchestrator.main, "PUBLIC_WORKER_CA", str(good_dir / "ca.crt"))

        client = TestClient(app)

        mock_response = MagicMock()
        mock_response.json.return_value = {"answer": "response"}

        with patch("orchestrator.main.httpx.post", return_value=mock_response) as mock_post:
            client.post("/query", json={"query": "test"})

            # Verify mTLS kwargs were passed (cert= is dropped; verify= is SSLContext)
            call_args = mock_post.call_args
            assert "cert" not in call_args[1]
            assert isinstance(call_args[1]["verify"], ssl.SSLContext)
