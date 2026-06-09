"""
Trust-boundary tests.

Invariant: the ONLY thing the orchestrator may send to the public worker is the
raw query string.  Private documents, chunks, or any derived private content
must never appear in the outbound HTTP payload.
"""

from unittest.mock import MagicMock, patch

import orchestrator.graph as graph_mod
from orchestrator.graph import build_graph

PRIVATE_MARKER = "SECRET-PRIVATE-MARKER"


class _FakeHttpClient:
    """Captures every outbound HTTP call and returns a canned public summary."""

    def __init__(self, received: list):
        """Initialise with a mutable list that will collect every outbound payload."""
        self._received = received

    def post(self, url, *, json=None, **kwargs):
        """Record the JSON payload and return a canned successful response."""
        self._received.append(json)
        resp = MagicMock()
        resp.json.return_value = {"summary": "public context summary"}
        resp.raise_for_status.return_value = None
        return resp

    def __enter__(self):
        """Support use as a context manager."""
        return self

    def __exit__(self, *args):
        """No-op context-manager exit."""


def test_only_query_crosses_the_boundary():
    """Outbound payload to the public worker must be exactly {query: <query string>}."""
    received = []

    with (
        patch.object(graph_mod, "httpx") as mock_httpx,
        patch.object(
            graph_mod,
            "_private_retrieve",
            return_value=[f"{PRIVATE_MARKER}: internal policy document"],
        ),
        patch.object(graph_mod, "_synthesize", return_value="synthesized answer"),
    ):
        mock_httpx.Client = MagicMock(return_value=_FakeHttpClient(received))
        build_graph().invoke({"query": "what is the policy?"})

    assert len(received) == 1, "Expected exactly one outbound call to the public worker"
    assert received[0] == {"query": "what is the policy?"}, (
        f"Outbound payload must be exactly {{query: ...}}, got: {received[0]}"
    )


def test_private_marker_never_appears_in_outbound_payload():
    """Private document content must never appear anywhere in the outbound HTTP payload."""
    received = []

    with (
        patch.object(graph_mod, "httpx") as mock_httpx,
        patch.object(
            graph_mod,
            "_private_retrieve",
            return_value=[
                f"{PRIVATE_MARKER}: confidential financials $47.3M",
                f"Another doc with {PRIVATE_MARKER} embedded",
            ],
        ),
        patch.object(graph_mod, "_synthesize", return_value="answer"),
    ):
        mock_httpx.Client = MagicMock(return_value=_FakeHttpClient(received))
        build_graph().invoke({"query": "tell me about revenue"})

    blob = str(received)
    assert PRIVATE_MARKER not in blob, (
        f"Private marker must never appear in anything sent to the public worker. Found in: {blob}"
    )


def test_query_string_is_sent_verbatim():
    """The query string is forwarded to the public worker without modification."""
    received = []
    query = "what are the security procedures for incident response?"

    with (
        patch.object(graph_mod, "httpx") as mock_httpx,
        patch.object(graph_mod, "_private_retrieve", return_value=[]),
        patch.object(graph_mod, "_synthesize", return_value="answer"),
    ):
        mock_httpx.Client = MagicMock(return_value=_FakeHttpClient(received))
        build_graph().invoke({"query": query})

    assert received[0]["query"] == query
