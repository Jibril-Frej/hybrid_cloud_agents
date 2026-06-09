# Hybrid Cloud Agents

A POC for deploying AI agents in a hybrid cloud environment where **nothing derived from private data may leave private nodes**.

## Architecture

A LangGraph agent answers questions using both public (cloud) and private (on-prem) data:

```
receive_query → [public_retrieve ‖ private_retrieve] → synthesize → return_answer
```

- **Public retrieval** — orchestrator sends only the raw query to the public worker; gets a public-context summary back.
- **Private retrieval** — orchestrator queries the local Chroma index; private chunks never leave the private cluster.
- **Synthesis** — the local `Qwen2.5-0.5B-Instruct` model merges both contexts and generates the answer entirely on-premises.

## The one invariant

Private data must never flow outward. The only thing that crosses the boundary is the raw user query string.

## Roadmap

Improvements deferred from the V1 prototype:

- **Query rewriting** — pre-retrieval node that reformulates the query for better recall (HyDE or a small rewriter model).
- **Hybrid retrieval tuning** — domain-finetuned encoder; reciprocal rank fusion for the merge step.
- **Larger generation model** — swap `Qwen2.5-0.5B-Instruct` for a larger model once the pipeline is validated end-to-end.
- **Certificate rotation** — automate mTLS cert rotation via cert-manager.
- **Observability** — structured logging and a Prometheus metrics endpoint on both workers.
