"""Unit tests for the private-cluster Chroma retriever."""

import uuid

import chromadb
import pytest

from orchestrator.retriever import retrieve


def _fresh_col():
    """Return a new, isolated EphemeralClient collection with a unique name."""
    client = chromadb.EphemeralClient()
    return client.get_or_create_collection(f"priv-{uuid.uuid4().hex}")


@pytest.fixture
def col():
    """Fixture: pre-populated private collection with three documents."""
    c = _fresh_col()
    c.add(
        documents=[
            "ACME employee bonus is 15% of base salary for individual contributors.",
            "Data classified RESTRICTED must stay on company-managed infrastructure.",
            "Incident response: report within 1 hour to security@acme.internal.",
        ],
        ids=["doc1", "doc2", "doc3"],
    )
    return c


def test_retrieve_returns_strings(col):
    """retrieve() returns a list of strings for a non-empty private collection."""
    results = retrieve("what is the bonus policy?", _collection=col)
    assert isinstance(results, list)
    assert all(isinstance(d, str) for d in results)


def test_retrieve_empty_collection():
    """retrieve() returns an empty list when the private collection has no documents."""
    empty = _fresh_col()
    results = retrieve("anything", _collection=empty)
    assert results == []


def test_retrieve_caps_n_results_to_collection_size(col):
    """retrieve() silently caps n_results to the collection size to avoid Chroma errors."""
    results = retrieve("security", n_results=10, _collection=col)
    assert len(results) <= 3
