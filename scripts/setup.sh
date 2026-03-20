#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

INSTALL_OPENCODE=0
INSTALL_CLAUDE=0

usage() {
  cat <<'EOF'
Usage:
  ./scripts/setup.sh [--all] [--opencode] [--claude]

Options:
  --all        Install everything supported on this machine
  --opencode   Install OpenCode config only
  --claude     Install Claude Code skills and agents only
EOF
}

append_marked_block() {
  local target_file="$1"
  local block_file="$2"
  local marker="$3"

  python3 - "$target_file" "$block_file" "$marker" <<'PY'
from pathlib import Path
import sys

target = Path(sys.argv[1])
block_path = Path(sys.argv[2])
marker = sys.argv[3]
start = f"<!-- BEGIN {marker} -->"
end = f"<!-- END {marker} -->"
block = block_path.read_text(encoding="utf-8").rstrip()
wrapped = f"{start}\n{block}\n{end}\n"

existing = target.read_text(encoding="utf-8") if target.exists() else ""
if start in existing and end in existing:
    before, rest = existing.split(start, 1)
    _, after = rest.split(end, 1)
    updated = before.rstrip()
    if updated:
        updated += "\n\n"
    updated += wrapped
    tail = after.strip()
    if tail:
        updated += "\n\n" + tail + "\n"
else:
    updated = existing.rstrip()
    if updated:
        updated += "\n\n"
    updated += wrapped

target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(updated, encoding="utf-8")
PY
}

backup_dir_if_exists() {
  local target_dir="$1"
  if [ -d "$target_dir" ]; then
    local backup="${target_dir}.backup.$(date +%Y%m%d-%H%M%S)"
    echo "Existing directory found at $target_dir"
    echo "Creating backup at $backup"
    cp -r "$target_dir" "$backup"
  fi
}

install_opencode() {
  local source_dir="$REPO_ROOT/opencode"
  local target_dir="$HOME/.config/opencode"

  if [ ! -d "$source_dir" ]; then
    echo "Error: opencode/ directory not found at $source_dir"
    exit 1
  fi

  backup_dir_if_exists "$target_dir"

  echo "Copying OpenCode config to $target_dir..."
  mkdir -p "$target_dir"
  rsync -a --exclude='node_modules' "$source_dir/" "$target_dir/"

  if [ -d "$target_dir" ]; then
    local latest_backup
    latest_backup=$(python3 -c "
from pathlib import Path
base = Path('$target_dir').expanduser()
matches = sorted(base.parent.glob(base.name + '.backup.*'), key=lambda p: p.stat().st_mtime, reverse=True)
print(matches[0] if matches else '')
" 2>/dev/null || true)
    if [ -n "$latest_backup" ] && [ -f "$latest_backup/opencode.json" ]; then
      local existing_key
      existing_key=$(python3 -c "
import json
from pathlib import Path
path = Path('$latest_backup/opencode.json')
try:
    data = json.loads(path.read_text())
    key = data.get('mcp', {}).get('context7', {}).get('headers', {}).get('CONTEXT7_API_KEY', '')
    if key and key != 'SET_IN_LOCAL_CONFIG':
        print(key)
except Exception:
    pass
" 2>/dev/null || true)

      if [ -n "$existing_key" ]; then
        echo "Restoring your Context7 API key from backup..."
        python3 -c "
import json
from pathlib import Path
path = Path('$target_dir/opencode.json')
data = json.loads(path.read_text())
data['mcp']['context7']['headers']['CONTEXT7_API_KEY'] = '$existing_key'
data['mcp']['context7']['enabled'] = True
path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
"
      fi
    fi
  fi

  echo "Installing OpenCode dependencies..."
  if command -v bun >/dev/null 2>&1; then
    (cd "$target_dir" && bun install --silent)
  elif command -v npm >/dev/null 2>&1; then
    (cd "$target_dir" && npm install --silent)
  else
    echo "Warning: neither bun nor npm found. Install dependencies manually:"
    echo "  cd $target_dir && bun install"
  fi

  echo "OpenCode installed at $target_dir"
}

install_claude() {
  local target_dir="$HOME/.claude"
  local overlay_file="$REPO_ROOT/claude-code/CLAUDE.md"
  local target_claude_md="$target_dir/CLAUDE.md"

  if [ ! -f "$overlay_file" ]; then
    echo "Error: Claude overlay not found at $overlay_file"
    exit 1
  fi

  backup_dir_if_exists "$target_dir"
  mkdir -p "$target_dir"

  echo "Rendering Claude Code agents and skills..."
  python3 "$REPO_ROOT/scripts/install_claude_assets.py"

  echo "Updating $target_claude_md with team workflow overlay..."
  append_marked_block "$target_claude_md" "$overlay_file" "skills-repo"

  echo "Claude Code assets installed at $target_dir"
}

if [ "$#" -eq 0 ]; then
  if command -v opencode >/dev/null 2>&1; then
    INSTALL_OPENCODE=1
  fi
  if command -v claude >/dev/null 2>&1; then
    INSTALL_CLAUDE=1
  fi

  if [ "$INSTALL_OPENCODE" -eq 0 ] && [ "$INSTALL_CLAUDE" -eq 0 ]; then
    echo "No supported tool detected automatically. Use --opencode, --claude, or --all."
    exit 1
  fi
fi

while [ "$#" -gt 0 ]; do
  case "$1" in
    --all)
      INSTALL_OPENCODE=1
      INSTALL_CLAUDE=1
      ;;
    --opencode)
      INSTALL_OPENCODE=1
      ;;
    --claude)
      INSTALL_CLAUDE=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
  shift
done

if [ "$INSTALL_OPENCODE" -eq 1 ]; then
  install_opencode
fi

if [ "$INSTALL_CLAUDE" -eq 1 ]; then
  install_claude
fi

echo ""
echo "Setup complete."
echo ""
if [ "$INSTALL_OPENCODE" -eq 1 ]; then
  echo "- OpenCode: ~/.config/opencode"
fi
if [ "$INSTALL_CLAUDE" -eq 1 ]; then
  echo "- Claude Code: ~/.claude"
  echo "  - agents: ~/.claude/agents"
  echo "  - skills: ~/.claude/skills"
  echo "  - overlay: ~/.claude/CLAUDE.md"
fi
