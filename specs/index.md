# Hybrid Cloud Agents

## Long-term vision

A drag-and-drop **agent builder focused on infrastructure**: a tool where a
user visually composes what gets deployed on a **private (on-prem)** cluster
versus a **public (cloud)** cluster — which services, which agents, which data
sources — and the tool generates and applies the corresponding Kubernetes
manifests.

The concrete starting point for that vision is a single hardcoded example of
the kind of system the builder would eventually let you compose: a hybrid
agent that answers questions using both public and private data while
guaranteeing that **private data never leaves the private cluster**, with
exactly one exception — the raw user query may cross outward.

## How this project is developed

The project is built as a series of versioned prototypes, each adding exactly
one major piece on top of the last so that failures are easy to localize.
Every version has its own spec file (`v1-spec.md`, `v2-spec.md`, …); the
previous specs are kept for reference. Significant decisions and their
rationale are logged in [`DECISIONS.md`](../DECISIONS.md).

**Current version: [`v3-spec.md`](v3-spec.md)**

## Roadmap

| Version | Adds | Proves |
|---|---|---|
| [V1](v1-spec.md) | Two `kind` clusters, plain HTTP, query → canned response | The topology works; the "only the query crosses" contract is testable |
| [V2](v2-spec.md) | mTLS on the V1 plumbing | Transport hardening, no app-logic change |
| [V3](v3-spec.md) | Private retrieval (Chroma + embeddings, private side only) | Private data can be used locally without crossing the boundary — the boundary test becomes meaningful |
| [V4](v4-spec.md) | Public retrieval (Chroma + embeddings, public side) | Both sides retrieve; public context crosses inward |
| [V5](v5-spec.md) | LangGraph + local LLM synthesis | Public + private context combined into a real answer — original V1 functionality, on a proven foundation |
| [V6+](v6-spec.md) | Declarative "what's deployed where" config, then a UI | First step toward the drag-and-drop builder |

## The one invariant that must never break: the one-way membrane

The trust boundary is **asymmetric**.

- Public → private may flow freely (public docs, public search results, public answers).
- Private → public must **never** flow, with exactly **one** exception: the raw user query.

This is enforced from V1 (where it's a trivial contract on an empty system)
and becomes meaningful starting at V3, once private data actually exists.
See `.claude/skills/trust-boundary/SKILL.md` before touching cross-cluster
code.
