# Project: Hybrid Cloud Agents — incremental POC

A LangGraph agent answers questions using both public (cloud) and private
(on-prem) data, while guaranteeing that private data never leaves the premises.
The project is developed as a series of versioned prototypes.

**Current version spec: [`docs/v1-spec.md`](../docs/v1-spec.md)**
When a new version starts, a new spec file is added (`docs/v2-spec.md`, …) and
this pointer is updated. The previous spec is kept for reference.

## The one invariant that must never break: the one-way membrane

The trust boundary is **asymmetric**. Read `.claude/skills/trust-boundary/SKILL.md`
before touching the orchestrator or the public worker.

- Public → private may flow freely (public docs, public search results, public answers).
- Private → public must **never** flow, with exactly **one** exception: the raw user query.
- Therefore the only thing the orchestrator may send outward is the query string.
  Private documents, private embeddings, private chunks, and any answer grounded
  in private text must never be passed to the public worker.

Any change to cross-cluster code requires a test that asserts this. Treat a
boundary violation as a release blocker, not a warning.

## Request flow (every query is hybrid)

1. Ingest — orchestrator (private) receives the query.
2. Public retrieval — orchestrator sends **only the query** to the public worker; gets public context back.
3. Private retrieval — orchestrator retrieves private chunks locally, in parallel. Never leaves the private cluster.
4. Synthesis — the **local** model answers using public + private context (runs locally because it sees private text).
5. Return — answer returned to the user inside the private environment.

## Development loop (follow this; it minimises manual approvals)

For each logical change:

1. Implement the change in `src/`.
2. **Delegate test authoring to the `test-author` subagent.** Hand it the
   working-tree diff so it scopes itself to what changed (it does not re-scan
   the repo). Example instruction when delegating: *"Update tests for the
   uncommitted changes only. Here is the diff: <output of `git diff HEAD`>."*
3. Run the suite (`python -m pytest -q`). The Stop hook also enforces this — it
   blocks finishing while tests are red and feeds you the failures.
4. When green, commit using **Conventional Commits** (see below). The
   commit-message hook will reject non-conforming messages.
5. **Push immediately after every commit** (`git push`). Never leave commits
   sitting locally. The push and the commit are a single atomic step.
6. Build/deploy the docs (`mkdocs build`).
7. Continue to the next change. Run the `code-reviewer` subagent at the end of a
   milestone (or when asked) to catch redundancy, bugs, and boundary leaks.

Only stop and ask the human when you hit something you cannot resolve — a
missing credential, a permission you were not granted, or a genuinely ambiguous
design decision. Routine edits, tests, commits, pushes, and doc builds are pre-approved.

## Conventional Commits

`type(scope): subject` — types: feat, fix, docs, style, refactor, perf, test,
build, ci, chore, revert. Scope is optional but prefer the module
(`orchestrator`, `private`, `public`, `common`). Examples:
`feat(orchestrator): add parallel private retrieval node`,
`test(public): assert only the query crosses the boundary`.
