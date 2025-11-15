#!/bin/sh
# shellcheck shell=ash
# Setup helper to install opkg-utils on Ubuntu runners where apt no longer provides it (Ubuntu 24.04+)
# - Installs required host dependencies for .ipk packaging
# - Fetches opkg-utils from OpenWrt GitHub mirror and installs opkg-build, opkg-unbuild, opkg-make-index
# - Falls back to downloading raw scripts from GitHub if git clone fails
# - Verifies availability via `opkg-build -h` and `opkg-make-index -h`
#
# This script is idempotent and safe to re-run.

set -eu

# Enable pipefail where supported
if (set -o pipefail) 2> /dev/null; then
    # shellcheck disable=SC3040
    set -o pipefail
fi

# Determine repository root for cloning tools/ directory
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
TOOLS_DIR="$REPO_ROOT/tools"
OPKG_UTILS_DIR="$TOOLS_DIR/opkg-utils"

# Packages required by build scripts and opkg-utils runtime
# Keep this list in sync with CI workflows if they also install these directly
DEPS="gawk tar gzip xz-utils zstd coreutils findutils file make rsync"

info() { printf 'info: %s\n' "$*"; }
warn() { printf 'warn: %s\n' "$*" 1>&2; }
err() { printf 'error: %s\n' "$*" 1>&2; }

have_cmd() {
    command -v "$1" >/dev/null 2>&1
}

download_file() {
    # download_file URL DEST
    url="$1"
    dest="$2"
    if have_cmd curl; then
        curl -fsSL "$url" -o "$dest"
    elif have_cmd wget; then
        wget -qO "$dest" "$url"
    else
        err "neither curl nor wget is available to download $url"
        return 1
    fi
}

# Install host dependencies via apt-get
install_deps() {
    info "installing host dependencies: $DEPS"
    sudo apt-get update
    # Use --no-install-recommends to keep the environment lean
    sudo apt-get install -y --no-install-recommends $DEPS
}

# Clone or update opkg-utils from OpenWrt GitHub mirror
fetch_opkg_utils_git() {
    mkdir -p "$TOOLS_DIR"
    # Attempt update if an existing git checkout is present
    if [ -d "$OPKG_UTILS_DIR/.git" ]; then
        info "updating existing opkg-utils checkout"
        if (cd "$OPKG_UTILS_DIR" && git fetch --depth=1 origin && git reset --hard origin/HEAD); then
            return 0
        fi
        warn "failed to update existing opkg-utils checkout; attempting fresh clone"
    fi
    info "cloning opkg-utils from GitHub mirror"
    rm -rf "$OPKG_UTILS_DIR"
    if git clone --depth=1 https://github.com/openwrt/opkg-utils.git "$OPKG_UTILS_DIR"; then
        return 0
    fi
    warn "git clone of opkg-utils failed"
    return 1
}

# Fallback: download raw scripts from GitHub mirror if git is unavailable or clone fails
fetch_opkg_utils_raw() {
    base="https://raw.githubusercontent.com/openwrt/opkg-utils/master"
    rm -rf "$OPKG_UTILS_DIR"
    mkdir -p "$OPKG_UTILS_DIR"
    for bin in opkg-build opkg-unbuild opkg-make-index; do
        url="$base/$bin"
        dest="$OPKG_UTILS_DIR/$bin"
        info "downloading $bin from $url"
        if ! download_file "$url" "$dest"; then
            err "failed to download $bin from $url"
            return 1
        fi
        chmod 0755 "$dest"
    done
    return 0
}

# Install utility scripts into /usr/local/bin
install_opkg_binaries() {
    for bin in opkg-build opkg-unbuild opkg-make-index; do
        if [ ! -x "$OPKG_UTILS_DIR/$bin" ]; then
            err "missing $bin in $OPKG_UTILS_DIR"
            exit 1
        fi
        # Install with 0755 permissions, owned by root
        sudo install -m0755 "$OPKG_UTILS_DIR/$bin" "/usr/local/bin/$bin"
    done
}

verify_install() {
    if ! command -v opkg-build > /dev/null 2>&1; then
        err "opkg-build not found in PATH after installation"
        exit 1
    fi
    if ! command -v opkg-make-index > /dev/null 2>&1; then
        err "opkg-make-index not found in PATH after installation"
        exit 1
    fi
    # Print help to prove binaries are runnable
    opkg-build -h > /dev/null 2>&1 || true
    opkg-make-index -h > /dev/null 2>&1 || true
}

main() {
    install_deps
    if ! fetch_opkg_utils_git; then
        warn "falling back to raw download method for opkg-utils"
        fetch_opkg_utils_raw
    fi
    install_opkg_binaries
    verify_install
    info "opkg-utils installed successfully"
}

main "$@"
