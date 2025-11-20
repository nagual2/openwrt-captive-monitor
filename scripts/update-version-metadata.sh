#!/bin/sh
# shellcheck shell=ash
# Update repository metadata version fields in a synchronized, idempotent way.
#
# This helper updates:
#   - The root VERSION file
#   - PKG_VERSION in package/openwrt-captive-monitor/Makefile
#
# It accepts a single argument in the form YYYY.M.D.N (date-based version
# matching the auto-version tag scheme without the leading "v"). The script:
#   1. Validates the format against a strict date regex
#   2. Updates VERSION and PKG_VERSION
#   3. Prints a git diff for the touched files (when git is available)
#   4. Is safe to run repeatedly (no-op when both values already match)

set -eu

# Enable pipefail where supported (BusyBox ash compatible)
if (set -o pipefail) 2> /dev/null; then
	# shellcheck disable=SC3040
	set -o pipefail
fi

if [ "${TRACE:-0}" = "1" ]; then
	set -x
fi

script_dir=$(cd "$(dirname "$0")" && pwd)
repo_root=$(cd "$script_dir/.." && pwd)

# shellcheck source=lib/colors.sh
. "$script_dir/lib/colors.sh"

print_usage() {
	cat << 'EOF'
Usage: update-version-metadata.sh <YYYY.M.D.N>

Update VERSION and PKG_VERSION metadata to the provided date-based version.

Arguments:
  YYYY.M.D.N  Date-based version matching the auto-version tag scheme
              (e.g., 2025.1.15.1), without leading "v".

Behavior:
  - Validates the version format using a strict date regex
  - Writes the version to the root VERSION file
  - Updates PKG_VERSION in package/openwrt-captive-monitor/Makefile
  - Prints a git diff for the updated files when git is available
  - No-op when both VERSION and PKG_VERSION already match the argument
EOF
}

if [ "$#" -ne 1 ]; then
	printf '%serror:%s expected exactly one argument (YYYY.M.D.N)\n' "$RED" "$NC" >&2
	print_usage >&2
	exit 1
fi

new_version=$1

# Regex: YYYY.M.D.N
#   - YYYY: 4-digit year
#   - M:   month 1-12 (no leading zero)
#   - D:   day   1-31 (no leading zero)
#   - N:   sequence number (one or more digits)
version_pattern='^[0-9]{4}\.(1[0-2]|[1-9])\.(3[01]|[12][0-9]|[1-9])\.[0-9]+$'

if ! printf '%s\n' "$new_version" | grep -Eq "$version_pattern"; then
	printf '%serror:%s invalid version format: %s\n' "$RED" "$NC" "$new_version" >&2
	printf '%sExpected format:%s YYYY.M.D.N (e.g., 2025.1.15.1)\n' "$YELLOW" "$NC" >&2
	exit 1
fi

version_file="$repo_root/VERSION"
pkg_makefile="$repo_root/package/openwrt-captive-monitor/Makefile"

if [ ! -f "$pkg_makefile" ]; then
	printf '%serror:%s package Makefile not found: %s\n' "$RED" "$NC" "$pkg_makefile" >&2
	exit 1
fi

current_version=""
if [ -f "$version_file" ]; then
	# Use the first line as the current version, strip any trailing CR
	current_version=$(sed -n '1p' "$version_file" | tr -d '\r')
fi

current_pkg_version=$(grep '^PKG_VERSION:=' "$pkg_makefile" 2> /dev/null | head -n 1 | sed 's/^PKG_VERSION:=[[:space:]]*//')

if [ "$current_version" = "$new_version" ] && [ "$current_pkg_version" = "$new_version" ]; then
	printf '%sVersion metadata already up to date:%s %s\n' "$GREEN" "$NC" "$new_version"
	exit 0
fi

printf '%sUpdating version metadata to:%s %s\n' "$BLUE" "$NC" "$new_version"

# Update VERSION file
printf '%s\n' "$new_version" > "$version_file"

# Ensure PKG_VERSION line exists before attempting replacement
if ! grep -q '^PKG_VERSION:=' "$pkg_makefile"; then
	printf '%serror:%s PKG_VERSION line not found in %s\n' "$RED" "$NC" "$pkg_makefile" >&2
	exit 1
fi

# Safely rewrite PKG_VERSION line
# Note: new_version contains only digits and dots, so sed replacement is safe
_tmp_file=$(mktemp)
if ! sed "s/^PKG_VERSION:=.*/PKG_VERSION:=$new_version/" "$pkg_makefile" > "$_tmp_file"; then
	rm -f "$_tmp_file"
	printf '%serror:%s failed to update PKG_VERSION in %s\n' "$RED" "$NC" "$pkg_makefile" >&2
	exit 1
fi

mv "$_tmp_file" "$pkg_makefile"

# Print diff for debugging/visibility when git is available
if command -v git > /dev/null 2>&1; then
	printf '%sMetadata diff (git):%s\n' "$CYAN" "$NC"
	(
		cd "$repo_root"
		git diff -- VERSION package/openwrt-captive-monitor/Makefile || true
	)
else
	printf '%snote:%s git not found in PATH; skipping diff output\n' "$YELLOW" "$NC"
fi

printf '%sVersion metadata update complete.%s\n' "$GREEN" "$NC"
