#!/usr/bin/env bash
# PostToolUse (matcher: Bash) — after a `git commit`, rebuild the docs site so
# it's never left stale (CLAUDE.md dev-loop step 6). No-ops if mkdocs.yml
# doesn't exist yet. Requires `jq`.
set -uo pipefail

input=$(cat)
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // ""')

case "$cmd" in
  *"git commit"*)
    cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
    [ -f mkdocs.yml ] || exit 0

    if output=$(uv run mkdocs build --strict 2>&1); then
      exit 0
    else
      reason=$(printf 'git commit succeeded, but `mkdocs build --strict` failed — fix the docs build:\n\n%s' "$output" | tail -c 4000)
      jq -n --arg r "$reason" '{decision:"block",reason:$r}'
      exit 0
    fi
    ;;
esac

exit 0
