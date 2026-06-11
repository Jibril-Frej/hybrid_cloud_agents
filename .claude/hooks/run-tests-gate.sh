#!/usr/bin/env bash
# Stop hook — block finishing while tests are red, and hand the failures back so
# the session fixes them. Guards against infinite loops via stop_hook_active.
# Requires `jq`.
set -uo pipefail

input=$(cat)
active=$(printf '%s' "$input" | jq -r '.stop_hook_active // false')
[ "$active" = "true" ] && exit 0   # already re-entered once; let it stop

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

# Nothing to test yet (e.g. first scaffolding turn, or tests/ left over from
# a reset with only stale __pycache__ in it) — don't block.
find tests -name '*.py' -not -path '*/__pycache__/*' 2>/dev/null | grep -q . || exit 0

if output=$(uv run pytest -q 2>&1); then
  exit 0
else
  reason=$(printf 'Tests are failing — fix them (or the code) before finishing:\n\n%s' "$output" | tail -c 4000)
  jq -n --arg r "$reason" '{decision:"block",reason:$r}'
  exit 0
fi
