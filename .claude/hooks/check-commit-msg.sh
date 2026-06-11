#!/usr/bin/env bash
# PreToolUse (matcher: Bash) — reject `git commit -m "..."` messages that are
# not Conventional Commits. Requires `jq`.
set -uo pipefail

input=$(cat)
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // ""')

case "$cmd" in
  *"git commit"*"-m"*)
    pattern='^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-z0-9._-]+\))?!?: .+'

    # Heredoc form: -m "$(cat <<'EOF' ... EOF)" — the subject is the first
    # line of the heredoc body. Otherwise fall back to a single-line -m "...".
    delim=$(printf '%s' "$cmd" | sed -nE "s/.*<<-?[\"']?([A-Za-z_][A-Za-z0-9_]*)[\"']?.*/\1/p" | head -n1)
    if [ -n "$delim" ]; then
      msg=$(printf '%s' "$cmd" | awk -v d="$delim" '
        f && $0==d { f=0 }
        f && !got { print; got=1 }
        /<</ { f=1 }
      ')
    else
      msg=$(printf '%s' "$cmd" | sed -nE "s/.*-m[[:space:]]+['\"]([^'\"]*)['\"].*/\1/p")
    fi
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
