"""FastAPI app for the orchestrator.

Receives a query, forwards it to the public worker over mutually authenticated
TLS, and returns the response unchanged. Per the one-way membrane invariant
(see ``.claude/skills/trust-boundary/SKILL.md``), the only payload sent to the
public worker is the raw query.
"""

import os

import httpx
from fastapi import FastAPI

from common.models import PublicWorkerRequest, PublicWorkerResponse

PUBLIC_WORKER_URL = os.environ.get("PUBLIC_WORKER_URL", "https://localhost:8001/query")
PUBLIC_WORKER_CERT = os.environ.get("PUBLIC_WORKER_CERT")
PUBLIC_WORKER_KEY = os.environ.get("PUBLIC_WORKER_KEY")
PUBLIC_WORKER_CA = os.environ.get("PUBLIC_WORKER_CA")

app = FastAPI(title="orchestrator")


def _mtls_kwargs() -> dict[str, object]:
    """Return httpx client kwargs for mTLS, or {} if certs aren't configured."""
    if PUBLIC_WORKER_CERT and PUBLIC_WORKER_KEY and PUBLIC_WORKER_CA:
        return {"cert": (PUBLIC_WORKER_CERT, PUBLIC_WORKER_KEY), "verify": PUBLIC_WORKER_CA}
    return {}


@app.post("/query")
def query(request: PublicWorkerRequest) -> PublicWorkerResponse:
    """Forward the query to the public worker and return its response unchanged."""
    response = httpx.post(PUBLIC_WORKER_URL, json=request.model_dump(), **_mtls_kwargs())
    response.raise_for_status()
    return PublicWorkerResponse.model_validate(response.json())
