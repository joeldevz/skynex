#!/usr/bin/env bash
# OpenCode SessionStart hook — custom, smart-zone aware
# Inspired by obra/Superpowers SessionStart hook but adapted to:
# - Respect orchestrator-delegate-first (no "1% chance invoke skill")
# - Inject project context with token budget awareness
# - Bilingual ES/EN support
# - Optional via SKIP_SESSION_HOOK=1
#
# Refs: docs/IMPROVEMENT-PLAN.md (IL9), Research/Superpowers-vs-Clasing-Skills.md

set -e

# Bypass for emergency or testing
if [ "${SKIP_SESSION_HOOK:-0}" = "1" ]; then
  exit 0
fi

# Locate repo root
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT" || exit 0

# Token budget for hook injection (smart-zone aware)
# Budget: ~5K tokens max for the hook output to leave room for actual work
MAX_HOOK_TOKENS=5000

# Helper: detect approximate token count (rough: chars / 4)
estimate_tokens() {
  echo "$1" | wc -c | awk '{print int($1/4)}'
}

# Build the injection payload
INJECTION=""

# 1. Project name + branch
PROJECT_NAME="$(basename "$REPO_ROOT")"
GIT_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"
INJECTION+="# Session Bootstrap

Project: ${PROJECT_NAME}
Branch: ${GIT_BRANCH}

"

# 2. Inject CONVENTIONS.md if exists (cap at 200 lines)
if [ -f "CONVENTIONS.md" ]; then
  INJECTION+="## Conventions (auto-injected)

$(head -n 200 CONVENTIONS.md)

"
fi

# 3. Inject skill-registry if exists (when GA4 lands)
if [ -f ".opencode/skill-registry.md" ]; then
  INJECTION+="## Skill Registry (auto-injected)

$(cat .opencode/skill-registry.md)

"
fi

# 4. Active sprint indicator from IMPROVEMENT-PLAN.md
if [ -f "docs/IMPROVEMENT-PLAN.md" ]; then
  ACTIVE_SPRINT="$(grep -E '^## Fase' docs/IMPROVEMENT-PLAN.md | head -3 | sed 's/^## /- /')"
  INJECTION+="## Active Plan Phases

${ACTIVE_SPRINT}

"
fi

# 5. Smart-zone reminder
INJECTION+="## Smart Zone Reminder

- Hard cap: 100K tokens
- Strategy at warning (80K): plan clean break point
- See: opencode/skills/_shared/smart-zone-budget.md

"

# Verify payload is within budget
TOKEN_ESTIMATE=$(estimate_tokens "$INJECTION")
if [ "$TOKEN_ESTIMATE" -gt "$MAX_HOOK_TOKENS" ]; then
  # Trim to first N chars (rough cap)
  CHAR_LIMIT=$((MAX_HOOK_TOKENS * 4))
  INJECTION="${INJECTION:0:$CHAR_LIMIT}

[truncated by session-start hook to respect token budget]"
fi

# Output to stdout — OpenCode picks this up as session prefix
echo "$INJECTION"
