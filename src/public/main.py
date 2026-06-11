"""FastAPI app for the public worker.

Receives a query from the orchestrator and returns a canned response. V1 has
no retrieval or AI — this is pure plumbing to prove the cross-cluster HTTP
path works.
"""

from fastapi import FastAPI

from common.models import PublicWorkerRequest, PublicWorkerResponse

app = FastAPI(title="public-worker")


@app.post("/query")
def query(request: PublicWorkerRequest) -> PublicWorkerResponse:
    """Return a canned response acknowledging the received query."""
    return PublicWorkerResponse(answer=f"public worker received: {request.query}")
