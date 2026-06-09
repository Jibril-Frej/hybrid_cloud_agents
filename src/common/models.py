from pydantic import BaseModel


class PublicWorkerRequest(BaseModel):
    query: str


class PublicWorkerResponse(BaseModel):
    summary: str


class OrchestratorRequest(BaseModel):
    query: str


class OrchestratorResponse(BaseModel):
    answer: str
