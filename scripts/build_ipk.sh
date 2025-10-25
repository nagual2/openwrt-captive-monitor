#!/bin/sh
# shellcheck shell=ash
# shellcheck disable=SC3043 # BusyBox ash and bash-compatible shells provide 'local'
set -eu

if (set -o pipefail) 2> /dev/null; then
    # shellcheck disable=SC3040
    set -o pipefail
fi

usage() {
    cat << 'EOF'
Usage: scripts/build_ipk.sh [--arch <name>] [--feed-root <path>]

Options:
  --arch <name>       Architecture string to embed into the .ipk (default: value of PKG_ARCH or "all")
  --feed-root <path>  Output directory for the opkg feed (default: <repo>/dist/opkg)
  -h, --help          Show this help message

The script builds an .ipk package directly from the repository sources and
creates/updates an opkg feed containing Packages and Packages.gz indexes.
EOF
}

script_dir=$(cd "$(dirname "$0")" && pwd)
repo_root=$(cd "$script_dir/.." && pwd)
pkg_root="$repo_root/package/openwrt-captive-monitor"
pkg_makefile="$pkg_root/Makefile"
files_dir="$pkg_root/files"

if [ ! -f "$pkg_makefile" ]; then
    echo "error: expected Makefile at $pkg_makefile" >&2
    exit 1
fi

if [ ! -d "$files_dir" ]; then
    echo "error: expected package files directory at $files_dir" >&2
    exit 1
fi

parse_make_var() {
    local key="$1"
    awk -F':=' -v key="$key" '
        $1 == key {
            gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2)
            gsub(/\r/, "", $2)
            print $2
            exit
        }
    ' "$pkg_makefile"
}

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

extract_description_block() {
    awk '
        /^define Package\/openwrt-captive-monitor\/description$/ {inside=1; next}
        inside && /^endef$/ {inside=0}
        inside {
            sub(/^[[:space:]]*/, "", $0)
            print
        }
    ' "$pkg_makefile"
}

pkg_name=$(parse_make_var "PKG_NAME")
[ -n "$pkg_name" ] || pkg_name="openwrt-captive-monitor"

pkg_version=$(parse_make_var "PKG_VERSION")
[ -n "$pkg_version" ] || pkg_version="0.0.0"

pkg_release=$(parse_make_var "PKG_RELEASE")
[ -n "$pkg_release" ] || pkg_release="1"

pkg_arch_default=$(parse_make_var "PKG_ARCH")
[ -n "$pkg_arch_default" ] || pkg_arch_default="all"

pkg_license=$(parse_make_var "PKG_LICENSE")
[ -n "$pkg_license" ] || pkg_license="MIT"

pkg_maintainer=$(parse_make_var "PKG_MAINTAINER")
[ -n "$pkg_maintainer" ] || pkg_maintainer="Unknown"

pkg_title=$(parse_package_field "TITLE")
[ -n "$pkg_title" ] || pkg_title="OpenWrt captive portal monitor"

pkg_section=$(parse_package_field "SECTION")
[ -n "$pkg_section" ] || pkg_section="net"

pkg_category=$(parse_package_field "CATEGORY")

pkg_depends=$(parse_package_field "DEPENDS")
if [ -n "$pkg_depends" ]; then
    pkg_depends=$(printf '%s\n' "$pkg_depends" | sed 's/[+]//g; s/[[:space:]]\+/ /g; s/^ //; s/ $//; s/ /, /g')
fi

description_block=$(extract_description_block)

arch="$pkg_arch_default"
feed_root="$repo_root/dist/opkg"

while [ $# -gt 0 ]; do
    case "$1" in
        --arch)
            [ $# -ge 2 ] || {
                echo "error: --arch requires a value" >&2
                usage
                exit 1
            }
            arch="$2"
            shift 2
            ;;
        --feed-root)
            [ $# -ge 2 ] || {
                echo "error: --feed-root requires a value" >&2
                usage
                exit 1
            }
            feed_root="$2"
            shift 2
            ;;
        -h | --help)
            usage
            exit 0
            ;;
        *)
            echo "error: unknown option $1" >&2
            usage
            exit 1
            ;;
    esac
done

feed_dir="$feed_root/$arch"
mkdir -p "$feed_dir"

build_dir=$(mktemp -d)
cleanup() {
    rm -rf "$build_dir"
}
trap cleanup EXIT INT TERM HUP

data_dir="$build_dir/data"
control_dir="$build_dir/control"
mkdir -p "$data_dir" "$control_dir"

# Copy payload files
cp -a "$files_dir/." "$data_dir/"

# Ensure key executables are marked correctly when the copy umask interferes
if [ -f "$data_dir/usr/sbin/openwrt_captive_monitor" ]; then
    chmod 0755 "$data_dir/usr/sbin/openwrt_captive_monitor"
fi
if [ -f "$data_dir/etc/init.d/captive-monitor" ]; then
    chmod 0755 "$data_dir/etc/init.d/captive-monitor"
fi
if [ -f "$data_dir/etc/uci-defaults/99-captive-monitor" ]; then
    chmod 0755 "$data_dir/etc/uci-defaults/99-captive-monitor"
fi

installed_size=$(du -sk "$data_dir" | awk '{print $1}')
[ -n "$installed_size" ] || installed_size=0

control_file="$control_dir/control"
{
    echo "Package: $pkg_name"
    echo "Version: ${pkg_version}-${pkg_release}"
    echo "Architecture: $arch"
    echo "Maintainer: $pkg_maintainer"
    echo "License: $pkg_license"
    echo "Section: $pkg_section"
    [ -n "$pkg_category" ] && echo "Category: $pkg_category"
    echo "Priority: optional"
    [ -n "$pkg_depends" ] && echo "Depends: $pkg_depends"
    echo "Source: https://github.com/nagual2/openwrt-captive-monitor"
    echo "Installed-Size: $installed_size"
    echo "Description: $pkg_title"
    if [ -n "$description_block" ]; then
        printf '%s\n' "$description_block" | sed 's/^/ /'
    fi
} > "$control_file"

cat << 'EOF' > "$control_dir/postinst"
#!/bin/sh
if [ -z "$IPKG_INSTROOT" ]; then
    if [ -x /etc/uci-defaults/99-captive-monitor ]; then
        /etc/uci-defaults/99-captive-monitor || true
    fi
    /etc/init.d/captive-monitor disable >/dev/null 2>&1 || true
    /etc/init.d/captive-monitor stop >/dev/null 2>&1 || true
fi
exit 0
EOF

cat << 'EOF' > "$control_dir/prerm"
#!/bin/sh
if [ -z "$IPKG_INSTROOT" ]; then
    /etc/init.d/captive-monitor disable >/dev/null 2>&1 || true
    /etc/init.d/captive-monitor stop >/dev/null 2>&1 || true
fi
exit 0
EOF

cat << 'EOF' > "$control_dir/postrm"
#!/bin/sh
if [ -z "$IPKG_INSTROOT" ]; then
    /etc/init.d/captive-monitor stop >/dev/null 2>&1 || true
fi
exit 0
EOF

echo "/etc/config/captive-monitor" > "$control_dir/conffiles"

chmod 0755 "$control_dir/postinst" "$control_dir/prerm" "$control_dir/postrm"
chmod 0644 "$control_file" "$control_dir/conffiles"

(cd "$data_dir" && tar --numeric-owner --owner=0 --group=0 -czf "$build_dir/data.tar.gz" .)
(cd "$control_dir" && tar --numeric-owner --owner=0 --group=0 -czf "$build_dir/control.tar.gz" .)

echo "2.0" > "$build_dir/debian-binary"

output_ipk="$feed_dir/${pkg_name}_${pkg_version}-${pkg_release}_${arch}.ipk"
rm -f "$output_ipk"

(cd "$build_dir" && ar r "$output_ipk" debian-binary control.tar.gz data.tar.gz)

packages_file="$feed_dir/Packages"
rm -f "$packages_file" "$packages_file.gz"
: > "$packages_file"

for ipk in "$feed_dir"/*.ipk; do
    [ -f "$ipk" ] || continue
    tmpdir=$(mktemp -d)
    ar p "$ipk" control.tar.gz | tar -C "$tmpdir" -xz
    {
        cat "$tmpdir/control"
        echo "Filename: $(basename "$ipk")"
        echo "Size: $(stat -c%s "$ipk")"
        echo "MD5sum: $(md5sum "$ipk" | awk '{print $1}')"
        echo "SHA256sum: $(sha256sum "$ipk" | awk '{print $1}')"
        echo
    } >> "$packages_file"
    rm -rf "$tmpdir"
done

if command -v pigz > /dev/null 2>&1; then
    pigz -c "$packages_file" > "$packages_file.gz"
else
    gzip -c "$packages_file" > "$packages_file.gz"
fi

echo "Created package: $output_ipk"
echo "Updated feed index under: $feed_dir"
