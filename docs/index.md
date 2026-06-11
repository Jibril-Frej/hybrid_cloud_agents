# Hybrid Cloud Agents

A proof-of-concept for a drag-and-drop **agent builder focused on
infrastructure** — a tool for composing what gets deployed on a **private
(on-prem)** cluster versus a **public (cloud)** cluster, while guaranteeing
that **private data never leaves the private cluster** (with exactly one
exception: the raw user query).

The project is built incrementally as a series of versioned prototypes. See
[`specs/index.md`](https://github.com/Jibril-Frej/hybrid_cloud_agents/blob/main/specs/index.md)
for the long-term vision and the full roadmap, and
[`specs/v1-spec.md`](https://github.com/Jibril-Frej/hybrid_cloud_agents/blob/main/specs/v1-spec.md)
for the current version.

## V1 — minimal two-cluster plumbing

V1 proves the basic topology: two `kind` clusters (`private`, `public`)
connected by a single plain-HTTP call. The orchestrator (private) forwards
the raw user query to the public worker (public), which returns a canned
response, unchanged back to the user. See the [API Reference](reference/common.md)
for the wire contract and service implementations.

## Running it locally

```console
$ make dev          # spin up both kind clusters, build images, deploy
$ make test         # lint + unit + boundary tests
$ make test-e2e     # end-to-end test against the live clusters
$ make clusters-down
```
