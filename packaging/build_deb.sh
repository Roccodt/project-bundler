#!/usr/bin/env bash
# packaging/build_deb.sh
# Builds a .deb package from the compiled binary.
# Usage: bash packaging/build_deb.sh <version>
set -euo pipefail

VERSION="${1:-1.0}"
ARCH="amd64"
PKG_NAME="project-bundler"
DEB_ROOT="deb-build"

echo "▶ Building ${PKG_NAME}_${VERSION}_${ARCH}.deb"

# ── clean slate ──────────────────────────────────────────────
rm -rf "$DEB_ROOT"

# ── directory structure ──────────────────────────────────────
mkdir -p "${DEB_ROOT}/DEBIAN"
mkdir -p "${DEB_ROOT}/usr/local/bin"
mkdir -p "${DEB_ROOT}/usr/share/applications"
mkdir -p "${DEB_ROOT}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${DEB_ROOT}/usr/share/doc/${PKG_NAME}"

# ── binary ───────────────────────────────────────────────────
cp dist/project-bundler "${DEB_ROOT}/usr/local/bin/project-bundler"
chmod 755 "${DEB_ROOT}/usr/local/bin/project-bundler"

# ── icon ─────────────────────────────────────────────────────
cp packaging/project-bundler.svg \
   "${DEB_ROOT}/usr/share/icons/hicolor/256x256/apps/project-bundler.svg"

# ── .desktop entry ───────────────────────────────────────────
cat > "${DEB_ROOT}/usr/share/applications/project-bundler.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Project Bundler
Comment=Archive and restore project folders with SHA-256 verification
Exec=/usr/local/bin/project-bundler
Icon=project-bundler
Terminal=false
Categories=Utility;Archiving;
Keywords=archive;bundle;compress;backup;restore;
StartupWMClass=project-bundler
DESKTOP

# ── copyright / changelog ─────────────────────────────────────
cat > "${DEB_ROOT}/usr/share/doc/${PKG_NAME}/copyright" <<COPYRIGHT
Project Bundler
Copyright $(date +%Y) Roccodt
MIT License — https://github.com/Roccodt/project-bundler/blob/main/LICENSE
COPYRIGHT

# ── DEBIAN/control ───────────────────────────────────────────
# Get installed size in KB
INSTALLED_SIZE=$(du -sk "${DEB_ROOT}/usr" | cut -f1)

cat > "${DEB_ROOT}/DEBIAN/control" <<CONTROL
Package: project-bundler
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Installed-Size: ${INSTALLED_SIZE}
Depends: zenity, libx11-6
Maintainer: Roccodt <roccodt@gmail.com>
Homepage: https://github.com/Roccodt/project-bundler
Description: Archive and restore project folders
 Project Bundler compresses project folders into verified
 portable bundle files using gzip + SHA-256 integrity checks.
 Supports drag-and-drop, a bundle library, and one-click restore.
CONTROL

# ── DEBIAN/postinst — update icon cache after install ─────────
cat > "${DEB_ROOT}/DEBIAN/postinst" <<'POSTINST'
#!/bin/sh
set -e
if command -v update-icon-caches >/dev/null 2>&1; then
    update-icon-caches /usr/share/icons/hicolor 2>/dev/null || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
fi
POSTINST
chmod 755 "${DEB_ROOT}/DEBIAN/postinst"

# ── DEBIAN/postrm — clean up icon cache after remove ──────────
cat > "${DEB_ROOT}/DEBIAN/postrm" <<'POSTRM'
#!/bin/sh
set -e
if command -v update-icon-caches >/dev/null 2>&1; then
    update-icon-caches /usr/share/icons/hicolor 2>/dev/null || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
fi
POSTRM
chmod 755 "${DEB_ROOT}/DEBIAN/postrm"

# ── build ────────────────────────────────────────────────────
dpkg-deb --build --root-owner-group "${DEB_ROOT}" \
    "${PKG_NAME}_${VERSION}_${ARCH}.deb"

echo "✔ Built: ${PKG_NAME}_${VERSION}_${ARCH}.deb"
ls -lh "${PKG_NAME}_${VERSION}_${ARCH}.deb"
