"""LangGraph orchestration graph for hybrid public+private RAG.

The graph implements the four-node pipeline described in the V1 spec::

    receive_query → [public_retrieve ‖ private_retrieve] → synthesize → return_answer

Public and private retrieval run as parallel branches.  The synthesizer node
waits for both branches to complete before generating the final answer.

The trust-boundary invariant is enforced here:
- ``public_retrieve`` sends **only** the query string outward.
- ``private_retrieve`` never forwards chunks outside this module.
- ``synthesize`` always runs locally; it is never delegated to the public cluster.
"""

from __future__ import annotations

import os
from typing import Any, TypedDict

import httpx

from common.models import PublicWorkerRequest, PublicWorkerResponse
from orchestrator.retriever import retrieve as _private_retrieve
from orchestrator.synthesizer import synthesize as _synthesize


class AgentState(TypedDict, total=False):
    """Mutable state passed between graph nodes.

    All fields are optional (``total=False``) so the graph can be invoked with
    only ``{"query": "..."}`` and each node fills in its own output keys.

    Attributes:
        query: The raw user query string.
        public_summary: Summarized public context returned by the public worker.
        private_chunks: Private document chunks retrieved locally.
        answer: The final synthesized answer produced by the local model.
    """

    query: str
    public_summary: str
    private_chunks: list[str]
    answer: str


def receive_query(state: AgentState) -> dict:
    """Pass the query through unchanged; acts as the graph entry point.

    Args:
        state: Current graph state.

    Returns:
        A dict with the ``query`` key preserved for downstream nodes.
    """
    return {"query": state["query"]}


def public_retrieve(state: AgentState) -> dict:
    """Send only the query to the public worker; return the public summary.

    Constructs an mTLS-authenticated ``httpx`` request carrying exclusively
    the query string.  On any network or HTTP error the summary degrades to an
    empty string so the pipeline can continue with private-only context.

    Args:
        state: Current graph state.  Only ``state["query"]`` is read.

    Returns:
        A dict with ``public_summary`` set to the retrieved summary string
        (empty string on failure).
    """
    query = state["query"]
    url = os.environ.get("PUBLIC_WORKER_URL", "https://public-worker:8080")

    mtls_kwargs: dict = {}
    cert = os.environ.get("PUBLIC_WORKER_CERT", "")
    key = os.environ.get("PUBLIC_WORKER_KEY", "")
    ca = os.environ.get("PUBLIC_WORKER_CA", "")
    if cert and key:
        mtls_kwargs["cert"] = (cert, key)
    if ca:
        mtls_kwargs["verify"] = ca

    try:
        with httpx.Client(**mtls_kwargs, timeout=30.0) as client:
            body = PublicWorkerRequest(query=query).model_dump()
            resp = client.post(f"{url}/retrieve", json=body)
            resp.raise_for_status()
            summary = PublicWorkerResponse(**resp.json()).summary
    except Exception:  # pylint: disable=broad-exception-caught  # intentional graceful degradation
        summary = ""

    return {"public_summary": summary}


def private_retrieve(state: AgentState) -> dict:
    """Query the local private Chroma index; chunks never leave this function.

    Args:
        state: Current graph state.  Only ``state["query"]`` is read.

    Returns:
        A dict with ``private_chunks`` set to the list of retrieved document
        strings.
    """
    chunks = _private_retrieve(state["query"])
    return {"private_chunks": chunks}


def synthesize(state: AgentState) -> dict:
    """Merge public summary and private chunks, then call the local model.

    Args:
        state: Current graph state after both retrieval branches have completed.

    Returns:
        A dict with ``answer`` set to the generated response string.
    """
    answer = _synthesize(
        query=state["query"],
        public_summary=state.get("public_summary", ""),
        private_chunks=state.get("private_chunks", []),
    )
    return {"answer": answer}


def return_answer(state: AgentState) -> dict:
    """Pass the answer through unchanged; acts as the graph exit point.

    Args:
        state: Current graph state containing the synthesized ``answer``.

    Returns:
        A dict with the ``answer`` key preserved for the caller.
    """
    return {"answer": state["answer"]}


def build_graph() -> Any:
    """Compile and return the LangGraph ``StateGraph``.

    Wires up the four nodes with a fork-join topology so that
    ``public_retrieve`` and ``private_retrieve`` execute as parallel branches.

    Returns:
        A compiled :class:`langgraph.graph.CompiledGraph` ready for
        ``.invoke()``.
    """
    from langgraph.graph import END, START, StateGraph

    builder = StateGraph(AgentState)
    builder.add_node("receive_query", receive_query)
    builder.add_node("public_retrieve", public_retrieve)
    builder.add_node("private_retrieve", private_retrieve)
    builder.add_node("synthesize", synthesize)
    builder.add_node("return_answer", return_answer)

    builder.add_edge(START, "receive_query")
    # Fan out: public and private retrieval run in parallel
    builder.add_edge("receive_query", "public_retrieve")
    builder.add_edge("receive_query", "private_retrieve")
    # Fan in: synthesize waits for both branches
    builder.add_edge("public_retrieve", "synthesize")
    builder.add_edge("private_retrieve", "synthesize")
    builder.add_edge("synthesize", "return_answer")
    builder.add_edge("return_answer", END)

    return builder.compile()


graph = build_graph()
