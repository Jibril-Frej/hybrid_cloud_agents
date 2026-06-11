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

**V1** — minimal two-`kind`-cluster plumbing (no AI, no retrieval, no
encryption yet). The full prior prototype (LangGraph + Chroma + local LLM +
mTLS) is preserved on the `archive/v1-original` branch and will be
reintroduced incrementally in later versions.

## Prerequisites

- Python 3.11+ and [uv](https://docs.astral.sh/uv/)
- [Docker](https://docs.docker.com/get-docker/)
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)

## Running V1

```console
$ uv sync                 # install dependencies
$ make test                # lint + unit + boundary tests

$ make dev                  # spin up both kind clusters, build images, deploy
$ make test-e2e             # query the deployed orchestrator end-to-end
$ make clusters-down         # tear down both kind clusters when done
```

`make test-e2e` sends a query to the orchestrator's NodePort (private
cluster) and asserts it gets back the public worker's canned response,
proving the cross-cluster HTTP path works.

Docs (including the mkdocstrings API reference) are built with
`uv run mkdocs build` and served locally with `uv run mkdocs serve`.

## Decisions log

Significant project decisions and their rationale are recorded in
[`DECISIONS.md`](DECISIONS.md).
