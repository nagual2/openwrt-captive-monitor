#!/bin/bash
set -euo pipefail

# Сборка DEB пакета с Docker образом

VERSION=$(cat VERSION)
PACKAGE_NAME="openwrt-captive-monitor-docker"
BUILD_DIR=$(mktemp -d)
DIST_DIR="dist/deb-docker"

echo "=== Building Docker DEB package ==="
echo "Version: $VERSION"
echo "Build dir: $BUILD_DIR"

# Создать структуру пакета
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/usr/lib/systemd/system"
mkdir -p "$BUILD_DIR/usr/share/captive-daemon"
mkdir -p "$BUILD_DIR/etc/default"

# Копировать control файлы
cp debian-docker/control "$BUILD_DIR/DEBIAN/"
cp debian-docker/postinst "$BUILD_DIR/DEBIAN/"
cp debian-docker/prerm "$BUILD_DIR/DEBIAN/"
chmod 755 "$BUILD_DIR/DEBIAN/postinst"
chmod 755 "$BUILD_DIR/DEBIAN/prerm"

# Обновить версию в control
sed -i "s/^Version:.*/Version: $VERSION/" "$BUILD_DIR/DEBIAN/control"

# Копировать systemd unit
cp debian-docker/captive-daemon.service "$BUILD_DIR/usr/lib/systemd/system/"

# Собрать Docker образ
echo "Building Docker image..."
docker build -f docker/daemon-selenium/Dockerfile -t captive-portal-daemon:latest .

# Экспортировать образ в tar
echo "Exporting Docker image..."
docker save captive-portal-daemon:latest -o "$BUILD_DIR/usr/share/captive-daemon/captive-portal-daemon.tar"

# Сжать tar
echo "Compressing image..."
gzip "$BUILD_DIR/usr/share/captive-daemon/captive-portal-daemon.tar"

# Собрать пакет
echo "Building package..."
mkdir -p "$DIST_DIR"
dpkg-deb --build "$BUILD_DIR" "$DIST_DIR/${PACKAGE_NAME}_${VERSION}_all.deb"

# Очистка
rm -rf "$BUILD_DIR"

echo "=== Build complete ==="
ls -lh "$DIST_DIR/${PACKAGE_NAME}_${VERSION}_all.deb"

echo ""
echo "To install:"
echo "  sudo dpkg -i $DIST_DIR/${PACKAGE_NAME}_${VERSION}_all.deb"
echo ""
echo "Note: Docker must be installed first!"
echo "  curl -fsSL https://get.docker.com | sudo sh"
