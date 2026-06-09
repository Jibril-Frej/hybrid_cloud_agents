# hybrid_cloud_agents
A POC for deploying AI Agents in a hybrid cloud environment where nothing derived from private data may leave private nodes.

## Roadmap

Improvements deferred from the V1 prototype:

- **Public worker graceful degradation** — if the public cluster is unreachable or times out, the orchestrator falls back to synthesizing with private-only context instead of failing the request.
- **Query rewriting** — add a pre-retrieval node that reformulates the raw user query for better retrieval recall (e.g. HyDE or a small rewriter model).
- **Hybrid retrieval tuning** — tune dense retrieval (e.g. a domain-finetuned encoder) and add reciprocal rank fusion for the merge step.
- **Larger generation model** — swap `Qwen2.5-0.5B-Instruct` for `Apertus-8B-Instruct-2509` once the pipeline is validated end-to-end.
- **Certificate rotation** — automate mTLS cert rotation (e.g. via cert-manager) rather than relying on a static self-signed CA.
- **Observability** — structured logging and a metrics endpoint (Prometheus) on both workers; trace the full request through both clusters.