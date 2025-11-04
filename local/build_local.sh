#!/bin/bash
set -e

# Create necessary directories
mkdir -p /tmp/opkg-feed
cd /mnt/c/git/openwrt-captive-monitor

# Clean previous builds
rm -rf /tmp/opkg-feed/*

# Create a simple package structure
PKG_DIR="/tmp/opkg-feed/package"
mkdir -p "$PKG_DIR/usr/sbin"
mkdir -p "$PKG_DIR/etc/init.d"
mkdir -p "$PKG_DIR/etc/config"
mkdir -p "$PKG_DIR/etc/uci-defaults"

# Copy the main script
cp package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor "$PKG_DIR/usr/sbin/"
chmod +x "$PKG_DIR/usr/sbin/openwrt_captive_monitor"

# Copy init script
cp package/openwrt-captive-monitor/files/etc/init.d/captive-monitor "$PKG_DIR/etc/init.d/"
chmod +x "$PKG_DIR/etc/init.d/captive-monitor"

# Copy config
cp package/openwrt-captive-monitor/files/etc/config/captive-monitor "$PKG_DIR/etc/config/"

# Create control file
cat > /tmp/opkg-feed/control <<EOL
Package: openwrt-captive-monitor
Version: 0.1.2-1
Depends: dnsmasq, curl
Architecture: all
Maintainer: OpenWrt Captive Monitor Team
Section: net
Description: Captive portal connectivity monitor and auto-redirect helper
EOL

# Create postinst script
cat > /tmp/opkg-feed/postinst <<'EOL'
#!/bin/sh
[ "${IPKG_NO_SCRIPT}" = "1" ] && exit 0
[ -x "${IPKG_INSTROOT}/etc/uci-defaults/99-captive-monitor" ] && "${IPKG_INSTROOT}/etc/uci-defaults/99-captive-monitor"
${IPKG_INSTROOT}/etc/init.d/captive-monitor enable
${IPKG_INSTROOT}/etc/init.d/captive-monitor start
exit 0
EOL
chmod +x /tmp/opkg-feed/postinst

# Create the IPK
cd /tmp/opkg-feed
find . -type f -not -path './control' -not -path './postinst' | sort | tar --no-recursion -czf data.tar.gz -T -
echo "2.0" > debian-binary
tar czf openwrt-captive-monitor_0.1.2-1_all.ipk ./control ./data.tar.gz ./postinst ./debian-binary

# Create Packages file
cat > /tmp/opkg-feed/Packages <<EOL
Package: openwrt-captive-monitor
Version: 0.1.2-1
Depends: dnsmasq, curl
Architecture: all
Maintainer: OpenWrt Captive Monitor Team
Filename: openwrt-captive-monitor_0.1.2-1_all.ipk
Size: $(stat -c%s /tmp/opkg-feed/openwrt-captive-monitor_0.1.2-1_all.ipk)
SHA256sum: $(sha256sum /tmp/opkg-feed/openwrt-captive-monitor_0.1.2-1_all.ipk | cut -d' ' -f1)
Description: Captive portal connectivity monitor and auto-redirect helper
EOL

gzip -c /tmp/opkg-feed/Packages > /tmp/opkg-feed/Packages.gz

echo "Package built: /tmp/opkg-feed/openwrt-captive-monitor_0.1.2-1_all.ipk"
echo "To install on the router, run:"
echo "  scp /tmp/opkg-feed/openwrt-captive-monitor_0.1.2-1_all.ipk root@192.168.35.170:/tmp/"
echo "  ssh root@192.168.35.170 'opkg install /tmp/openwrt-captive-monitor_0.1.2-1_all.ipk'"
