"""FastAPI app for the orchestrator.

Receives a query, forwards it to the public worker over plain HTTP, and
returns the response unchanged. Per the one-way membrane invariant (see
``.claude/skills/trust-boundary/SKILL.md``), the only payload sent to the
public worker is the raw query.
"""

import os

import httpx
from fastapi import FastAPI

from common.models import PublicWorkerRequest, PublicWorkerResponse

PUBLIC_WORKER_URL = os.environ.get("PUBLIC_WORKER_URL", "http://localhost:8001/query")

app = FastAPI(title="orchestrator")


@app.post("/query")
def query(request: PublicWorkerRequest) -> PublicWorkerResponse:
    """Forward the query to the public worker and return its response unchanged."""
    response = httpx.post(PUBLIC_WORKER_URL, json=request.model_dump())
    response.raise_for_status()
    return PublicWorkerResponse.model_validate(response.json())
