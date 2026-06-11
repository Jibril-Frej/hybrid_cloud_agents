# V3 Spec — Private retrieval

V3 adds a local Chroma vector store on the **private** side only. This is the
first version where the one-way membrane boundary test becomes meaningful:
private content now exists, and the test must prove it never crosses outward.

## Adds on top of V2

- `data/private/` — synthetic private documents (git-tracked).
- `src/private/ingest.py` — seeds `data/private/` into a private Chroma index
  (dense retrieval, `all-MiniLM-L6-v2` ONNX embeddings).
- `src/orchestrator/retriever.py` — queries the private Chroma index for the
  incoming query; runs entirely inside the private cluster.
- The orchestrator's `/query` handler now does two things for each request:
  1. sends `{"query": ...}` to the public worker (unchanged from V1/V2) and
     gets back its canned `PublicWorkerResponse`;
  2. retrieves the top private chunks locally.
- The final answer combines both, e.g.:

  ```python
  PublicWorkerResponse  # from the public worker, unchanged
  private_chunks        # retrieved locally, never sent anywhere

  answer = f"{public_response.answer} | private context: {private_chunks}"
  ```

  This is still templated, not LLM-generated — synthesis arrives in V5.

## Wire contract

Unchanged from V1/V2 — still just `{"query": "..."}` out, canned
`PublicWorkerResponse` back.

## Tests

- **Boundary test (now meaningful):** seed the private index with a document
  containing a unique marker string. Send a query that would retrieve it.
  Assert the request sent to the public worker is still exactly
  `{"query": "..."}` and that the marker string never appears anywhere in
  the outbound payload.
- Unit tests for `src/private/ingest.py` and `src/orchestrator/retriever.py`.

## Repo additions

```
data/
  private/             # synthetic private documents (git-tracked)
src/
  private/
    ingest.py
  orchestrator/
    retriever.py
```
