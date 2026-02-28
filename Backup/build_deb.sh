#!/bin/bash
set -e

APP=project-bundler
VER=3.0
BUILD=deb-build

rm -rf $BUILD

mkdir -p $BUILD/DEBIAN
mkdir -p $BUILD/usr/bin
mkdir -p $BUILD/usr/share
mkdir -p $BUILD/usr/share/applications
mkdir -p $BUILD/usr/share/icons/hicolor/512x512/apps

# Python app
cp project_bundler_v3.py $BUILD/usr/share/$APP.py
chmod 755 $BUILD/usr/share/$APP.py

# launcher wrapper
cat > $BUILD/usr/bin/$APP <<EOF
#!/bin/bash
exec python3 /usr/share/$APP.py "\$@"
EOF
chmod 755 $BUILD/usr/bin/$APP

# icon
cp assets/project-bundler.png \
$BUILD/usr/share/icons/hicolor/512x512/apps/$APP.png

# control
cat > $BUILD/DEBIAN/control <<EOF
Package: $APP
Version: $VER
Architecture: amd64
Maintainer: Rocco
Depends: python3, python3-tk, zenity
Description: Professional project archiver with verification.
EOF

# desktop entry
cat > $BUILD/usr/share/applications/$APP.desktop <<EOF
[Desktop Entry]
Name=Project Bundler
Comment=Archive and Restore Projects
Exec=project-bundler
Icon=$APP
Type=Application
Terminal=false
Categories=Utility;
EOF

dpkg-deb --root-owner-group --build $BUILD "${APP}_${VER}_amd64.deb"

echo "✅ Build complete"
