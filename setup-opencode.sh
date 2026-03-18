#!/usr/bin/env bash
set -euo pipefail

# ─── OpenCode Team Setup Script ──────────────────────────────────────────────
# Copies the shared OpenCode config to ~/.config/opencode/ and installs deps.
# Run from the root of the skills repository.
# ──────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/opencode"
TARGET_DIR="$HOME/.config/opencode"

# ─── Preflight ────────────────────────────────────────────────────────────────

if [ ! -d "$SOURCE_DIR" ]; then
  echo "Error: opencode/ directory not found at $SOURCE_DIR"
  echo "Make sure you run this script from the root of the skills repository."
  exit 1
fi

# ─── Backup existing config ──────────────────────────────────────────────────

if [ -d "$TARGET_DIR" ]; then
  BACKUP="$TARGET_DIR.backup.$(date +%Y%m%d-%H%M%S)"
  echo "Existing config found at $TARGET_DIR"
  echo "Creating backup at $BACKUP"
  cp -r "$TARGET_DIR" "$BACKUP"
fi

# ─── Copy config ─────────────────────────────────────────────────────────────

echo "Copying opencode config to $TARGET_DIR..."
mkdir -p "$TARGET_DIR"

# Copy everything except node_modules
rsync -a --exclude='node_modules' "$SOURCE_DIR/" "$TARGET_DIR/"

# ─── Preserve local secrets ──────────────────────────────────────────────────

# If the backup had a real Context7 API key, restore it
if [ -n "${BACKUP:-}" ] && [ -f "$BACKUP/opencode.json" ]; then
  EXISTING_KEY=$(python3 -c "
import json, sys
try:
    with open('$BACKUP/opencode.json') as f:
        c = json.load(f)
    key = c.get('mcp',{}).get('context7',{}).get('headers',{}).get('CONTEXT7_API_KEY','')
    if key and key != 'SET_IN_LOCAL_CONFIG':
        print(key)
except:
    pass
" 2>/dev/null || true)

  if [ -n "$EXISTING_KEY" ]; then
    echo "Restoring your Context7 API key from backup..."
    python3 -c "
import json
with open('$TARGET_DIR/opencode.json') as f:
    c = json.load(f)
c['mcp']['context7']['headers']['CONTEXT7_API_KEY'] = '$EXISTING_KEY'
c['mcp']['context7']['enabled'] = True
with open('$TARGET_DIR/opencode.json', 'w') as f:
    json.dump(c, f, indent=2, ensure_ascii=False)
"
    echo "Context7 restored and enabled."
  fi
fi

# ─── Install plugin dependency ───────────────────────────────────────────────

echo "Installing plugin dependencies..."
if command -v bun &>/dev/null; then
  (cd "$TARGET_DIR" && bun install --silent)
elif command -v npm &>/dev/null; then
  (cd "$TARGET_DIR" && npm install --silent)
else
  echo "Warning: neither bun nor npm found. Install dependencies manually:"
  echo "  cd $TARGET_DIR && bun install"
fi

# ─── Check optional tools ───────────────────────────────────────────────────

echo ""
echo "Checking optional tools..."

if command -v engram &>/dev/null; then
  echo "  engram: found"
else
  echo "  engram: not found (memory persistence will be disabled)"
fi

if command -v gh &>/dev/null; then
  echo "  gh: found"
else
  echo "  gh: not found (/pr command won't work)"
fi

# ─── Context7 setup ─────────────────────────────────────────────────────────

CTX7_KEY=$(python3 -c "
import json
with open('$TARGET_DIR/opencode.json') as f:
    c = json.load(f)
print(c.get('mcp',{}).get('context7',{}).get('headers',{}).get('CONTEXT7_API_KEY',''))
" 2>/dev/null || true)

if [ "$CTX7_KEY" = "SET_IN_LOCAL_CONFIG" ]; then
  echo ""
  echo "Context7 is enabled but needs an API key for live library docs (/docs command)."
  read -rp "Do you have a Context7 API key? (y/N): " HAS_KEY
  if [[ "$HAS_KEY" =~ ^[Yy]$ ]]; then
    read -rp "Enter your Context7 API key: " USER_KEY
    if [ -n "$USER_KEY" ]; then
      python3 -c "
import json
with open('$TARGET_DIR/opencode.json') as f:
    c = json.load(f)
c['mcp']['context7']['headers']['CONTEXT7_API_KEY'] = '$USER_KEY'
c['mcp']['context7']['enabled'] = True
with open('$TARGET_DIR/opencode.json', 'w') as f:
    json.dump(c, f, indent=2, ensure_ascii=False)
"
      echo "Context7 configured and enabled."
    fi
  else
    echo "Skipped. You can enable it later in $TARGET_DIR/opencode.json"
  fi
fi

# ─── Done ────────────────────────────────────────────────────────────────────

echo ""
echo "Setup complete."
echo ""
echo "Config installed at: $TARGET_DIR"
echo ""
echo "Available commands:"
echo ""
echo "  Planning:"
echo "    /onboard           explore project stack, arch and conventions"
echo "    /plan <task>       investigate codebase and generate PLAN.md"
echo "    /plan-rewrite      review and improve an existing PLAN.md"
echo "    /estimate          T-shirt size estimate per step (XS-XL)"
echo ""
echo "  Execution:"
echo "    /execute           run next pending step"
echo "    /apply-feedback    apply human corrections to current step"
echo "    /diff              show annotated diff of current step changes"
echo "    /rollback [step]   undo last step with confirmation gate"
echo "    /status            show PLAN.md progress"
echo ""
echo "  Quality:"
echo "    /test [module]     generate or run tests for current step"
echo "    /review            quality gate: conventions, types, arch, missing tests"
echo ""
echo "  Documentation & Memory:"
echo "    /docs <lib> <topic>  fetch live docs via Context7"
echo "    /context [obs]       save discoveries to persistent memory (Engram)"
echo ""
echo "  Git:"
echo "    /commit            create conventional commit"
echo "    /pr                create pull request with gh"
echo ""
echo "Next step: open a project with OpenCode and run /onboard"
