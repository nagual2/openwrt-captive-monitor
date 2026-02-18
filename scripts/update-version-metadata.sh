#!/bin/sh
# update-version-metadata.sh — Canonical helper to bump the root VERSION file
# and PKG_VERSION in package/openwrt-captive-monitor/Makefile in a synchronised,
# date-based way.
#
# Usage:
#   ./scripts/update-version-metadata.sh <YYYY.M.D.N>
#
# The version argument must match the date-based format used by the project:
#   YYYY.M.D.N  – where N is a small positive integer sequence number for the day.
#
# Examples:
#   ./scripts/update-version-metadata.sh 2026.2.18.1
#   ./scripts/update-version-metadata.sh 2026.2.18.2
#
# The script is intentionally written as POSIX sh / BusyBox-ash-compatible
# (no bashisms) to match the project's shell scripting conventions.

set -eu

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

usage() {
    sed -n 's/^# //p' "$0" | head -20
    exit 1
}

# ---------------------------------------------------------------------------
# Validate argument
# ---------------------------------------------------------------------------

if [ $# -ne 1 ]; then
    usage
fi

NEW_VERSION="$1"

# Validate the version matches YYYY.M.D.N (no leading zeroes in M, D, or N).
# The regex allows single or multi-digit month/day/sequence numbers.
if ! printf '%s\n' "$NEW_VERSION" | grep -qE '^[0-9]{4}\.[1-9][0-9]*\.[1-9][0-9]*\.[0-9]+$'; then
    die "Version '$NEW_VERSION' does not match the required format YYYY.M.D.N (e.g. 2026.2.18.1)"
fi

# ---------------------------------------------------------------------------
# Locate project root (the directory that contains this script's parent)
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

VERSION_FILE="$PROJECT_ROOT/VERSION"
PKG_MAKEFILE="$PROJECT_ROOT/package/openwrt-captive-monitor/Makefile"

# Verify both target files exist before making any changes.
[ -f "$VERSION_FILE" ] || die "VERSION file not found at: $VERSION_FILE"
[ -f "$PKG_MAKEFILE" ] || die "Package Makefile not found at: $PKG_MAKEFILE"

# ---------------------------------------------------------------------------
# Read current values for informational output
# ---------------------------------------------------------------------------

CURRENT_VERSION="$(tr -d '\r\n' < "$VERSION_FILE")"
CURRENT_PKG_VERSION="$(sed -n 's/^PKG_VERSION:=//p' "$PKG_MAKEFILE" | tr -d '\r\n')"

printf 'Updating version metadata:\n'
printf '  Current VERSION    : %s\n' "$CURRENT_VERSION"
printf '  Current PKG_VERSION: %s\n' "$CURRENT_PKG_VERSION"
printf '  New version        : %s\n' "$NEW_VERSION"

# ---------------------------------------------------------------------------
# Update VERSION file
# ---------------------------------------------------------------------------

printf '%s\n' "$NEW_VERSION" > "$VERSION_FILE"
printf 'Updated %s\n' "$VERSION_FILE"

# ---------------------------------------------------------------------------
# Update PKG_VERSION in the OpenWrt package Makefile
#
# We use sed to replace the PKG_VERSION line in-place.  The pattern targets
# the exact "PKG_VERSION:=…" assignment that the OpenWrt build system uses.
# ---------------------------------------------------------------------------

# Use a tmp file for portability (sed -i differs across platforms).
TMP_MAKEFILE="${PKG_MAKEFILE}.tmp"
sed "s/^PKG_VERSION:=.*/PKG_VERSION:=${NEW_VERSION}/" "$PKG_MAKEFILE" > "$TMP_MAKEFILE"
mv "$TMP_MAKEFILE" "$PKG_MAKEFILE"
printf 'Updated %s\n' "$PKG_MAKEFILE"

# ---------------------------------------------------------------------------
# Verify the update was applied correctly
# ---------------------------------------------------------------------------

UPDATED_PKG_VERSION="$(sed -n 's/^PKG_VERSION:=//p' "$PKG_MAKEFILE" | tr -d '\r\n')"
UPDATED_VERSION="$(tr -d '\r\n' < "$VERSION_FILE")"

if [ "$UPDATED_VERSION" != "$NEW_VERSION" ]; then
    die "VERSION file update verification failed: got '$UPDATED_VERSION', expected '$NEW_VERSION'"
fi

if [ "$UPDATED_PKG_VERSION" != "$NEW_VERSION" ]; then
    die "PKG_VERSION update verification failed: got '$UPDATED_PKG_VERSION', expected '$NEW_VERSION'"
fi

printf 'Version metadata updated successfully to %s\n' "$NEW_VERSION"
