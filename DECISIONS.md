# Decisions Log

Append-only record of significant project decisions: what was decided, why,
and what alternatives were considered. Newest entries at the top.

---

## 2026-06-11 — Use `uv` for Python environment/dependency management

**Decision:** V1 (and onward) uses `uv` instead of plain `venv` + `pip` —
`uv venv` to create the environment, `uv sync` to install from `uv.lock`.
Recorded in `specs/v1-spec.md`'s stack table.

**Why:** `.claude/settings.json` already pre-approves `uv --version` and
`uv lock *`, and the project previously experimented with `uv` for Docker
dependency installs (before reverting to `requirements.txt` for layer
caching) — there's already precedent. `uv` is fast enough that rebuilding the
environment from scratch stops being a cost worth avoiding, which matters for
a project whose dependency set changes from version to version. It also
produces a lockfile (`uv.lock`) for reproducibility, unlike bare `venv`+`pip`.

**Alternatives considered:** `venv` + `pip` (no lockfile, slow installs);
Poetry (mature, but slower than `uv` and a non-standard lock format); conda
(overkill — no non-Python binary deps needed).

---

## 2026-06-11 — Executed the reset: `archive/v1-original` branch + new `main`

**Decision:** Created `archive/v1-original` from the pre-reset `main` HEAD
(commit `4e4df09`) and pushed it. On `main`, removed the full V1 prototype
(`src/`, `tests/`, `manifests/`, `docker/`, `certs/`, `data/`, `docs/`,
`pyproject.toml`, `requirements.txt`, `Makefile`, `.github/workflows/ci.yml`)
and added the new minimal-V1 scaffold: rewritten `CLAUDE.md` (vision, V1
request flow, branching strategy), rewritten `README.md`, and `specs/`
(`index.md`, `v1-spec.md` … `v6-spec.md`).

**Why:** Implements the V1 redefinition, branching strategy, and roadmap
decided above. `main`'s ref was not moved/force-pushed — this is a normal new
commit on top of the existing history, so all prior commits remain reachable
both via `main`'s ancestry and via `archive/v1-original`.

**Status:** `main` currently has no Python project at all (no `pyproject.toml`,
no `src/`). The next step is a `feat/v1-minimal-plumbing` branch that builds
the V1 scaffold described in `specs/v1-spec.md` from scratch (new
`pyproject.toml` with minimal deps, `src/orchestrator`, `src/public`,
`src/common`, `tests/`, `manifests/`, `docker/`, `Makefile`, CI).

---

## 2026-06-11 — Incremental roadmap V1–V6+

**Decision:** Adopt this version sequence, each reintroducing one major piece
on top of the previous, independently testable:

- **V1**: two kind clusters, plain HTTP, query → canned response (topology +
  "only the query crosses" contract).
- **V2**: reintroduce mTLS on the V1 plumbing (transport hardening only).
- **V3**: private retrieval — Chroma + embeddings on the private side only.
  First version where the boundary test becomes meaningful.
- **V4**: public retrieval — Chroma + embeddings on the public side too.
- **V5**: local synthesis — LangGraph + local LLM combining public + private
  context (roughly "V1-original" functionality, on a proven foundation).
- **V6+**: toward the agent-builder vision — declarative "what's deployed
  where" config, then a UI. Sketched loosely in specs, not detailed yet.

**Why:** Each version adds exactly one major dependency/concern, so failures
are easy to localize — directly addressing "v1 became complex too fast and we
didn't think through dependencies."

**Alternatives considered:** merging V3+V4 into one "retrieval" version
(rejected — keeping private and public retrieval as separate steps lets the
boundary test be introduced and proven before the public side is added).

---

## 2026-06-11 — V1 drops mTLS; plain HTTP across clusters

**Decision:** No mTLS in V1. Cross-cluster calls use plain HTTP over the kind
Docker network. The one-way membrane invariant ("only the query crosses") is
enforced and tested at the application/contract level (request body shape),
not via transport encryption.

**Why:** Cert generation, secret distribution, and volume mounts (`certs/gen-
certs.sh`, `make load-certs`, per-pod cert mounts) are exactly the kind of
extra moving part that's hard to debug and was contributing to V1's
complexity. mTLS is a self-contained, additive increment for a later version
("harden the transport") once the basic topology is solid.

**Alternatives considered:** keep mTLS from V1 (rejected — the membrane's
core concern per `CLAUDE.md` is *what data* crosses, not *how it's
encrypted*; transport security is separable and can be layered on later).

---

## 2026-06-11 — V1 is pure plumbing: no LLM, no RAG, no vector DB

**Decision:** V1's application is minimal HTTP services only — orchestrator
(private) forwards a query string to the public worker, public worker returns
a canned/templated response, orchestrator returns it. Dependencies limited to
something like `fastapi` + `uvicorn` + `httpx`. No LangGraph, no Chroma, no
ingest step, no model downloads.

**Why:** Goal is a system that's fast to deploy and fast to test/iterate on —
heavy deps (LLM downloads, Chroma ingest on every container start) were a
major source of V1's complexity and slow iteration. V1 should validate the
*topology* (two kind clusters, cross-cluster networking, build/load/deploy
pipeline, the one-way membrane contract) before any AI components are
reintroduced incrementally in v2+.

**Alternatives considered:** keep a trivial local LLM call without RAG
(rejected — still pulls in a model dependency before the basics are proven).

---

## 2026-06-11 — V1 is minimal/hardcoded; the agent-builder vision is future narrative only

**Decision:** The long-term vision (a drag-and-drop agent builder for defining
what's deployed on private/public clusters) becomes part of the project's
stated goal in the specs, but does **not** change V1's architecture. V1 stays
a fixed, hardcoded two-cluster system, redefined to be minimal. No declarative
config layer is introduced yet.

**Why:** The stated problem is that V1 grew complex too fast without thinking
through dependencies/tooling. Pulling builder/declarative-config concepts into
V1 now risks repeating that — get a boring, working two-cluster baseline
first, then build toward the vision incrementally in v2+.

**Alternatives considered:** Starting V1 with a declarative "what's deployed
where" config that a future UI would generate (rejected — adds complexity
before the basics are proven).

---

## 2026-06-11 — Branch promotion flow and push policy

**Decision:**
- `feat/*`: commit + push after every logical change (unchanged from today).
- `feat/*` → `dev`: direct merge once tests pass on the feature branch.
  Squash messy WIP history; regular merge if commits are already clean
  Conventional Commits.
- `dev` → `main`: direct merge only at milestone boundaries (a `vN-spec.md`
  is fully implemented and `make test` + `make test-e2e` are green). This
  merge represents the "release" of that version.
- Test gating (Stop hook running `python -m pytest -q`) applies at every
  commit, regardless of branch — no change from today.

**Why:** Solo project — PRs/self-review add ceremony without benefit. `main`
should always represent a clean, working, spec-complete milestone; `dev` is
where in-progress integration happens.

**Alternatives considered:** self-merged PRs as checkpoints (rejected — extra
ceremony, no second reviewer to benefit from it).

---

## 2026-06-11 — Branching strategy: `main` + `dev` + `feat/*` (no `staging`)

**Decision:** Adopt three branch types: `main` (clean, working milestones —
mirrors `docs/vN-spec.md`), `dev` (integration branch for current work),
and `feat/*` (per-change branches). No `staging` branch for now.

**Why:** This is a solo POC with no persistent staging environment — clusters
are spun up/torn down on demand via `make dev`. A `staging` branch would add
merge ceremony without a corresponding deployment target to validate against.

**Alternatives considered:** `main` + `staging` + `dev` + `feat/*` (rejected —
`staging` has no environment to gate yet; can be added later if a persistent
pre-prod cluster is introduced).

**Status:** Workflow details (push policy, promotion triggers feat→dev→main)
still to be written into `CLAUDE.md`.

---

## 2026-06-11 — Decision tracking: this file (`DECISIONS.md`)

**Decision:** Keep a lightweight, append-only decision log at the repo root.

**Why:** Needs to survive the planned `main` reset (so it can't live only in
chat history), and should sit next to `CLAUDE.md` where it'll be seen.

**Alternatives considered:** `docs/adr/` directory with one file per decision
(rejected as too much structure for a small POC at this stage).

---

## 2026-06-11 — Reset `main`, archive current code on a branch (not delete)

**Decision:** Instead of deleting git history (locally and on GitHub), archive
the current V1 codebase on a separate branch and reset `main` to a clean
baseline for the redefined, simpler V1.

**Why:** History has debugging value (e.g., the Dockerfile layer-caching fixes
contain real lessons). A soft reset gives a clean slate with zero risk and is
fully reversible, unlike a force-push history rewrite or repo deletion.

**Alternatives considered:** hard reset + force-push (discards V1 commits from
`main`'s history, recoverable only via GitHub support for ~90 days); delete
and recreate the GitHub repo (permanent, loses issues/stars too).

**Status:** Archive branch name and exactly what `main` gets reset *to* are
still to be decided — depends on the redefined V1 scope (open question).
