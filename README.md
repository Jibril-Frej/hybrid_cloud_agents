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

## Stack and why

- **uv** — single tool for the venv, dependency resolution, and a lockfile
  (`uv.lock`); fast enough that recreating the environment from scratch is
  never a cost worth avoiding. See `DECISIONS.md`.
- **FastAPI + uvicorn** — minimal, typed HTTP framework for both services.
  Async-capable, but V1's handlers are plain `def` — there's no concurrent
  work yet to benefit from `async`.
- **httpx** — used for the orchestrator's one outbound call to the public
  worker. A single synchronous `httpx.post` is all V1 needs.
- **pydantic** — `PublicWorkerRequest`/`PublicWorkerResponse` in
  `src/common/models.py` define the wire contract once, shared by both
  services, so request/response shapes can't silently drift apart.
- **Two `kind` clusters (`private`, `public`)** — the cheapest way to get two
  genuinely separate local Kubernetes clusters that mirror the on-prem/cloud
  split, with no cloud cost. Both clusters join the same `kind` Docker
  network, so cross-cluster traffic is possible — but `kind` provides no
  cross-cluster DNS, hence the `hostAliases` patch in `make deploy`.
- **Plain HTTP, no mTLS** — V1 isolates the *topology* and the *one-way
  membrane contract* from transport security. mTLS is a self-contained,
  additive increment reserved for V2 (see `DECISIONS.md`, "V1 drops mTLS").
- **Plain Kubernetes YAML manifests + Docker** — no Helm/Kustomize. Two small
  Deployment+Service pairs don't need templating yet.
- **ruff** — one tool for linting, formatting, import sorting, and docstring
  conventions (replaces flake8 + black + isort + pydocstyle).
- **GitHub Actions** — `lint-and-unit` and `boundary` jobs mirror `make test`.
  E2E is excluded from CI since it needs live `kind` clusters.

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

## Testing

- **`tests/unit/`** — mirrors `src/`. Tests each FastAPI endpoint and the
  Pydantic models in isolation; the orchestrator's outbound call to the
  public worker is mocked.
- **`tests/integration/boundary/`** (`test_membrane.py`) — the **one-way
  membrane** test. Spins up the orchestrator against a fake public worker and
  asserts that exactly one outbound request is made and its body is *only*
  `{"query": "<the raw query>"}` — for a range of inputs (empty string,
  special characters, etc.). This is the contract that becomes
  safety-critical from V3 onward, once private data exists; V1 fixes its
  shape now. Run via `make test` and the CI `boundary` job.
- **`tests/integration/e2e/`** (`test_kind_clusters.py`) — marked
  `@pytest.mark.e2e` and excluded from the default test run
  (`addopts = "-m 'not e2e'"` in `pyproject.toml`). Run via `make test-e2e`
  after `make dev`. It looks up the private cluster's kind node IP, sends a
  real HTTP request to the orchestrator's NodePort, and asserts the response
  is the public worker's canned answer — proving the full topology (build →
  load → deploy → cross-cluster HTTP → response) works end to end, not just
  the application code in isolation.

## Decisions log

Significant project decisions and their rationale are recorded in
[`DECISIONS.md`](DECISIONS.md).
