"""Pydantic models for the wire contract between the orchestrator and the public worker.

These are the only payloads allowed to cross the cluster boundary. See
``.claude/skills/trust-boundary/SKILL.md`` for the one-way membrane invariant
that this contract exists to enforce.
"""

from pydantic import BaseModel


class PublicWorkerRequest(BaseModel):
    """Request sent from the orchestrator (private) to the public worker.

    Carries only the raw user query — the sole piece of information that may
    cross from the private cluster to the public cluster.
    """

    query: str


class PublicWorkerResponse(BaseModel):
    """Response returned by the public worker to the orchestrator."""

    answer: str
