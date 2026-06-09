"""FastAPI application for the public RAG worker.

Exposes a single ``POST /retrieve`` endpoint that accepts a query string and
returns a summarized public-context string.  This service runs in the public
cluster and is never given private data.
"""

import logging
import logging.config

from fastapi import FastAPI

from common.models import PublicWorkerRequest, PublicWorkerResponse
from public.retriever import retrieve
from public.summarizer import summarize

logging.config.dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            }
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["stdout"]},
    }
)

log = logging.getLogger(__name__)

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
    log.info("Received retrieve request: query=%r", req.query)
    chunks = retrieve(req.query)
    log.info("Retrieved %d public chunk(s)", len(chunks))
    summary = summarize(req.query, chunks)
    log.info("Returning summary (%d chars)", len(summary))
    return PublicWorkerResponse(summary=summary)


@app.get("/health")
def health():
    """Return a simple liveness check payload."""
    return {"status": "ok"}
