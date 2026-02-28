#!/usr/bin/env bash
# Project Bundler — Uninstaller
set -euo pipefail

APP_NAME="project-bundler"
APP_DIR="$HOME/.local/share/$APP_NAME"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RESET='\033[0m'

echo -e "${CYAN}Uninstalling Project Bundler…${RESET}"

rm -f  "$BIN_DIR/$APP_NAME"
rm -f  "$DESKTOP_DIR/$APP_NAME.desktop"
rm -f  "$ICON_DIR/$APP_NAME.svg"
rm -rf "$APP_DIR"

command -v update-desktop-database &>/dev/null && \
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true

echo -e "${GREEN}✔ Project Bundler removed.${RESET}"
echo -e "${YELLOW}Note: Your bundles in ~/MyProjectBundles/ were NOT deleted.${RESET}"
echo -e "      Remove them manually if you want: rm -rf ~/MyProjectBundles/"
