"""Unit tests for the public Chroma retriever."""

import uuid

import chromadb
import pytest

from public.retriever import retrieve


def _fresh_col():
    """Return a new, isolated EphemeralClient collection with a unique name."""
    client = chromadb.EphemeralClient()
    return client.get_or_create_collection(f"pub-{uuid.uuid4().hex}")


@pytest.fixture
def col():
    """Fixture: pre-populated public collection with three documents."""
    c = _fresh_col()
    c.add(
        documents=[
            "RAG combines retrieval with generation to ground LLM answers.",
            "Dense embeddings enable semantic similarity search.",
            "ChromaDB stores and queries vector embeddings efficiently.",
        ],
        ids=["doc1", "doc2", "doc3"],
    )
    return c


def test_retrieve_returns_strings(col):
    """retrieve() returns a list of strings for a non-empty collection."""
    results = retrieve("what is RAG?", _collection=col)
    assert isinstance(results, list)
    assert all(isinstance(d, str) for d in results)


def test_retrieve_respects_n_results(col):
    """retrieve() returns at most n_results items."""
    results = retrieve("embedding", n_results=2, _collection=col)
    assert len(results) <= 2


def test_retrieve_empty_collection():
    """retrieve() returns an empty list when the collection has no documents."""
    empty = _fresh_col()
    results = retrieve("anything", _collection=empty)
    assert results == []


def test_retrieve_caps_n_results_to_collection_size(col):
    """retrieve() silently caps n_results to the collection size to avoid Chroma errors."""
    results = retrieve("ranking", n_results=10, _collection=col)
    assert len(results) <= 3
