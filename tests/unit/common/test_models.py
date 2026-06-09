"""Unit tests for the Pydantic wire models in common.models."""

import pytest
from pydantic import ValidationError

from common.models import (
    OrchestratorRequest,
    OrchestratorResponse,
    PublicWorkerRequest,
    PublicWorkerResponse,
)


def test_public_worker_request_roundtrip():
    """PublicWorkerRequest serialises to exactly {query: ...}."""
    req = PublicWorkerRequest(query="what is RAG?")
    assert req.model_dump() == {"query": "what is RAG?"}


def test_public_worker_response_roundtrip():
    """PublicWorkerResponse preserves the summary field through construction."""
    resp = PublicWorkerResponse(summary="RAG combines retrieval and generation.")
    assert resp.summary == "RAG combines retrieval and generation."


def test_orchestrator_request_roundtrip():
    """OrchestratorRequest preserves the query field through construction."""
    req = OrchestratorRequest(query="explain BM25")
    assert req.query == "explain BM25"


def test_orchestrator_response_roundtrip():
    """OrchestratorResponse preserves the answer field through construction."""
    resp = OrchestratorResponse(answer="BM25 is a ranking function.")
    assert resp.answer == "BM25 is a ranking function."


def test_public_worker_request_requires_query():
    """PublicWorkerRequest raises ValidationError when the query field is absent."""
    with pytest.raises(ValidationError):
        PublicWorkerRequest()  # type: ignore[call-arg]


def test_public_worker_request_wire_format():
    """Outbound wire payload must be exactly {query: ...} with no extra fields."""
    req = PublicWorkerRequest(query="hello")
    payload = req.model_dump()
    assert set(payload.keys()) == {"query"}
