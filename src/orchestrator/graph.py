from __future__ import annotations

import os
from typing import TypedDict

import httpx

from common.models import PublicWorkerRequest, PublicWorkerResponse
from orchestrator.retriever import retrieve as _private_retrieve
from orchestrator.synthesizer import synthesize as _synthesize


class AgentState(TypedDict, total=False):
    query: str
    public_summary: str
    private_chunks: list[str]
    answer: str


def receive_query(state: AgentState) -> dict:
    return {"query": state["query"]}


def public_retrieve(state: AgentState) -> dict:
    """Sends only the query to the public worker; returns the public summary."""
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
    except Exception:
        summary = ""

    return {"public_summary": summary}


def private_retrieve(state: AgentState) -> dict:
    """Queries the local private Chroma index; data never leaves this function."""
    chunks = _private_retrieve(state["query"])
    return {"private_chunks": chunks}


def synthesize(state: AgentState) -> dict:
    """Merges public summary + private chunks and calls the local model."""
    answer = _synthesize(
        query=state["query"],
        public_summary=state.get("public_summary", ""),
        private_chunks=state.get("private_chunks", []),
    )
    return {"answer": answer}


def return_answer(state: AgentState) -> dict:
    return {"answer": state["answer"]}


def build_graph():
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
