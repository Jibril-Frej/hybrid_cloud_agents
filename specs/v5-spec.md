# V5 Spec — Local synthesis (LangGraph + LLM)

V5 replaces the templated string-concatenation from V3/V4 with a real
LangGraph agent that synthesizes an answer from public + private context
using a local LLM. This restores the original project's functionality, now
built on a foundation that's been proven incrementally (topology → transport
security → private retrieval → public retrieval).

## Adds on top of V4

- `src/orchestrator/graph.py` — LangGraph `StateGraph` with parallel
  retrieval branches:

  ```
  receive_query → [public_retrieve ‖ private_retrieve] → synthesize → return_answer
  ```

- `src/orchestrator/synthesizer.py` — local `Qwen2.5-0.5B-Instruct` (CPU, via
  `transformers`) merges the public worker's response and the private chunks
  into a generated answer. Synthesis always runs in the private cluster.
- The public worker may also use the local model to *summarize* its retrieved
  chunks before returning them (as in the original prototype) — but it never
  performs synthesis grounded in private content, since it never sees private
  content.

## Wire contract

Unchanged shape. `PublicWorkerResponse.answer` may now be an LLM-generated
summary of public chunks rather than raw chunk text.

## Reference implementation

The archived prototype on `archive/v1-original` already implements this
graph, synthesizer, and summarizer — it can be used as a starting point and
adapted to the cumulative V1–V4 codebase rather than rewritten from scratch.

## Tests

- `test_synthesis_uses_local_model_only` (see
  `.claude/skills/trust-boundary/SKILL.md`): the local model is called for
  synthesis; the public worker's model is never called with private context.
- Boundary test from V3 continues to apply unchanged.
- Unit tests for `graph.py` and `synthesizer.py`.

## Repo additions

```
src/
  orchestrator/
    graph.py
    synthesizer.py
  public/
    summarizer.py
```
