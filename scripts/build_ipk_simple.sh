#!/bin/bash
# Simple IPK builder without opkg-utils dependency
# Creates .ipk packages manually using tar and gzip

set -euo pipefail

script_dir=$(cd "$(dirname "$0")" && pwd)
repo_root=$(cd "$script_dir/.." && pwd)
pkg_root="$repo_root/package/openwrt-captive-monitor"
pkg_makefile="$pkg_root/Makefile"
files_dir="$pkg_root/files"

# Parse Makefile variables
parse_make_var() {
    key="$1"
    awk -F':=' -v key="$key" '
        $1 == key {
            gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2)
            gsub(/\r/, "", $2)
            print $2
            exit
        }
    ' "$pkg_makefile"
}

pkg_name=$(parse_make_var "PKG_NAME")
pkg_version=$(parse_make_var "PKG_VERSION")
pkg_release=$(parse_make_var "PKG_RELEASE")
pkg_arch="${1:-all}"

full_version="${pkg_version}-${pkg_release}"
output_dir="$repo_root/dist/opkg/$pkg_arch"
mkdir -p "$output_dir"

build_dir=$(mktemp -d)
trap "rm -rf '$build_dir'" EXIT

# Parse more metadata
parse_package_field() {
    local field="$1"
    awk -v field="$field" '
        /^define Package\/openwrt-captive-monitor$/ {inside=1; next}
        inside && /^endef$/ {inside=0}
        inside {
            pattern = "^[[:space:]]*" field ":="
            if ($0 ~ pattern) {
                sub(pattern, "", $0)
                gsub(/^[[:space:]]+|[[:space:]]+$/, "", $0)
                print
                exit
            }
        }
    ' "$pkg_makefile"
}

pkg_maintainer=$(parse_make_var "PKG_MAINTAINER")
pkg_license=$(parse_make_var "PKG_LICENSE")
pkg_title=$(parse_package_field "TITLE")
pkg_depends=$(parse_package_field "DEPENDS")
pkg_depends=$(echo "$pkg_depends" | sed 's/[+]//g; s/[[:space:]]\+/ /g; s/^ //; s/ $//; s/ /, /g')

# Calculate installed size
installed_size=$(du -sk "$files_dir" 2>/dev/null | awk '{print $1}' || echo "100")

# Create control file
control_dir="$build_dir/control"
mkdir -p "$control_dir"

cat > "$control_dir/control" << EOF
Package: $pkg_name
Version: $full_version
Architecture: $pkg_arch
Maintainer: ${pkg_maintainer:-OpenWrt Captive Monitor Team}
License: ${pkg_license:-MIT}
Section: net
Priority: optional
Depends: ${pkg_depends:-dnsmasq, curl, iptables}
Source: https://github.com/nagual2/openwrt-captive-monitor
Installed-Size: $installed_size
Description: ${pkg_title:-Captive portal connectivity monitor}
 openwrt-captive-monitor detects captive portals, applies DNS/HTTP redirects
 so authenticated clients can sign in, and restores normal routing once
 internet access is available again.
EOF

# Create postinst script
cat > "$control_dir/postinst" << 'EOF'
#!/bin/sh
if [ -z "$IPKG_INSTROOT" ]; then
    if [ -x /etc/uci-defaults/99-captive-monitor ]; then
        /etc/uci-defaults/99-captive-monitor || true
    fi
    /etc/init.d/captive-monitor disable > /dev/null 2>&1 || true
    /etc/init.d/captive-monitor stop > /dev/null 2>&1 || true
fi
exit 0
EOF

# Create prerm script
cat > "$control_dir/prerm" << 'EOF'
#!/bin/sh
if [ -z "$IPKG_INSTROOT" ]; then
    /etc/init.d/captive-monitor disable > /dev/null 2>&1 || true
    /etc/init.d/captive-monitor stop > /dev/null 2>&1 || true
fi
exit 0
EOF

# Create postrm script
cat > "$control_dir/postrm" << 'EOF'
#!/bin/sh
if [ -z "$IPKG_INSTROOT" ]; then
    /etc/init.d/captive-monitor stop > /dev/null 2>&1 || true
fi
exit 0
EOF

# Create conffiles
echo "/etc/config/captive-monitor" > "$control_dir/conffiles"

chmod 0755 "$control_dir/postinst" "$control_dir/prerm" "$control_dir/postrm"
chmod 0644 "$control_dir/control" "$control_dir/conffiles"

# Create data archive
data_dir="$build_dir/data"
mkdir -p "$data_dir"
cp -a "$files_dir/." "$data_dir/"

# Set permissions
chmod 0755 "$data_dir/usr/sbin/openwrt_captive_monitor" 2>/dev/null || true
chmod 0755 "$data_dir/etc/init.d/captive-monitor" 2>/dev/null || true
chmod 0755 "$data_dir/etc/uci-defaults/99-captive-monitor" 2>/dev/null || true

# Create control.tar.gz with all control files
(cd "$control_dir" && tar czf "$build_dir/control.tar.gz" .)

# Create data.tar.gz
(cd "$data_dir" && tar czf "$build_dir/data.tar.gz" .)

# Create debian-binary
echo "2.0" > "$build_dir/debian-binary"

# Create final .ipk (which is an ar archive)
output_ipk="$output_dir/${pkg_name}_${full_version}_${pkg_arch}.ipk"
(cd "$build_dir" && ar r "$output_ipk" debian-binary control.tar.gz data.tar.gz)

echo "Created: $output_ipk"
ls -lh "$output_ipk"

# Stage artifacts
export BUILD_NAME="${BUILD_NAME:-local-build}"
bash "$repo_root/scripts/stage_artifacts.sh" "$output_dir"
