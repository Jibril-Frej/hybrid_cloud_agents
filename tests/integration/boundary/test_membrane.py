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

    def mock_post(url: str, json: dict[str, Any]) -> MagicMock:
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
