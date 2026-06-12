"""FastAPI app for the public worker.

Receives a query from the orchestrator and returns matching chunks from the
public Chroma index.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from common.models import PublicWorkerRequest, PublicWorkerResponse
from public.retriever import retrieve, warm_up


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Build the public Chroma index before serving requests (see `warm_up`)."""
    warm_up()
    yield


app = FastAPI(title="public-worker", lifespan=lifespan)


@app.post("/query")
def query(request: PublicWorkerRequest) -> PublicWorkerResponse:
    """Return the public document chunks most relevant to the query."""
    chunks = retrieve(request.query)
    return PublicWorkerResponse(answer="\n".join(chunks))
