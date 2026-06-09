from fastapi import FastAPI, HTTPException

from common.models import OrchestratorRequest, OrchestratorResponse
from orchestrator.graph import graph

app = FastAPI(title="Orchestrator")


@app.post("/query", response_model=OrchestratorResponse)
def query_endpoint(req: OrchestratorRequest) -> OrchestratorResponse:
    try:
        state = graph.invoke({"query": req.query})
        return OrchestratorResponse(answer=state["answer"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/health")
def health():
    return {"status": "ok"}
