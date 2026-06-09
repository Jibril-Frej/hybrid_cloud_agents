#!/usr/bin/env bash
# PreToolUse (matcher: Bash) — reject `git commit -m "..."` messages that are
# not Conventional Commits. Requires `jq`.
set -uo pipefail

input=$(cat)
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // ""')

case "$cmd" in
  *"git commit"*"-m"*)
    # Grab the message inside the first single- or double-quoted -m argument.
    msg=$(printf '%s' "$cmd" | sed -nE "s/.*-m[[:space:]]+['\"]([^'\"]*)['\"].*/\1/p")
    pattern='^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-z0-9._-]+\))?!?: .+'
    if [ -n "$msg" ] && ! [[ "$msg" =~ $pattern ]]; then
      reason="Commit message is not Conventional Commits: \"$msg\". Use e.g. 'feat(orchestrator): add private retrieval node'."
      jq -n --arg r "$reason" \
        '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'
      exit 0
    fi
    ;;
esac

# Allow everything else (no decision = normal permission flow).
exit 0
