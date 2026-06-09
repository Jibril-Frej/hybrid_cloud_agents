"""FastAPI application for the public RAG worker.

Exposes a single ``POST /retrieve`` endpoint that accepts a query string and
returns a summarized public-context string.  This service runs in the public
cluster and is never given private data.
"""

from fastapi import FastAPI

from common.models import PublicWorkerRequest, PublicWorkerResponse
from public.retriever import retrieve
from public.summarizer import summarize

app = FastAPI(title="Public RAG Worker")


@app.post("/retrieve", response_model=PublicWorkerResponse)
def retrieve_endpoint(req: PublicWorkerRequest) -> PublicWorkerResponse:
    """Retrieve and summarize public context for the given query.

    Args:
        req: The inbound request containing only the user query.

    Returns:
        A :class:`~common.models.PublicWorkerResponse` whose ``summary`` field
        contains a condensed string of publicly-retrieved context.
    """
    chunks = retrieve(req.query)
    summary = summarize(req.query, chunks)
    return PublicWorkerResponse(summary=summary)


@app.get("/health")
def health():
    """Return a simple liveness check payload."""
    return {"status": "ok"}
