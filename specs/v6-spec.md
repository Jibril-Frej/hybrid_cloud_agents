# V6+ — Toward the agent builder (direction, not yet a detailed spec)

Once V5 reproduces the original hybrid-agent functionality on a proven
foundation, the project starts moving toward its long-term goal: a
drag-and-drop builder focused on infrastructure — what gets deployed on the
private vs. public cluster.

This is intentionally sketched at a high level rather than fully specced; a
detailed `v6-spec.md` (and v7, …) will be written once V5 is done and we can
see what generalizes cleanly.

## Likely direction

- **Declarative deployment config** — a YAML/JSON file describing "what's
  deployed where": which services/agents run on the private cluster, which
  on the public cluster, what data sources each has access to. V1–V5's
  hardcoded two-pod topology becomes the first thing this config can describe.
- **Config-driven manifests** — manifests for both clusters are generated
  from that config rather than hand-written.
- **UI** — a drag-and-drop interface for editing the config, with the
  one-way membrane invariant enforced as a structural constraint the UI
  can't violate (e.g., it's impossible to draw an edge from a private node to
  a public node except the designated query-only edge).
- **Multiple agents/services** — generalize beyond a single
  orchestrator/public-worker pair to arbitrary user-defined components per
  cluster.

## What stays constant

The one-way membrane invariant (private → public forbidden except the raw
query) remains the non-negotiable constraint the builder is designed around —
it's the reason the builder needs an "infrastructure" focus in the first
place: it's a tool for composing systems that respect this boundary by
construction.
