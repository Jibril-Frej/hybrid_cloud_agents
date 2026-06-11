# V1 Spec — Minimal two-cluster plumbing

V1 proves the basic topology: two `kind` clusters (`private`, `public`) that
can be built, deployed, and torn down reliably, with a single HTTP call
crossing from the private cluster to the public cluster and a response coming
back. **No AI, no retrieval, no encryption** — those are reintroduced one at a
time in later versions (see [`index.md`](index.md)). The goal is a system
that's fast to deploy and fast to test, so iteration on the topology itself is
cheap.

## Stack

| Concern | Choice |
|---|---|
| Language | Python 3.11+ |
| Web framework | FastAPI + uvicorn |
| Cross-cluster transport | Plain HTTP (no mTLS — see [v2-spec.md](v2-spec.md)) |
| Packaging | Docker images + plain Kubernetes YAML manifests |
| Local clusters | Two `kind` clusters (`private`, `public`), separate kubeconfig contexts |
| Tests | `pytest` |
| Lint / format | `ruff` |
| CI | GitHub Actions |

## Wire contract

The **only** payload the orchestrator may send to the public worker is the
raw user query. The response carries a single canned/templated string. Both
sides are enforced by Pydantic models in `src/common/`:

```python
class PublicWorkerRequest(BaseModel):
    query: str

class PublicWorkerResponse(BaseModel):
    answer: str
```

The public worker's `/query` handler returns a fixed template, e.g.:

```python
PublicWorkerResponse(answer=f"public worker received: {request.query}")
```

The orchestrator's `/query` handler forwards the request unchanged and
returns the public worker's response unchanged — there is nothing else to
combine yet.

## Repo layout

```
src/
  orchestrator/        # runs in the PRIVATE cluster
    main.py            # FastAPI POST /query — forwards {"query": ...} to the public worker
  public/              # runs in the PUBLIC cluster
    main.py            # FastAPI POST /query — returns a canned PublicWorkerResponse
  common/
    models.py          # cross-boundary Pydantic wire models (see above)
tests/
  unit/                # mirrors src/: src/foo/bar.py → tests/unit/foo/test_bar.py
  integration/
    boundary/          # fake public worker; assert only {"query": ...} crosses; runs in CI
    e2e/               # real kind clusters; manual only (make test-e2e)
manifests/
  private/             # YAML for the private kind cluster (orchestrator Deployment + Service)
  public/              # YAML for the public kind cluster (public-worker Deployment + Service)
docker/
  private/             # Dockerfile: orchestrator only
  public/              # Dockerfile: public worker only
specs/
```

## Cross-cluster networking

Both clusters run as separate `kind` clusters on the same Docker network.
`kind` doesn't provide cross-cluster DNS, so the public worker is exposed via
a `NodePort` Service and the orchestrator reaches it through a `hostAliases`
entry pointing at the public cluster's node IP — patched in after both
clusters are up (the same approach the archived prototype on
`archive/v1-original` used, since this is genuine `kind` plumbing rather than
incidental complexity).

## Makefile targets

```
make clusters-up      # spin up both kind clusters
make clusters-down    # tear down both kind clusters
make build            # build both Docker images
make load-images      # load images into the kind clusters
make deploy           # apply manifests to both clusters; patch hostAliases
make test             # lint + unit + boundary tests (mirrors CI)
make test-e2e         # full end-to-end against live clusters (manual only)
make dev              # clusters-up + build + load-images + deploy in one shot
```

## CI (GitHub Actions)

Two jobs run on every push; e2e is excluded from CI:

| Job | Command |
|---|---|
| `lint-and-unit` | `ruff check . && ruff format --check . && pytest tests/unit/ -q` |
| `boundary` | `pytest tests/integration/boundary/ -q` |

## Testing conventions

- Unit tests mirror `src/` under `tests/unit/`.
- Boundary tests use a fake public worker that records every inbound request;
  assert that only `{"query": "..."}` was received. See
  `.claude/skills/trust-boundary/SKILL.md` for ready-made assertions. Even
  though V1 has no private data, this test fixes the contract shape that V3+
  must continue to satisfy.
- E2E tests (`tests/integration/e2e/`) require live `kind` clusters and run
  via `make test-e2e`.
