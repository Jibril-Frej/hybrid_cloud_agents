"""Unit tests for the LangGraph orchestration graph."""

from unittest.mock import MagicMock, patch

import orchestrator.graph as graph_mod
from orchestrator.graph import build_graph


def _make_mock_http(summary="public summary"):
    """Return a mock httpx.Client context manager that returns the given summary."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"summary": summary}
    mock_resp.raise_for_status.return_value = None

    mock_client = MagicMock()
    mock_client.post.return_value = mock_resp
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    mock_cls = MagicMock(return_value=mock_client)
    return mock_cls, mock_client


def test_graph_returns_answer():
    """build_graph().invoke() returns a dict containing the synthesizer's answer."""
    mock_cls, _ = _make_mock_http()
    with (
        patch.object(graph_mod, "httpx") as mock_httpx,
        patch.object(graph_mod, "_private_retrieve", return_value=["private chunk"]),
        patch.object(graph_mod, "_synthesize", return_value="final answer"),
    ):
        mock_httpx.Client = mock_cls
        g = build_graph()
        result = g.invoke({"query": "test question"})

    assert result["answer"] == "final answer"


def test_graph_passes_both_contexts_to_synthesizer():
    """The graph passes both the public summary and private chunks to the synthesizer."""
    mock_cls, _ = _make_mock_http(summary="pub summary")
    synth_calls = []

    def capture_synth(query, public_summary, private_chunks):
        """Capture synthesizer arguments for assertion."""
        synth_calls.append({"query": query, "pub": public_summary, "priv": private_chunks})
        return "answer"

    with (
        patch.object(graph_mod, "httpx") as mock_httpx,
        patch.object(graph_mod, "_private_retrieve", return_value=["priv chunk"]),
        patch.object(graph_mod, "_synthesize", side_effect=capture_synth),
    ):
        mock_httpx.Client = mock_cls
        build_graph().invoke({"query": "q"})

    assert len(synth_calls) == 1
    assert synth_calls[0]["pub"] == "pub summary"
    assert synth_calls[0]["priv"] == ["priv chunk"]


def test_graph_degrades_gracefully_when_public_worker_fails():
    """The graph continues with an empty public summary when the public worker raises."""
    synth_calls = []

    def capture_synth(query, public_summary, private_chunks):
        """Capture synthesizer arguments for assertion."""
        synth_calls.append({"pub": public_summary, "priv": private_chunks})
        return "private-only answer"

    mock_client = MagicMock()
    mock_client.post.side_effect = Exception("connection refused")
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with (
        patch.object(graph_mod, "httpx") as mock_httpx,
        patch.object(graph_mod, "_private_retrieve", return_value=["priv chunk"]),
        patch.object(graph_mod, "_synthesize", side_effect=capture_synth),
    ):
        mock_httpx.Client = MagicMock(return_value=mock_client)
        result = build_graph().invoke({"query": "q"})

    assert result["answer"] == "private-only answer"
    assert synth_calls[0]["pub"] == ""
    assert synth_calls[0]["priv"] == ["priv chunk"]
