#!/bin/sh
# shellcheck shell=ash
# Setup helper to install opkg-utils on Ubuntu runners where apt no longer provides it (Ubuntu 24.04+)
# - Installs required host dependencies for .ipk packaging
# - Fetches opkg-utils from OpenWrt upstream and installs opkg-build, opkg-unbuild, opkg-make-index
# - Verifies availability via `opkg-build -h`
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

# Install host dependencies via apt-get
install_deps() {
    info "installing host dependencies: $DEPS"
    sudo apt-get update
    # Use --no-install-recommends to keep the environment lean
    sudo apt-get install -y --no-install-recommends $DEPS
}

# Clone or update opkg-utils from OpenWrt upstream
fetch_opkg_utils() {
    mkdir -p "$TOOLS_DIR"
    if [ -d "$OPKG_UTILS_DIR/.git" ]; then
        info "updating existing opkg-utils checkout"
        (cd "$OPKG_UTILS_DIR" && git fetch --depth=1 origin && git reset --hard origin/HEAD)
    else
        info "cloning opkg-utils from upstream"
        rm -rf "$OPKG_UTILS_DIR"
        git clone --depth=1 https://git.openwrt.org/project/opkg-utils.git "$OPKG_UTILS_DIR"
    fi
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
    if ! command -v opkg-build >/dev/null 2>&1; then
        err "opkg-build not found in PATH after installation"
        exit 1
    fi
    # Print help to prove binary is runnable
    opkg-build -h >/dev/null 2>&1 || true
}

main() {
    install_deps
    fetch_opkg_utils
    install_opkg_binaries
    verify_install
    info "opkg-utils installed successfully"
}

main "$@"
