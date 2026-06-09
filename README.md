# Hybrid Cloud Agents

A proof-of-concept LangGraph agent that answers questions by combining **public** (cloud) and **private** (on-prem) knowledge, while enforcing a hard guarantee: **nothing derived from private data ever leaves the private cluster**.

## How it works

The system splits across two Kubernetes clusters — a private on-prem cluster that owns all sensitive data and runs the final LLM, and a public cloud cluster that handles public-document retrieval only.

```
User
 │
 ▼
POST /query  ← private cluster (orchestrator)
 │
 ├─ sends only {"query": "..."}  ──────────────────► public cluster
 │                                                     retrieves public docs
 │                                                     summarizes them locally
 │◄──────────────── {"summary": "..."}  ◄─────────────┘
 │
 ├─ retrieves private docs locally (never leaves)
 │
 └─ local Qwen model synthesizes answer
        using public summary + private chunks
 │
 ▼
Answer returned to user (inside private cluster)
```

The trust boundary is **asymmetric and one-way**: public context flows freely into the private cluster; private content never flows out. The only thing the orchestrator sends to the public cluster is the raw query string — enforced by a Pydantic wire contract and verified by dedicated boundary tests.

## Architecture

| Concern | Choice |
|---|---|
| Language | Python 3.11+ |
| Orchestration | LangGraph (`StateGraph` with fork-join parallel branches) |
| Retrieval | Chroma dense retrieval, `all-MiniLM-L6-v2` ONNX embeddings |
| Generation | `Qwen2.5-0.5B-Instruct` via HuggingFace `transformers` (CPU) |
| Public worker API | FastAPI |
| Cross-cluster transport | Single HTTPS endpoint over **mTLS** (self-signed CA) |
| Packaging | Docker images + plain Kubernetes YAML manifests |
| Local clusters | Two `kind` clusters (`private`, `public`) |

### Graph topology

```
receive_query → [public_retrieve ‖ private_retrieve] → synthesize → return_answer
```

`public_retrieve` and `private_retrieve` run as parallel LangGraph branches. The synthesizer node waits for both branches before calling the local model.

### Wire contract

The Pydantic models in `src/common/models.py` are the single source of truth for what may cross the boundary:

```python
class PublicWorkerRequest(BaseModel):
    query: str                 # the only thing sent outward

class PublicWorkerResponse(BaseModel):
    summary: str               # the only thing received back
```

### Repository layout

```
src/
  orchestrator/        # runs in the PRIVATE cluster
    main.py            # FastAPI POST /query endpoint
    graph.py           # LangGraph graph with four nodes
    retriever.py       # private Chroma retrieval
    synthesizer.py     # local Qwen synthesis (always runs here)
  private/
    ingest.py          # seeds data/private/ into private Chroma
  public/              # runs in the PUBLIC cluster
    main.py            # FastAPI POST /retrieve endpoint
    retriever.py       # public Chroma retrieval
    summarizer.py      # Qwen chunk summarization
    ingest.py          # seeds data/public/ into public Chroma
  common/
    models.py          # cross-boundary Pydantic wire models
tests/
  unit/                # mirrors src/ layout
  integration/
    boundary/          # fake public worker; asserts only query crosses
    e2e/               # live kind clusters (manual only)
manifests/
  private/             # Kubernetes YAML for the private cluster
  public/              # Kubernetes YAML for the public cluster
docker/
  private/             # Dockerfile: orchestrator + private retrieval + Qwen
  public/              # Dockerfile: public worker + Qwen summarizer
certs/
  gen-certs.sh         # generates self-signed CA, certs, and keys for mTLS
data/
  private/             # synthetic private documents (git-tracked)
  public/              # synthetic public documents (git-tracked)
docs/                  # MkDocs API reference (mkdocstrings)
```

## Prerequisites

- Python 3.11+
- [Docker](https://docs.docker.com/get-docker/)
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- `openssl` (for certificate generation)

## Installation

```bash
git clone https://github.com/Jibril-Frej/hybrid_cloud_agents.git
cd hybrid_cloud_agents

# create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# install runtime + dev dependencies
pip install -e ".[dev]"
```

## Running the test suite

```bash
# lint, format check, unit tests, and boundary tests
make test

# or individually:
ruff check . && ruff format --check .
pytest tests/unit/ tests/integration/boundary/ -q
```

## Full local deployment (two kind clusters)

The `make dev` target runs every setup step in order. Run it once on a fresh checkout to get a working two-cluster environment:

```bash
make dev
```

This is equivalent to running the following steps individually:

```bash
# 1. spin up both kind clusters
make clusters-up

# 2. generate mTLS certificates (self-signed CA)
make certs

# 3. push certs into each cluster as Kubernetes Secrets
make load-certs

# 4. seed both Chroma indexes from data/
make seed

# 5. build Docker images
make build

# 6. load images into kind (bypasses a registry)
make load-images

# 7. apply Kubernetes manifests
make deploy
```

## Querying the orchestrator

The orchestrator exposes `POST /query` inside the private cluster. Forward the port to reach it from your laptop:

```bash
kubectl --kubeconfig kubeconfig-private.yaml port-forward svc/orchestrator 8080:8080
```

Then send a query:

```bash
curl -s -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the incident response procedure?"}' | jq .
```

Expected response shape:

```json
{
  "answer": "..."
}
```

## End-to-end tests

E2E tests require live `kind` clusters and are excluded from CI. Run them manually after `make dev`:

```bash
make test-e2e
```

## Tearing down

```bash
make clusters-down
```

## API reference (docs)

Build and serve the MkDocs API reference locally:

```bash
mkdocs serve
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Roadmap

Improvements deferred from V1:

- **Query rewriting** — add a pre-retrieval node that reformulates the user query for better recall (e.g. HyDE or a small rewriter model).
- **Hybrid retrieval tuning** — tune the dense encoder for the domain; add reciprocal rank fusion.
- **Larger generation model** — swap `Qwen2.5-0.5B-Instruct` for a larger model once the pipeline is validated end-to-end.
- **Certificate rotation** — automate mTLS cert rotation (e.g. via cert-manager) instead of relying on static self-signed certs.
- **Observability** — structured logging and a Prometheus metrics endpoint on both workers.
