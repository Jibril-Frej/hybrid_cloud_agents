from fastapi import FastAPI

from common.models import PublicWorkerRequest, PublicWorkerResponse
from public.retriever import retrieve
from public.summarizer import summarize

app = FastAPI(title="Public RAG Worker")


@app.post("/retrieve", response_model=PublicWorkerResponse)
def retrieve_endpoint(req: PublicWorkerRequest) -> PublicWorkerResponse:
    chunks = retrieve(req.query)
    summary = summarize(req.query, chunks)
    return PublicWorkerResponse(summary=summary)


@app.get("/health")
def health():
    return {"status": "ok"}
