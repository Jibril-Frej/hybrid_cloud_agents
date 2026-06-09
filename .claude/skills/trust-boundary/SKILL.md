---
name: trust-boundary
description: Read this whenever writing, changing, testing, or reviewing anything that crosses between the private (on-prem) and public (cloud) clusters — the orchestrator, the public RAG worker, the cross-cluster HTTPS call, or any code that decides what data leaves the private environment. Defines the one-way membrane invariant and gives ready-made test assertions.
---

# The one-way membrane

The private and public clusters form an asymmetric trust boundary.

- **Public -> private: allowed.** Public documents, public search results, and
  public-grounded answers may enter the private environment freely.
- **Private -> public: forbidden,** with exactly one exception: the **raw user
  query** may be sent outward.

So the only payload the orchestrator may send to the public worker is the query
string. The following must NEVER cross outward:

- private documents or any private text/chunks
- private embeddings or the private index
- the final answer (it is grounded in private text)
- any derived value that could leak private content (scores tied to private
  chunks, private metadata, filenames, etc.)

The synthesis step sees private text, so it MUST run on the local model inside
the private cluster. It can never be delegated to the public LLM.

## Verification checklist (use in review and tests)

1. The outbound call carries only the query — inspect the exact request body.
2. No private object (document, chunk, embedding, index handle) is reachable
   from the code path that builds the outbound request.
3. Synthesis runs locally; the public LLM is never called with private context.
4. Errors/timeouts on the public side degrade gracefully and still never echo
   private data in logs or responses sent outward.

## Ready-made test assertions

Use a fake public worker that records everything it receives, then assert on it:

```python
def test_only_query_crosses_the_boundary(orchestrator, fake_public_worker):
    private_docs = seed_private_index("SECRET-PRIVATE-MARKER")
    orchestrator.answer("what is the policy?")

    # Exactly one outbound call, carrying only the query.
    assert len(fake_public_worker.received) == 1
    sent = fake_public_worker.received[0]
    assert sent == {"query": "what is the policy?"}

    # No private content ever appears in anything sent outward.
    blob = repr(fake_public_worker.received)
    assert "SECRET-PRIVATE-MARKER" not in blob
```

```python
def test_synthesis_uses_local_model_only(orchestrator, spy_public_llm, spy_local_llm):
    orchestrator.answer("hybrid question")
    assert spy_local_llm.called          # private/local model generated the answer
    assert not spy_public_llm.generated  # public LLM never produced the final answer
```

Adapt names to the real interfaces, but keep the two guarantees: only the query
goes out, and synthesis is local.
