# Project: Hybrid Cloud Agents — incremental POC

## Long-term vision

A drag-and-drop **agent builder focused on infrastructure**: a tool for
visually composing what gets deployed on a **private (on-prem)** cluster
versus a **public (cloud)** cluster — which services, which agents, which data
sources. The concrete starting point is a single hardcoded example of the kind
of system the builder would let you compose: an agent that answers questions
using both public and private data while guaranteeing private data never
leaves the private cluster.

The project is developed as a series of versioned prototypes, each adding
exactly one major piece on top of the last. See [`specs/index.md`](../specs/index.md)
for the full roadmap. Significant decisions and their rationale are logged in
[`DECISIONS.md`](../DECISIONS.md).

**Current version spec: [`specs/v2-spec.md`](../specs/v2-spec.md)**

When a new version starts, a new spec file is added (`specs/v2-spec.md`, …)
and this pointer is updated. Previous specs are kept for reference.

## The one invariant that must never break: the one-way membrane

The trust boundary is **asymmetric**. Read `.claude/skills/trust-boundary/SKILL.md`
before touching the orchestrator or the public worker.

- Public → private may flow freely (public docs, public search results, public answers).
- Private → public must **never** flow, with exactly **one** exception: the raw user query.
- Therefore the only thing the orchestrator may send outward is the query string.
  Private documents, private embeddings, private chunks, and any answer grounded
  in private text must never be passed to the public worker.

Any change to cross-cluster code requires a test that asserts this. Treat a
boundary violation as a release blocker, not a warning. As of V1 this is a
trivial contract on an empty system; it becomes meaningful starting at V3 once
private data exists (see `specs/v3-spec.md`).

## Request flow (V1–V2)

1. Ingest — orchestrator (private) receives the query.
2. Forward — orchestrator sends **only the query** to the public worker over
   mutual TLS (mTLS); gets back a canned response.
3. Return — the response is returned to the user inside the private
   environment.

This flow gains steps as later versions land (private retrieval in V3, public
retrieval in V4, local synthesis in V5) — see `specs/index.md` for the full
sequence. Each `vN-spec.md` documents the request flow for that version.

## Branching strategy

Three branch types:

- **`main`** — always a clean, working milestone. Corresponds to a completed
  `specs/vN-spec.md`.
- **`dev`** — integration branch for current work.
- **`feat/*`** — one branch per logical change.

Promotion flow:

- `feat/*`: commit + push after every logical change (work stays backed up on
  GitHub continuously).
- `feat/*` → `dev`: direct merge once tests pass on the feature branch.
  Squash messy WIP history; regular merge if commits are already clean
  Conventional Commits.
- `dev` → `main`: direct merge only at milestone boundaries — a `vN-spec.md`
  is fully implemented and `make test` + `make test-e2e` are green. This
  merge is the "release" of that version.

No PRs — solo project, direct merges. Test gating (the Stop hook running
`uv run pytest -q`) applies at every commit, regardless of branch.

## Development loop (follow this; it minimises manual approvals)

For each logical change, on a `feat/*` branch:

1. Implement the change in `src/`.
2. **Delegate test authoring to the `test-author` subagent.** Hand it the
   working-tree diff so it scopes itself to what changed (it does not re-scan
   the repo). Example instruction when delegating: *"Update tests for the
   uncommitted changes only. Here is the diff: <output of `git diff HEAD`>."*
3. Run the suite (`uv run pytest -q`). The Stop hook also enforces this — it
   blocks finishing while tests are red and feeds you the failures.
4. Run **`/simplify`** on the diff (reuse, simplification, efficiency,
   altitude cleanups) and re-run the suite if it made changes.
5. When green, commit using **Conventional Commits** (see below). The
   commit-message hook will reject non-conforming messages.
6. **Push immediately after every commit** (`git push`). Never leave commits
   sitting locally. The push and the commit are a single atomic step.
7. Build/deploy the docs (`mkdocs build`).
8. Continue to the next change. When the feature is complete and tests pass,
   merge `feat/*` → `dev` (see Branching strategy above). Before merging
   `dev` → `main`, run both the `code-reviewer` subagent (redundancy, bugs,
   boundary leaks) and the `spec-compliance` subagent (does the repo actually
   fulfil the active `vN-spec.md`).
9. **Before `dev` → `main`, update top-level docs to match the
   just-completed version** — this merge is the "release" of `vN`, and these
   files are the user-facing record of what's current:
   - `README.md` — `## Status`, the architecture section/diagram, and the
     "Stack and why" bullets affected by this version's changes.
   - `specs/index.md` — the "Current version" pointer.
   - `.claude/CLAUDE.md` — the "Current version spec" pointer and the
     "Request flow" section.
   Commit these doc updates (`docs: ...`) as part of the milestone merge, not
   left for a later session.

Only stop and ask the human when you hit something you cannot resolve — a
missing credential, a permission you were not granted, or a genuinely ambiguous
design decision. Routine edits, tests, commits, pushes, and doc builds are pre-approved.

## Conventional Commits

`type(scope): subject` — types: feat, fix, docs, style, refactor, perf, test,
build, ci, chore, revert. Scope is optional but prefer the module
(`orchestrator`, `private`, `public`, `common`). Examples:
`feat(orchestrator): add parallel private retrieval node`,
`test(public): assert only the query crosses the boundary`.
