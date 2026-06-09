"""Wire contract types shared between the orchestrator and the public worker.

Only :class:`PublicWorkerRequest` and :class:`PublicWorkerResponse` cross the
cluster boundary.  The contract is intentionally minimal: the outbound payload
carries only the raw query string, enforcing the one-way membrane invariant.
"""

from pydantic import BaseModel


class PublicWorkerRequest(BaseModel):
    """Payload sent from the orchestrator to the public worker.

    Attributes:
        query: The raw user query string.  This is the *only* field allowed to
            cross from the private cluster to the public cluster.
    """

    query: str


class PublicWorkerResponse(BaseModel):
    """Payload returned by the public worker to the orchestrator.

    Attributes:
        summary: A summarised string of publicly-retrieved context.  Contains
            no private data; safe to merge with private chunks on the private
            cluster before synthesis.
    """

    summary: str


class OrchestratorRequest(BaseModel):
    """Request body accepted by the orchestrator's ``/query`` endpoint.

    Attributes:
        query: The natural-language question from the end user.
    """

    query: str


class OrchestratorResponse(BaseModel):
    """Response body returned by the orchestrator's ``/query`` endpoint.

    Attributes:
        answer: The synthesised answer produced by the local model.  The answer
            may be grounded in private data and must never leave the private
            cluster.
    """

    answer: str
