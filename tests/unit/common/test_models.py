import pytest
from pydantic import ValidationError

from common.models import (
    OrchestratorRequest,
    OrchestratorResponse,
    PublicWorkerRequest,
    PublicWorkerResponse,
)


def test_public_worker_request_roundtrip():
    req = PublicWorkerRequest(query="what is RAG?")
    assert req.model_dump() == {"query": "what is RAG?"}


def test_public_worker_response_roundtrip():
    resp = PublicWorkerResponse(summary="RAG combines retrieval and generation.")
    assert resp.summary == "RAG combines retrieval and generation."


def test_orchestrator_request_roundtrip():
    req = OrchestratorRequest(query="explain BM25")
    assert req.query == "explain BM25"


def test_orchestrator_response_roundtrip():
    resp = OrchestratorResponse(answer="BM25 is a ranking function.")
    assert resp.answer == "BM25 is a ranking function."


def test_public_worker_request_requires_query():
    with pytest.raises(ValidationError):
        PublicWorkerRequest()  # type: ignore[call-arg]


def test_public_worker_request_wire_format():
    # The outbound wire payload must be exactly {"query": "..."}; no extra fields.
    req = PublicWorkerRequest(query="hello")
    payload = req.model_dump()
    assert set(payload.keys()) == {"query"}
