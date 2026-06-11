# V4 Spec — Public retrieval

V4 mirrors V3 on the public side: the public worker gets its own Chroma index
and retrieves relevant chunks for the incoming query, instead of returning a
fixed canned response.

## Adds on top of V3

- `data/public/` — synthetic public documents (git-tracked).
- `src/public/ingest.py` — seeds `data/public/` into a public Chroma index
  (same embedding setup as the private side).
- `src/public/retriever.py` — queries the public Chroma index for the
  incoming query.
- The public worker's `/query` handler now retrieves matching public chunks
  and returns them (still no LLM — return the matched chunk text directly or
  a simple join), e.g.:

  ```python
  PublicWorkerResponse(answer="\n".join(chunk.text for chunk in matches))
  ```

- The orchestrator combines the public worker's response with its own private
  chunks, same templated combination as V3.

## Wire contract

Unchanged shape (`{"query": "..."}` out, `{"answer": "..."}` back) — only the
*content* of `PublicWorkerResponse.answer` changes, from a fixed template to
retrieved public chunk text.

## Tests

- Unit tests for `src/public/ingest.py` and `src/public/retriever.py`.
- Boundary test from V3 continues to apply unchanged — the private marker
  must still never appear in the outbound request, regardless of what the
  public worker now does with the query.

## Repo additions

```
data/
  public/              # synthetic public documents (git-tracked)
src/
  public/
    ingest.py
    retriever.py
```
