# V1 Spec — RAG over public + private documents

A LangGraph agent answers questions using **public** data (on a public/cloud
cluster) and **private** data (on an on-prem cluster), while guaranteeing that
private data never leaves the premises. V1 runs on a single laptop with the two
clusters simulated locally using two `kind` clusters.

## Stack

| Concern | Choice |
|---|---|
| Language | Python 3.11+ |
| Orchestration | LangGraph (graph runs in the **private** cluster) |
| Retrieval | Chroma BM25 (separate indexes per cluster; no dense embeddings in V1) |
| Generation | `Qwen2.5-0.5B-Instruct` via `transformers` (CPU) |
| Public worker framework | FastAPI |
| Cross-cluster link | Single HTTPS endpoint over **mTLS** (self-signed CA; certs as K8s Secrets) |
| Packaging | Docker images + plain YAML manifests |
| Local clusters | Two `kind` clusters (`private`, `public`), separate kubeconfig contexts |
| Tests | `pytest` |
| Lint / format | `ruff` |
| CI | GitHub Actions (see below) |

## Wire contract

The **only** payload the orchestrator may send to the public worker is the raw user query.
The response carries a single summarized string of public context. Both sides are enforced
by Pydantic models in `src/common/`:

```python
class PublicWorkerRequest(BaseModel):
    query: str

class PublicWorkerResponse(BaseModel):
    summary: str
```

## Repo layout

```
src/
  orchestrator/        # runs in the PRIVATE cluster
    main.py            # FastAPI /query endpoint (ClusterIP; reached via kubectl port-forward)
    graph.py           # LangGraph graph definition and nodes
    retriever.py       # private Chroma BM25 retrieval
    synthesizer.py     # local Qwen inference (synthesis ALWAYS runs here)
  private/
    ingest.py          # seeds data/private/ into Chroma
  public/              # public RAG worker (mTLS HTTPS endpoint)
    main.py            # FastAPI app
    retriever.py       # public Chroma BM25 retrieval
    summarizer.py      # Qwen chunk summarization (NEVER synthesis)
    ingest.py          # seeds data/public/ into Chroma
  common/              # cross-boundary wire types only (see above)
tests/
  unit/                # mirrors src/: src/foo/bar.py → tests/unit/foo/test_bar.py
  integration/
    boundary/          # fake public worker; assert only query crosses; runs in CI
    e2e/               # real kind clusters; manual only (make test-e2e)
manifests/
  private/             # YAML for the private kind cluster
  public/              # YAML for the public kind cluster
certs/                 # openssl script + CA/cert/key pairs (gitignore *.pem; track the script)
data/
  private/             # synthetic private documents (gittracked)
  public/              # synthetic public documents (gittracked)
docker/
  private/             # Dockerfile: orchestrator + private retrieval + Qwen
  public/              # Dockerfile: public RAG worker + Qwen summarizer
docs/
```

## LangGraph graph

Four nodes; public and private retrieval run in parallel:

```
receive_query → [public_retrieve ‖ private_retrieve] → synthesize → return_answer
```

- `public_retrieve` — sends only the query over mTLS; receives `PublicWorkerResponse.summary`.
- `private_retrieve` — queries local Chroma; private chunks never leave the private cluster.
- `synthesize` — merges public summary + private chunks; calls local Qwen; always runs locally.

## Makefile targets

```
make clusters-up      # spin up both kind clusters
make clusters-down    # tear down both kind clusters
make certs            # generate CA + cert/key pairs for mTLS
make seed             # ingest data/ corpus into both Chroma indexes
make build            # build both Docker images
make deploy           # apply manifests to both clusters
make test             # lint + unit + boundary tests (mirrors CI)
make test-e2e         # full end-to-end against live clusters (manual only)
make dev              # clusters-up + certs + seed + deploy in one shot
```

## CI (GitHub Actions)

Two jobs run on every push; e2e is excluded from CI:

| Job | Command |
|---|---|
| `lint-and-unit` | `ruff check . && ruff format --check . && pytest tests/unit/ -q` |
| `boundary` | `pytest tests/integration/boundary/ -q` |

## Testing conventions

- Unit tests mirror `src/` under `tests/unit/`.
- Boundary tests use a fake public worker that records every inbound request; assert that
  only `{"query": "..."}` was received and no private marker appears anywhere in the payload.
  See `.claude/skills/trust-boundary/SKILL.md` for ready-made assertions.
- Every change to `src/orchestrator/` or `src/public/` must add or update a boundary test.
- E2E tests (`tests/integration/e2e/`) require live `kind` clusters and run via `make test-e2e`.
