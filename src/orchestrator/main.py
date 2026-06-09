"""FastAPI application for the private-cluster orchestrator.

Exposes a single ``POST /query`` endpoint that drives the LangGraph pipeline
end-to-end and returns the synthesized answer.  This service runs entirely
within the private cluster and is the only entry point for end users.
"""

import logging
import logging.config

from fastapi import FastAPI, HTTPException

from common.models import OrchestratorRequest, OrchestratorResponse
from orchestrator.graph import graph

logging.config.dictConfig({
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
})

log = logging.getLogger(__name__)

app = FastAPI(title="Orchestrator")


@app.post("/query", response_model=OrchestratorResponse)
def query_endpoint(req: OrchestratorRequest) -> OrchestratorResponse:
    """Run the hybrid RAG pipeline and return the synthesized answer.

    Invokes the compiled LangGraph graph which performs parallel public and
    private retrieval before synthesizing a final answer with the local model.

    Args:
        req: The inbound request containing the user's natural-language query.

    Returns:
        An :class:`~common.models.OrchestratorResponse` with the ``answer``
        field populated.

    Raises:
        HTTPException: 500 if the graph raises an unexpected exception.
    """
    log.info("Received query: %r", req.query)
    try:
        state = graph.invoke({"query": req.query})
        answer = state["answer"]
        log.info("Returning answer (%d chars)", len(answer))
        return OrchestratorResponse(answer=answer)
    except Exception as exc:
        log.exception("Graph invocation failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/health")
def health():
    """Return a simple liveness check payload."""
    return {"status": "ok"}
