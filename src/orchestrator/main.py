"""FastAPI application for the private-cluster orchestrator.

Exposes a single ``POST /query`` endpoint that drives the LangGraph pipeline
end-to-end and returns the synthesized answer.  This service runs entirely
within the private cluster and is the only entry point for end users.
"""

from fastapi import FastAPI, HTTPException

from common.models import OrchestratorRequest, OrchestratorResponse
from orchestrator.graph import graph

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
    try:
        state = graph.invoke({"query": req.query})
        return OrchestratorResponse(answer=state["answer"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/health")
def health():
    """Return a simple liveness check payload."""
    return {"status": "ok"}
