"""Unit tests for common.models."""

import pytest
from pydantic import ValidationError

from common.models import PublicWorkerRequest, PublicWorkerResponse


class TestPublicWorkerRequest:
    """Test PublicWorkerRequest model validation."""

    def test_valid_request(self):
        """Create a valid PublicWorkerRequest with a query string."""
        req = PublicWorkerRequest(query="test query")
        assert req.query == "test query"

    def test_empty_query(self):
        """Allow empty query strings."""
        req = PublicWorkerRequest(query="")
        assert req.query == ""

    def test_query_required(self):
        """Raise ValidationError if query is missing."""
        with pytest.raises(ValidationError):
            PublicWorkerRequest()

    def test_query_must_be_string(self):
        """Raise ValidationError if query is not a string."""
        with pytest.raises(ValidationError):
            PublicWorkerRequest(query=123)

    def test_model_dump(self):
        """Serialize to dict via model_dump."""
        req = PublicWorkerRequest(query="hello world")
        assert req.model_dump() == {"query": "hello world"}

    def test_model_validate(self):
        """Deserialize from dict via model_validate."""
        data = {"query": "test"}
        req = PublicWorkerRequest.model_validate(data)
        assert req.query == "test"


class TestPublicWorkerResponse:
    """Test PublicWorkerResponse model validation."""

    def test_valid_response(self):
        """Create a valid PublicWorkerResponse with an answer string."""
        resp = PublicWorkerResponse(answer="test answer")
        assert resp.answer == "test answer"

    def test_empty_answer(self):
        """Allow empty answer strings."""
        resp = PublicWorkerResponse(answer="")
        assert resp.answer == ""

    def test_answer_required(self):
        """Raise ValidationError if answer is missing."""
        with pytest.raises(ValidationError):
            PublicWorkerResponse()

    def test_answer_must_be_string(self):
        """Raise ValidationError if answer is not a string."""
        with pytest.raises(ValidationError):
            PublicWorkerResponse(answer=42)

    def test_model_dump(self):
        """Serialize to dict via model_dump."""
        resp = PublicWorkerResponse(answer="hello world")
        assert resp.model_dump() == {"answer": "hello world"}

    def test_model_validate(self):
        """Deserialize from dict via model_validate."""
        data = {"answer": "test"}
        resp = PublicWorkerResponse.model_validate(data)
        assert resp.answer == "test"
