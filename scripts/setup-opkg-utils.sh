#!/bin/sh
# shellcheck shell=ash
# Setup helper to install opkg-utils on Ubuntu runners where apt no longer provides it (Ubuntu 24.04+)
# - Installs required host dependencies for .ipk packaging
# - Prefers an anonymous HTTPS snapshot tarball from the canonical git.openwrt.org repository
#   to install opkg-build, opkg-unbuild, and opkg-make-index
# - Falls back to downloading raw scripts from git.openwrt.org if the tarball fetch fails
# - Optionally uses a git clone from git.openwrt.org when OPKG_UTILS_ALLOW_GIT=1 (for local
#   development environments)
# - Verifies availability via `opkg-build -h` and `opkg-make-index -h`
#
# This script is idempotent and safe to re-run.

set -eu

# Enable pipefail where supported
if (set -o pipefail) 2> /dev/null; then
    # shellcheck disable=SC3040
    set -o pipefail
fi

# Determine repository root for installing tools/ directory
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
TOOLS_DIR="$REPO_ROOT/tools"
OPKG_UTILS_DIR="$TOOLS_DIR/opkg-utils"
# Default location where opkg-utils binaries will be found after fetch.
OPKG_UTILS_BIN_DIR="$OPKG_UTILS_DIR"
# Track how we fetched opkg-utils (tarball, raw, git) for diagnostics.
OPKG_UTILS_FETCH_MODE=""

# Upstream opkg-utils repository and raw script locations.
# These use anonymous HTTPS URLs suitable for non-interactive CI environments.
OPKG_UTILS_REPO="https://git.openwrt.org/project/opkg-utils.git"
OPKG_UTILS_BRANCH="master"
OPKG_UTILS_TARBALL_URL="https://git.openwrt.org/?p=project/opkg-utils.git;a=snapshot;h=HEAD;sf=tgz"
OPKG_UTILS_RAW_BASE="https://git.openwrt.org/project/opkg-utils.git/plain"
OPKG_UTILS_RAW_OPKG_BUILD="$OPKG_UTILS_RAW_BASE/opkg-build"

# Packages required by build scripts and opkg-utils runtime
# Keep this list in sync with CI workflows if they also install these directly
DEPS="gawk tar gzip xz-utils zstd coreutils findutils file make rsync"

# Source shared color definitions for consistent logging output.
# shellcheck source=lib/colors.sh
# shellcheck disable=SC1091
. "$SCRIPT_DIR/lib/colors.sh"

info() {
    printf '%s[INFO]%s %s\n' "$BLUE" "$NC" "$*"
}
warn() {
    printf '%s[WARN]%s %s\n' "$YELLOW" "$NC" "$*" 1>&2
}
err() {
    printf '%s[ERROR]%s %s\n' "$RED" "$NC" "$*" 1>&2
}

have_cmd() {
    command -v "$1" > /dev/null 2>&1
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

# Preferred: fetch opkg-utils via anonymous HTTPS tarball (suitable for CI)
fetch_opkg_utils_tarball() {
    mkdir -p "$TOOLS_DIR"

    tmp_tar=$(mktemp)
    info "downloading opkg-utils tarball from $OPKG_UTILS_TARBALL_URL"
    if ! download_file "$OPKG_UTILS_TARBALL_URL" "$tmp_tar"; then
        warn "failed to download opkg-utils tarball from $OPKG_UTILS_TARBALL_URL"
        rm -f "$tmp_tar"
        return 1
    fi

    rm -rf "$OPKG_UTILS_DIR"
    mkdir -p "$OPKG_UTILS_DIR"

    # Extract and strip leading directory component from archive
    if ! tar -xzf "$tmp_tar" --strip-components=1 -C "$OPKG_UTILS_DIR"; then
        warn "failed to extract opkg-utils tarball"
        rm -f "$tmp_tar"
        return 1
    fi

    rm -f "$tmp_tar"
    OPKG_UTILS_BIN_DIR="$OPKG_UTILS_DIR"
    OPKG_UTILS_FETCH_MODE="tarball"
    return 0
}

# Optional: clone or update opkg-utils from the canonical git.openwrt.org repository
# (opt-in via OPKG_UTILS_ALLOW_GIT=1). This is primarily intended for local development
# and is not used in CI by default.
fetch_opkg_utils_git() {
    # Honor OPKG_UTILS_ALLOW_GIT=1 as an explicit opt-in, defaulting to disabled in CI.
    if [ "${OPKG_UTILS_ALLOW_GIT:-0}" != "1" ]; then
        warn "git-based opkg-utils fetch is disabled (set OPKG_UTILS_ALLOW_GIT=1 to enable)"
        return 1
    fi

    mkdir -p "$TOOLS_DIR"

    # Bail out quickly if git is not available.
    if ! have_cmd git; then
        warn "git command not found; skipping git-based opkg-utils fetch"
        return 1
    fi

    # Attempt update if an existing git checkout is present.
    if [ -d "$OPKG_UTILS_DIR/.git" ]; then
        info "updating existing opkg-utils checkout at $OPKG_UTILS_DIR"
        if (cd "$OPKG_UTILS_DIR" && GIT_TERMINAL_PROMPT=0 git fetch --depth=1 origin && GIT_TERMINAL_PROMPT=0 git reset --hard "origin/${OPKG_UTILS_BRANCH}"); then
            OPKG_UTILS_BIN_DIR="$OPKG_UTILS_DIR"
            OPKG_UTILS_FETCH_MODE="git"
            return 0
        fi
        warn "failed to update existing opkg-utils checkout; attempting fresh clone"
    fi

    info "cloning opkg-utils from $OPKG_UTILS_REPO using anonymous HTTPS"
    rm -rf "$OPKG_UTILS_DIR"
    if GIT_TERMINAL_PROMPT=0 git clone --branch "$OPKG_UTILS_BRANCH" --depth=1 "$OPKG_UTILS_REPO" "$OPKG_UTILS_DIR"; then
        OPKG_UTILS_BIN_DIR="$OPKG_UTILS_DIR"
        OPKG_UTILS_FETCH_MODE="git"
        return 0
    fi

    warn "git clone of opkg-utils failed"
    return 1
}

# Fallback: download raw scripts from git.openwrt.org when tarball fetch is unavailable
fetch_opkg_utils_raw() {
    info "using raw download method for opkg-utils from $OPKG_UTILS_RAW_BASE"
    rm -rf "$OPKG_UTILS_DIR"
    mkdir -p "$OPKG_UTILS_DIR/bin"

    OPKG_UTILS_BIN_DIR="$OPKG_UTILS_DIR/bin"
    OPKG_UTILS_FETCH_MODE="raw"

    for bin in opkg-build opkg-unbuild opkg-make-index; do
        case "$bin" in
        opkg-build)
            url="$OPKG_UTILS_RAW_OPKG_BUILD"
            ;;
        *)
            url="$OPKG_UTILS_RAW_BASE/$bin"
            ;;
        esac
        dest="$OPKG_UTILS_BIN_DIR/$bin"
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
        if [ ! -x "$OPKG_UTILS_BIN_DIR/$bin" ]; then
            err "missing $bin in $OPKG_UTILS_BIN_DIR"
            exit 1
        fi
        # Install with 0755 permissions, owned by root
        sudo install -m0755 "$OPKG_UTILS_BIN_DIR/$bin" "/usr/local/bin/$bin"
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

    # Preferred path: download and unpack tarball from git.openwrt.org (no git required)
    if ! fetch_opkg_utils_tarball; then
        warn "tarball fetch for opkg-utils failed, falling back to raw script download"
        if ! fetch_opkg_utils_raw; then
            warn "raw script download for opkg-utils failed"

            # Last resort for local environments that explicitly allow git
            if [ "${OPKG_UTILS_ALLOW_GIT:-0}" = "1" ]; then
                warn "attempting git-based opkg-utils fetch from $OPKG_UTILS_REPO because OPKG_UTILS_ALLOW_GIT=1"
                if ! fetch_opkg_utils_git; then
                    err "failed to fetch opkg-utils via tarball, raw download, or git; aborting"
                    exit 1
                fi
            else
                err "failed to fetch opkg-utils via tarball or raw download from git.openwrt.org; set OPKG_UTILS_ALLOW_GIT=1 to enable git-based fallback from $OPKG_UTILS_REPO"
                exit 1
            fi
        fi
    fi

    install_opkg_binaries
    verify_install
    info "opkg-utils installed successfully using fetch mode: ${OPKG_UTILS_FETCH_MODE:-unknown}"
}

main "$@"
