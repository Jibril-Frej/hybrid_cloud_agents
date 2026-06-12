"""Integration tests for the one-way membrane boundary invariant.

Asserts that the orchestrator (private) never sends private data to the
public worker (public) — only the raw query string is allowed to cross the
cluster boundary. See `.claude/skills/trust-boundary/SKILL.md`.
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from orchestrator.main import app as orchestrator_app


class FakePublicWorker:
    """Fake public worker that records all inbound requests.

    Used to assert that only the raw query crosses the boundary.
    """

    def __init__(self):
        """Initialize the fake public worker with empty request log."""
        self.requests = []

    def handle_query(self, request_data: dict[str, Any]) -> dict[str, Any]:
        """Record the inbound request and return a fake response.

        Args:
            request_data: The JSON body of the POST request from orchestrator.

        Returns:
            A dict with 'answer' key for compatibility with PublicWorkerResponse.
        """
        self.requests.append(request_data)
        return {"answer": "fake response"}


@pytest.fixture
def fake_worker():
    """Patch httpx.post so it routes to a FakePublicWorker and returns it."""
    worker = FakePublicWorker()

    def mock_post(url: str, json: dict[str, Any], **kwargs: Any) -> MagicMock:
        response = MagicMock()
        response.json.return_value = worker.handle_query(json)
        return response

    with patch("orchestrator.main.httpx.post", side_effect=mock_post):
        yield worker


class TestOnewayMembrane:
    """Test the one-way membrane boundary invariant.

    The orchestrator must only send the raw query string to the public worker,
    never any private data like documents, embeddings, or answers.
    """

    @pytest.mark.parametrize(
        "query_text",
        [
            "what is 2+2?",
            "",
            "query with 'quotes' and \"double quotes\" and newlines\n",
        ],
    )
    def test_orchestrator_sends_only_query_to_public_worker(self, fake_worker, query_text):
        """Orchestrator /query sends exactly {"query": "<string>"} to public worker.

        This is the core boundary contract: only the raw query crosses from
        private to public. Nothing else.
        """
        client = TestClient(orchestrator_app)
        client.post("/query", json={"query": query_text})

        assert len(fake_worker.requests) == 1
        assert fake_worker.requests[0] == {"query": query_text}

    def test_private_data_marker_never_crosses_boundary(self, fake_worker, tmp_path, monkeypatch):
        """Private data (e.g., project codename) never appears in requests to the public worker.

        This test verifies that even when a query retrieves sensitive private
        documents, the orchestrator never sends them to the public worker.
        """
        # Set up a temp private data directory with the confidential marker
        data_dir = tmp_path / "private_data"
        data_dir.mkdir()
        (data_dir / "project-codenames.md").write_text(
            "This document lists internal-only codenames for active initiatives. "
            "It must never leave the private cluster.\n\n"
            "The hybrid cloud agents initiative is internally referred to by the "
            "codename PRJ-NEBULA-7F2A."
        )

        # Set up a temp index directory
        index_dir = tmp_path / "chroma_index"

        client = TestClient(orchestrator_app)

        # Patch retriever to use our temp directories
        with patch("orchestrator.retriever.PRIVATE_DATA_DIR", data_dir):
            with patch("orchestrator.retriever.PRIVATE_INDEX_DIR", index_dir):
                # Query designed to retrieve the project-codenames document
                client.post("/query", json={"query": "what is the internal project codename?"})

        # The confidential marker string must never appear in any request to the public worker
        assert len(fake_worker.requests) == 1
        request_data = str(fake_worker.requests[0])
        # The specific marker PRJ-NEBULA-7F2A must never cross the boundary
        assert "PRJ-NEBULA-7F2A" not in request_data
        # But the request should still be exactly {"query": "..."}
        assert fake_worker.requests[0]["query"] == "what is the internal project codename?"
