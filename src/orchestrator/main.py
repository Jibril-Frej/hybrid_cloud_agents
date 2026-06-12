"""FastAPI app for the orchestrator.

Receives a query, forwards it to the public worker over mutually authenticated
TLS, and combines its response with locally retrieved private context. Per
the one-way membrane invariant (see
``.claude/skills/trust-boundary/SKILL.md``), the only payload sent to the
public worker is the raw query.
"""

import logging
import os
import ssl
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from common.models import PublicWorkerRequest, PublicWorkerResponse
from orchestrator.retriever import retrieve, warm_up

PUBLIC_WORKER_URL = os.environ.get("PUBLIC_WORKER_URL", "https://localhost:8001/query")
PUBLIC_WORKER_CERT = os.environ.get("PUBLIC_WORKER_CERT")
PUBLIC_WORKER_KEY = os.environ.get("PUBLIC_WORKER_KEY")
PUBLIC_WORKER_CA = os.environ.get("PUBLIC_WORKER_CA")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Configure logging and build the private Chroma index (see `warm_up`)."""
    logging.basicConfig(level=logging.INFO)
    warm_up()
    yield


app = FastAPI(title="orchestrator", lifespan=lifespan)


def _mtls_kwargs() -> dict[str, object]:
    """Return httpx request kwargs for mTLS, or {} if certs aren't configured.

    httpx.post() has no ``cert=`` parameter, and passing a CA path string as
    ``verify=`` alongside a client cert breaks the TLS handshake (httpx
    ReadError). Both the CA and the client cert/key must instead be combined
    into a single ssl.SSLContext passed as ``verify=``.
    """
    if PUBLIC_WORKER_CERT and PUBLIC_WORKER_KEY and PUBLIC_WORKER_CA:
        context = ssl.create_default_context(cafile=PUBLIC_WORKER_CA)
        context.load_cert_chain(PUBLIC_WORKER_CERT, PUBLIC_WORKER_KEY)
        return {"verify": context}
    return {}


@app.post("/query")
def query(request: PublicWorkerRequest) -> PublicWorkerResponse:
    """Combine the public worker's response with locally retrieved private context.

    The public worker only ever receives the raw query (see
    ``.claude/skills/trust-boundary/SKILL.md``); private chunks are retrieved
    locally afterwards and never sent anywhere.
    """
    response = httpx.post(PUBLIC_WORKER_URL, json=request.model_dump(), **_mtls_kwargs())
    response.raise_for_status()
    public_response = PublicWorkerResponse.model_validate(response.json())

    private_chunks = retrieve(request.query)

    return PublicWorkerResponse(
        answer=f"{public_response.answer} | private context: {private_chunks}"
    )
