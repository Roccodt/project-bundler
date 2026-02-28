#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════╗
# ║          PROJECT BUNDLER — Self-Contained Installer      ║
# ║  Supports: Ubuntu/Debian · Fedora/RHEL · Arch · openSUSE ║
# ╚══════════════════════════════════════════════════════════╝
set -euo pipefail

APP_NAME="project-bundler"
APP_DIR="$HOME/.local/share/$APP_NAME"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
VENV="$APP_DIR/venv"
SCRIPT="$APP_DIR/project_bundler_v3.py"

# ── colours ──────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'
YELLOW='\033[1;33m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}▶ $*${RESET}"; }
success() { echo -e "${GREEN}✔ $*${RESET}"; }
warn()    { echo -e "${YELLOW}⚠ $*${RESET}"; }
error()   { echo -e "${RED}✖ $*${RESET}"; exit 1; }

echo -e "${BOLD}"
echo "  ╔════════════════════════════════╗"
echo "  ║    Project Bundler Installer   ║"
echo "  ╚════════════════════════════════╝"
echo -e "${RESET}"

# ── detect distro ────────────────────────────────────────────
detect_distro() {
    if   command -v apt-get  &>/dev/null; then echo "debian"
    elif command -v dnf      &>/dev/null; then echo "fedora"
    elif command -v pacman   &>/dev/null; then echo "arch"
    elif command -v zypper   &>/dev/null; then echo "suse"
    else echo "unknown"
    fi
}

DISTRO=$(detect_distro)
info "Detected package manager: $DISTRO"

# ── install system packages ───────────────────────────────────
install_system_deps() {
    info "Installing system dependencies…"
    case $DISTRO in
        debian)
            sudo apt-get update -qq
            sudo apt-get install -y \
                python3 python3-pip python3-venv python3-tk \
                tcl-dev tk-dev zenity \
                libx11-dev libxext-dev
            ;;
        fedora)
            sudo dnf install -y \
                python3 python3-pip python3-tkinter \
                zenity \
                libX11-devel libXext-devel
            ;;
        arch)
            sudo pacman -Sy --noconfirm \
                python python-pip tk \
                zenity \
                libx11
            ;;
        suse)
            sudo zypper install -y \
                python3 python3-pip python3-tk \
                zenity \
                libX11-devel
            ;;
        *)
            warn "Unknown distro — skipping system package install."
            warn "Make sure python3, python3-venv, python3-tk, and zenity are installed."
            ;;
    esac
    success "System deps ready"
}

# ── check for sudo only when needed ──────────────────────────
if [[ "$DISTRO" != "unknown" ]]; then
    install_system_deps
fi

# ── create app dir & venv ─────────────────────────────────────
info "Creating application directory…"
mkdir -p "$APP_DIR" "$BIN_DIR" "$DESKTOP_DIR" "$ICON_DIR"

info "Creating Python virtual environment…"
python3 -m venv "$VENV"
source "$VENV/bin/activate"

info "Installing Python packages (this may take a minute)…"
pip install --upgrade pip --quiet
pip install --quiet \
    customtkinter \
    tkinterdnd2

success "Python packages installed"

# ── copy app source ───────────────────────────────────────────
info "Installing application…"
cp "$(dirname "$0")/project_bundler_v3.py" "$SCRIPT"

# ── create launcher script ────────────────────────────────────
info "Creating launcher…"
cat > "$BIN_DIR/$APP_NAME" <<LAUNCHER
#!/usr/bin/env bash
source "$VENV/bin/activate"
exec python3 "$SCRIPT" "\$@"
LAUNCHER
chmod +x "$BIN_DIR/$APP_NAME"

# ── create SVG icon (pure text, no file needed) ───────────────
info "Creating icon…"
cat > "$ICON_DIR/$APP_NAME.svg" <<'SVG'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="12" fill="#0D1117"/>
  <rect x="8" y="20" width="48" height="32" rx="6"
        fill="#1A2A3A" stroke="#00B4FF" stroke-width="2"/>
  <rect x="16" y="12" width="20" height="12" rx="4"
        fill="#00B4FF" opacity="0.8"/>
  <line x1="32" y1="28" x2="32" y2="44"
        stroke="#00B4FF" stroke-width="3" stroke-linecap="round"/>
  <polyline points="24,38 32,46 40,38"
        fill="none" stroke="#00B4FF" stroke-width="3"
        stroke-linecap="round" stroke-linejoin="round"/>
</svg>
SVG

# ── .desktop file ─────────────────────────────────────────────
info "Creating application menu entry…"
cat > "$DESKTOP_DIR/$APP_NAME.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Project Bundler
Comment=Archive and restore project folders
Exec=$BIN_DIR/$APP_NAME
Icon=$ICON_DIR/$APP_NAME.svg
Terminal=false
Categories=Utility;Archiving;
Keywords=archive;bundle;compress;backup;
StartupWMClass=project-bundler
DESKTOP
chmod +x "$DESKTOP_DIR/$APP_NAME.desktop"

# update desktop database if possible
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

# ── add ~/.local/bin to PATH if missing ───────────────────────
SHELL_RC=""
case "$SHELL" in
    */bash) SHELL_RC="$HOME/.bashrc" ;;
    */zsh)  SHELL_RC="$HOME/.zshrc"  ;;
    */fish) SHELL_RC="$HOME/.config/fish/config.fish" ;;
esac

if [[ -n "$SHELL_RC" ]] && ! grep -q 'HOME/.local/bin' "$SHELL_RC" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
    warn "Added ~/.local/bin to PATH in $SHELL_RC — restart your shell or run:"
    warn "  source $SHELL_RC"
fi

echo
success "Installation complete!"
echo
echo -e "  ${BOLD}Run from terminal:${RESET}  $APP_NAME"
echo -e "  ${BOLD}Run from menu:${RESET}      Search 'Project Bundler'"
echo
echo -e "  ${CYAN}Bundles are saved to:  ~/MyProjectBundles/${RESET}"
echo
