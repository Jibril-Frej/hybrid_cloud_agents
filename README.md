# Hybrid Cloud Agents

A proof-of-concept for a drag-and-drop **agent builder focused on
infrastructure** — a tool for composing what gets deployed on a **private
(on-prem)** cluster versus a **public (cloud)** cluster, while guaranteeing
that **private data never leaves the private cluster** (with exactly one
exception: the raw user query).

The project is built incrementally as a series of versioned prototypes. See
[`specs/index.md`](specs/index.md) for the long-term vision and the full
roadmap, and [`specs/v1-spec.md`](specs/v1-spec.md) for the current version.

## Status

**V1 in progress** — minimal two-`kind`-cluster plumbing (no AI, no
retrieval, no encryption yet). The full prior prototype (LangGraph + Chroma +
local LLM + mTLS) is preserved on the `archive/v1-original` branch and will be
reintroduced incrementally in later versions.

## Prerequisites

- Python 3.11+
- [Docker](https://docs.docker.com/get-docker/)
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)

## Decisions log

Significant project decisions and their rationale are recorded in
[`DECISIONS.md`](DECISIONS.md).
