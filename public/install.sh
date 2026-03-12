#!/usr/bin/env bash
set -e

# ── Nexus CLI Installer ───────────────────────────────────────────────────────
#
# Usage:
#   curl -fsSL https://nexus.coderstudio.co/install.sh | bash
#
# Options (env vars):
#   NEXUS_VERSION   PyPI version to install     (default: latest)
#   NEXUS_DIR       Install prefix              (default: ~/.local)
# ─────────────────────────────────────────────────────────────────────────────

VERSION="${NEXUS_VERSION:-}"
INSTALL_DIR="${NEXUS_DIR:-$HOME/.local}"
BIN_DIR="$INSTALL_DIR/bin"

BOLD="\033[1m"
CYAN="\033[36m"
GREEN="\033[32m"
RED="\033[31m"
DIM="\033[2m"
RESET="\033[0m"

print_logo() {
  printf "\n"
  printf "${CYAN}  ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗${RESET}\n"
  printf "${CYAN}  ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝${RESET}\n"
  printf "${CYAN}  ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗${RESET}\n"
  printf "${CYAN}  ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║${RESET}\n"
  printf "${CYAN}  ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║${RESET}\n"
  printf "${CYAN}  ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝${RESET}\n"
  printf "  ${DIM}enterprise dev toolkit${RESET}\n\n"
}

step() { printf "  ${CYAN}▶${RESET}  $1\n"; }
ok()   { printf "  ${GREEN}✓${RESET}  $1\n"; }
err()  { printf "  ${RED}✗${RESET}  $1\n" >&2; exit 1; }

need() {
  command -v "$1" >/dev/null 2>&1 || err "'$1' is required but not installed. $2"
}

print_logo

DISPLAY_VERSION="${VERSION:-latest}"
printf "  ${BOLD}Installing nexus CLI${RESET}  ${DIM}(version: $DISPLAY_VERSION)${RESET}\n\n"

# ── Check requirements ────────────────────────────────────────────────────────
step "Checking requirements…"
need curl  "Install via: brew install curl"

# Prefer uv, fall back to pip
if command -v uv >/dev/null 2>&1; then
  INSTALLER="uv"
elif command -v pip3 >/dev/null 2>&1; then
  INSTALLER="pip"
elif command -v pip >/dev/null 2>&1; then
  INSTALLER="pip"
else
  err "Neither 'uv' nor 'pip' found. Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
fi
ok "Requirements satisfied  (installer: $INSTALLER)"

# ── Install ───────────────────────────────────────────────────────────────────
if [ -n "$VERSION" ]; then
  PYPI_PKG="nexus-toolkit==$VERSION"
  step "Installing nexus-toolkit==$VERSION from PyPI…"
else
  PYPI_PKG="nexus-toolkit"
  step "Installing nexus-toolkit from PyPI…"
fi

if [ "$INSTALLER" = "uv" ]; then
  # Remove old nexus-mcp tool if present (package was renamed to nexus-toolkit)
  uv tool uninstall nexus-mcp 2>/dev/null || true
  uv tool install --reinstall --force "$PYPI_PKG" --quiet
  NEXUS_BIN="$(uv tool dir)/nexus-toolkit/bin/nexus"
  # uv tool also exposes scripts via ~/.local/bin — check there first
  UV_TOOL_BIN="$(uv tool dir)/../bin/nexus"
  [ -f "$UV_TOOL_BIN" ] && NEXUS_BIN="$UV_TOOL_BIN"
else
  pip3 install --quiet --upgrade "$PYPI_PKG"
  NEXUS_BIN="$(python3 -m site --user-base)/bin/nexus"
fi

# Find actual binary if the guessed path is wrong
if [ ! -f "$NEXUS_BIN" ]; then
  NEXUS_BIN="$(find "${HOME}/.local" -name "nexus" -type f 2>/dev/null | head -1)"
fi

ok "Installed successfully"

# Clear shell command hash cache so the new binary is found immediately
hash -r 2>/dev/null || true

# ── Verify binary ─────────────────────────────────────────────────────────────
step "Verifying installation…"

if command -v nexus >/dev/null 2>&1; then
  ok "nexus is in PATH"
else
  # Make sure BIN_DIR is in PATH for this session
  export PATH="$BIN_DIR:$(python3 -m site --user-base)/bin:$HOME/.local/share/uv/tools/nexus-toolkit/bin:$PATH"
  if command -v nexus >/dev/null 2>&1; then
    ok "nexus found (PATH update needed — see below)"
  else
    printf "\n  ${DIM}Binary location: $NEXUS_BIN${RESET}\n"
  fi
fi

# ── Symlink to /usr/local/bin so nexus works everywhere ──────────────────────
SYMLINK_DIR="/usr/local/bin"

if [ -f "$NEXUS_BIN" ] && ! command -v nexus >/dev/null 2>&1; then
  step "Creating symlink in $SYMLINK_DIR…"
  if [ -w "$SYMLINK_DIR" ]; then
    ln -sf "$NEXUS_BIN" "$SYMLINK_DIR/nexus"
    ok "Symlinked: $SYMLINK_DIR/nexus → $NEXUS_BIN"
  else
    # Try with sudo
    if sudo ln -sf "$NEXUS_BIN" "$SYMLINK_DIR/nexus" 2>/dev/null; then
      ok "Symlinked (sudo): $SYMLINK_DIR/nexus → $NEXUS_BIN"
    else
      # Fall back to ~/.local/bin (no sudo needed)
      mkdir -p "$HOME/.local/bin"
      ln -sf "$NEXUS_BIN" "$HOME/.local/bin/nexus"
      ok "Symlinked: ~/.local/bin/nexus → $NEXUS_BIN"

      # Add to shell RC if ~/.local/bin not already in PATH
      SHELL_RC=""
      case "$SHELL" in
        */zsh)  SHELL_RC="$HOME/.zshrc" ;;
        */bash) SHELL_RC="$HOME/.bashrc" ;;
        */fish) SHELL_RC="$HOME/.config/fish/config.fish" ;;
      esac
      if [ -n "$SHELL_RC" ] && ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
        printf "\n  ${DIM}Adding ~/.local/bin to PATH in $SHELL_RC…${RESET}\n"
        echo "\nexport PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$SHELL_RC"
        export PATH="$HOME/.local/bin:$PATH"
        ok "PATH updated — restart your terminal or run: source $SHELL_RC"
      fi
    fi
  fi
fi

# ── Done ──────────────────────────────────────────────────────────────────────
printf "\n  ${GREEN}${BOLD}Installation complete!${RESET}\n\n"
printf "  ${DIM}Get started:${RESET}\n"
printf "  ${CYAN}nexus${RESET} ${DIM}--help${RESET}\n"
printf "  ${CYAN}nexus run prompt${RESET} ${DIM}\"A SaaS dashboard\" -g nextjs-fullstack -p my-app${RESET}\n\n"
