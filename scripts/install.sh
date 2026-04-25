#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# skilar — Install Script
# One command to install AI agent skills for OpenCode and Claude Code.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/joeldevz/skills/main/scripts/install.sh | bash
#
# Options:
#   --method brew|binary|go   Force install method (default: auto)
#   --dir PATH                Custom install directory
#   -h, --help                Show help
# ============================================================================

GITHUB_OWNER="joeldevz"
GITHUB_REPO="skills"
BINARY_NAME="skilar"
BREW_TAP="joeldevz/tap"

# ============================================================================
# Colors (only when TTY)
# ============================================================================

setup_colors() {
  if [ -t 1 ] && [ "${TERM:-}" != "dumb" ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    DIM='\033[2m'
    NC='\033[0m'
  else
    RED='' GREEN='' YELLOW='' BLUE='' CYAN='' BOLD='' DIM='' NC=''
  fi
}

# ============================================================================
# Logging
# ============================================================================

info()    { echo -e "${BLUE}[info]${NC} $*"; }
success() { echo -e "${GREEN}[ok]${NC} $*"; }
warn()    { echo -e "${YELLOW}[warn]${NC} $*"; }
error()   { echo -e "${RED}[error]${NC} $*" >&2; }
fatal()   { error "$@"; exit 1; }
step()    { echo -e "\n${CYAN}${BOLD}==>${NC} ${BOLD}$*${NC}"; }

# ============================================================================
# Help
# ============================================================================

show_help() {
  cat <<EOF
skilar installer

USAGE:
  curl -fsSL https://raw.githubusercontent.com/joeldevz/skills/main/scripts/install.sh | bash
  ./install.sh [OPTIONS]

OPTIONS:
  --method METHOD   Install method: brew, binary, go (default: auto)
  --dir PATH        Custom install directory (default: ~/.local/bin)
  -h, --help        Show this help

EXAMPLES:
  ./install.sh                     # Auto-detect best method
  ./install.sh --method brew       # Force Homebrew
  ./install.sh --dir ~/bin         # Custom install dir
EOF
}

# ============================================================================
# Banner
# ============================================================================

print_banner() {
  echo ""
  echo -e "${CYAN}${BOLD}"
  echo "   ____           _                    ____  _    _ _ _     "
  echo "  / ___| ___  ___| | ___ ___  ___     / ___|| | _(_) | |___ "
  echo " | |   / _ \/ __| |/ / '__\ \/ /     \\___ \\| |/ / | | / __|"
  echo " | |__| (_) \\__ \\   <| |   >  <       ___) |   <| | | \\__ \\"
  echo "  \\____\\___/|___/_|\\_\\_|  /_/\\_\\     |____/|_|\\_\\_|_|_|___/"
  echo -e "${NC}"
  echo -e " ${DIM}AI agent skills installer for OpenCode and Claude Code${NC}"
  echo ""
}

# ============================================================================
# Platform detection
# ============================================================================

detect_platform() {
  OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
  case "$OS" in
    linux)  OS="linux" ;;
    darwin) OS="darwin" ;;
    *)      fatal "Unsupported OS: $OS. Use the Windows PowerShell installer instead." ;;
  esac

  ARCH="$(uname -m)"
  case "$ARCH" in
    x86_64|amd64)  ARCH="amd64" ;;
    arm64|aarch64) ARCH="arm64" ;;
    *)             fatal "Unsupported architecture: $ARCH" ;;
  esac

  success "Platform: ${OS}/${ARCH}"
}

# ============================================================================
# Prerequisites
# ============================================================================

check_prerequisites() {
  step "Checking prerequisites"

  local missing=()
  if ! command -v curl &>/dev/null; then
    missing+=("curl")
  fi
  if ! command -v git &>/dev/null; then
    missing+=("git")
  fi

  if [ ${#missing[@]} -gt 0 ]; then
    fatal "Missing required tools: ${missing[*]}. Please install them and try again."
  fi

  success "curl and git are available"
}

# ============================================================================
# Install method detection
# ============================================================================

detect_install_method() {
  if [ -n "${FORCE_METHOD:-}" ]; then
    case "$FORCE_METHOD" in
      brew|go|binary) INSTALL_METHOD="$FORCE_METHOD" ;;
      *) fatal "Unknown install method: $FORCE_METHOD. Use: brew, binary, or go" ;;
    esac
    info "Using forced method: $INSTALL_METHOD"
    return
  fi

  step "Detecting best install method"

  # Priority: brew > binary > go
  # Brew handles upgrades natively.
  # Binary download is always up-to-date.
  # go install last: Go module proxy can lag ~30min behind new tags.
  if command -v brew &>/dev/null; then
    INSTALL_METHOD="brew"
    success "Homebrew found — will install via brew tap"
  else
    INSTALL_METHOD="binary"
    info "Will download pre-built binary from GitHub Releases"
  fi
}

# ============================================================================
# Install via Homebrew
# ============================================================================

install_brew() {
  step "Installing via Homebrew"

  info "Refreshing ${BREW_TAP}..."
  brew untap "$BREW_TAP" 2>/dev/null || true
  if ! brew tap "$BREW_TAP"; then
    fatal "Failed to tap $BREW_TAP"
  fi

  if brew list "$BINARY_NAME" &>/dev/null; then
    info "Already installed, upgrading ${BINARY_NAME}..."
    if brew upgrade "$BINARY_NAME" 2>/dev/null; then
      success "Upgraded ${BINARY_NAME} via Homebrew"
    else
      success "${BINARY_NAME} is already at the latest version"
    fi
  else
    info "Installing ${BINARY_NAME}..."
    if brew install "$BINARY_NAME"; then
      success "Installed ${BINARY_NAME} via Homebrew"
    else
      fatal "Failed to install ${BINARY_NAME} via Homebrew"
    fi
  fi
}

# ============================================================================
# Install via go install
# ============================================================================

install_go() {
  step "Installing via go install"

  local go_package="github.com/${GITHUB_OWNER}/${GITHUB_REPO}/cmd/${BINARY_NAME}@latest"
  info "Running: go install ${go_package}"

  if ! go install "$go_package"; then
    fatal "Failed to install via go install. Make sure Go is properly configured."
  fi

  local gobin
  gobin="$(go env GOBIN)"
  if [ -z "$gobin" ]; then
    gobin="$(go env GOPATH)/bin"
  fi

  if [[ ":$PATH:" != *":$gobin:"* ]]; then
    warn "${gobin} is not in your PATH"
    warn "Add this to your shell profile: export PATH=\"\$PATH:${gobin}\""
  fi

  success "Installed ${BINARY_NAME} via go install"
}

# ============================================================================
# Install via binary download
# ============================================================================

get_latest_version() {
  local url="https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/releases/latest"
  info "Fetching latest release from GitHub..."

  local response
  response="$(curl -sL -w "\n%{http_code}" "$url")" || fatal "Failed to fetch latest release"

  local http_code body
  http_code="$(echo "$response" | tail -n1)"
  body="$(echo "$response" | sed '$d')"

  if [ "$http_code" != "200" ]; then
    fatal "GitHub API returned HTTP $http_code. Rate limited? Try again later or use --method brew/go"
  fi

  LATEST_VERSION="$(echo "$body" | sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)"

  if [ -z "$LATEST_VERSION" ]; then
    fatal "Could not determine latest version from GitHub API response"
  fi

  VERSION_NUMBER="${LATEST_VERSION#v}"
  success "Latest version: ${LATEST_VERSION}"
}

install_binary() {
  step "Installing pre-built binary"

  get_latest_version

  local archive_name="${BINARY_NAME}_${VERSION_NUMBER}_${OS}_${ARCH}.tar.gz"
  local download_url="https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}/releases/download/${LATEST_VERSION}/${archive_name}"
  local checksums_url="https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}/releases/download/${LATEST_VERSION}/checksums.txt"

  local tmpdir
  tmpdir="$(mktemp -d)"
  trap '[ -n "${tmpdir:-}" ] && rm -rf "$tmpdir"' EXIT

  info "Downloading ${archive_name}..."
  if ! curl -sfL -o "${tmpdir}/${archive_name}" "$download_url"; then
    fatal "Failed to download ${download_url}"
  fi

  local file_size
  file_size="$(wc -c < "${tmpdir}/${archive_name}" | tr -d '[:space:]')"
  if [ "$file_size" -lt 1000 ]; then
    fatal "Downloaded file is suspiciously small (${file_size} bytes). Archive may not exist for this platform."
  fi
  success "Downloaded ${archive_name} (${file_size} bytes)"

  info "Verifying checksum..."
  if curl -sL -o "${tmpdir}/checksums.txt" "$checksums_url"; then
    local expected_checksum
    expected_checksum="$(grep "${archive_name}" "${tmpdir}/checksums.txt" 2>/dev/null | awk '{print $1}' || true)"

    if [ -n "$expected_checksum" ]; then
      local actual_checksum
      if command -v sha256sum &>/dev/null; then
        actual_checksum="$(sha256sum "${tmpdir}/${archive_name}" | awk '{print $1}')"
      elif command -v shasum &>/dev/null; then
        actual_checksum="$(shasum -a 256 "${tmpdir}/${archive_name}" | awk '{print $1}')"
      else
        warn "No sha256sum or shasum found — skipping checksum verification"
        actual_checksum="$expected_checksum"
      fi

      if [ "$actual_checksum" != "$expected_checksum" ]; then
        fatal "Checksum mismatch!\n  Expected: ${expected_checksum}\n  Got:      ${actual_checksum}"
      fi
      success "Checksum verified"
    else
      warn "Archive not found in checksums.txt — skipping verification"
    fi
  else
    warn "Could not download checksums.txt — skipping verification"
  fi

  info "Extracting ${BINARY_NAME}..."
  if ! tar -xzf "${tmpdir}/${archive_name}" -C "$tmpdir"; then
    fatal "Failed to extract archive"
  fi

  if [ ! -f "${tmpdir}/${BINARY_NAME}" ]; then
    fatal "Binary '${BINARY_NAME}' not found in archive"
  fi

  # Determine install directory
  local install_dir="${INSTALL_DIR:-}"
  if [ -z "$install_dir" ]; then
    if [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
      install_dir="/usr/local/bin"
    elif [ "$(id -u)" = "0" ]; then
      install_dir="/usr/local/bin"
    else
      install_dir="${HOME}/.local/bin"
    fi
  fi

  mkdir -p "$install_dir"

  info "Installing to ${install_dir}/${BINARY_NAME}..."
  if cp "${tmpdir}/${BINARY_NAME}" "${install_dir}/${BINARY_NAME}" 2>/dev/null; then
    chmod +x "${install_dir}/${BINARY_NAME}"
  elif command -v sudo &>/dev/null; then
    warn "Permission denied. Trying with sudo..."
    sudo cp "${tmpdir}/${BINARY_NAME}" "${install_dir}/${BINARY_NAME}"
    sudo chmod +x "${install_dir}/${BINARY_NAME}"
  else
    fatal "Cannot write to ${install_dir}. Run with sudo or use --dir to specify a writable directory."
  fi

  success "Installed ${BINARY_NAME} to ${install_dir}/${BINARY_NAME}"

  if [[ ":$PATH:" != *":${install_dir}:"* ]]; then
    warn "${install_dir} is not in your PATH"
    echo ""
    warn "Add this to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
    echo -e "  ${DIM}export PATH=\"\$PATH:${install_dir}\"${NC}"
    echo ""
  fi
}

# ============================================================================
# Verify installation
# ============================================================================

verify_installation() {
  step "Verifying installation"

  hash -r 2>/dev/null || true

  if command -v "$BINARY_NAME" &>/dev/null; then
    local version_output
    version_output="$("$BINARY_NAME" --help 2>&1 | head -1 || true)"
    success "${BINARY_NAME} is installed and ready"
    return 0
  fi

  local locations=(
    "/usr/local/bin/${BINARY_NAME}"
    "${HOME}/.local/bin/${BINARY_NAME}"
  )

  for loc in "${locations[@]}"; do
    if [ -x "$loc" ]; then
      success "Found ${BINARY_NAME} at ${loc}"
      warn "Binary location is not in your PATH. Add it to use '${BINARY_NAME}' directly."
      return 0
    fi
  done

  warn "Could not verify installation. You may need to restart your shell."
  return 0
}

# ============================================================================
# Next steps
# ============================================================================

print_next_steps() {
  echo ""
  echo -e "${GREEN}${BOLD}Installation complete!${NC}"
  echo ""
  echo -e "${BOLD}Next steps:${NC}"
  echo -e "  ${CYAN}1.${NC} Run ${BOLD}${BINARY_NAME}${NC} to start the interactive installer"
  echo -e "  ${CYAN}2.${NC} Select your AI tool(s): Claude Code, OpenCode"
  echo -e "  ${CYAN}3.${NC} Follow the prompts"
  echo ""
  echo -e "${DIM}For help: ${BINARY_NAME} --help${NC}"
  echo -e "${DIM}Docs: https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}${NC}"
  echo ""
}

# ============================================================================
# Main
# ============================================================================

main() {
  setup_colors

  FORCE_METHOD=""
  INSTALL_DIR=""

  while [ $# -gt 0 ]; do
    case "$1" in
      --method)
        [ $# -lt 2 ] && fatal "--method requires an argument"
        FORCE_METHOD="$2"; shift 2
        ;;
      --dir)
        [ $# -lt 2 ] && fatal "--dir requires an argument"
        INSTALL_DIR="$2"; shift 2
        ;;
      -h|--help)
        setup_colors
        show_help
        exit 0
        ;;
      *)
        fatal "Unknown option: $1. Use --help for usage."
        ;;
    esac
  done

  print_banner

  step "Detecting platform"
  detect_platform

  check_prerequisites
  detect_install_method

  case "$INSTALL_METHOD" in
    brew)   install_brew ;;
    go)     install_go ;;
    binary) install_binary ;;
  esac

  verify_installation
  print_next_steps
}

main "$@"
