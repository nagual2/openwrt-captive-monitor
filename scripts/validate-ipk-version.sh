#!/bin/sh
# shellcheck shell=ash
# Minimal .ipk Version field validation.
#
# This helper is intentionally conservative: it only checks that the
# built .ipk archive contains control metadata with a non-empty
# "Version:" field and prints it for logging. It does NOT enforce:
#   - any particular date-based scheme,
#   - dev vs. release suffix rules,
#   - tag/metadata consistency.
#
# That means CI will not fail because of version/tag mismatches or
# missing "-dev" suffixes. The goal is simply to catch obviously
# broken packages that are missing version metadata entirely.
#
# Usage:
#   validate-ipk-version.sh <ipk_file> [context]
#
# Arguments:
#   ipk_file  Path to .ipk package file
#   context   Optional free-form label (e.g. "main", "pr", "release")
#             used only for log messages; it has no effect on validation.

set -eu

# Enable pipefail where supported
if (set -o pipefail) 2> /dev/null; then
    # shellcheck disable=SC3040
    set -o pipefail
fi

if [ "${TRACE:-0}" = "1" ]; then
    set -x
fi

script_dir=$(cd "$(dirname "$0")" && pwd)

# Source color library for consistent output
# shellcheck source=scripts/lib/colors.sh
. "$script_dir/lib/colors.sh"

print_usage() {
    cat << 'EOF'
Usage: validate-ipk-version.sh <ipk_file> [context]

Validate that an .ipk archive contains control metadata with a non-empty
Version field. The optional context argument is used only for logging
and does not affect validation rules.

Arguments:
  ipk_file   Path to .ipk package file
  context    Optional label (e.g., main, pr, release) for log messages

Exit codes:
  0: Validation passed
  1: Validation failed or error (e.g., missing Version field)
EOF
}

require_command() {
    cmd="$1"
    if ! command -v "$cmd" > /dev/null 2>&1; then
        printf "%serror:%s required command '%s' not found in PATH\n" "$RED" "$NC" "$cmd" >&2
        exit 1
    fi
}

# We only need a very small set of tools
require_command ar
require_command tar
require_command grep
require_command mktemp

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    print_usage >&2
    exit 1
fi

ipk_file="$1"
context="${2:-}"

if [ ! -f "$ipk_file" ]; then
    printf "%serror:%s IPK file not found: %s\n" "$RED" "$NC" "$ipk_file" >&2
    exit 1
fi

printf "%s=== Validating IPK Version metadata ===%s\n" "$CYAN" "$NC"
printf "Package: %s\n" "$ipk_file"
if [ -n "$context" ]; then
    printf "Context: %s\n" "$context"
fi
printf "\n"

# Temporary directory path (created lazily when needed)
temp_dir=""

# shellcheck disable=SC2317  # cleanup is invoked via trap
cleanup() {
    if [ -n "$temp_dir" ] && [ -d "$temp_dir" ]; then
        rm -rf "$temp_dir"
    fi
}

trap 'cleanup' EXIT INT TERM

# Create temporary directory for extraction
temp_dir=$(mktemp -d)

work_dir="$temp_dir/ipk"
mkdir -p "$work_dir"

# Resolve IPK path to an absolute path so extraction works from any CWD
case "$ipk_file" in
    /*) ipk_path="$ipk_file" ;;
    *) ipk_path="$(pwd)/$ipk_file" ;;
esac

# Extract .ipk archive (ar archive)
(
    cd "$work_dir"
    ar x "$ipk_path" 2> /dev/null
) || {
    printf "%serror:%s failed to extract IPK archive\n" "$RED" "$NC" >&2
    exit 1
}

# Check for control archive
if [ ! -f "$work_dir/control.tar.gz" ]; then
    printf "%serror:%s control.tar.gz not found in IPK\n" "$RED" "$NC" >&2
    exit 1
fi

# Extract control archive
control_dir="$temp_dir/control"
mkdir -p "$control_dir"
if ! tar -xzf "$work_dir/control.tar.gz" -C "$control_dir" 2> /dev/null; then
    printf "%serror:%s failed to extract control archive\n" "$RED" "$NC" >&2
    exit 1
fi

# Find control file
control_file=""
if [ -f "$control_dir/control" ]; then
    control_file="$control_dir/control"
else
    control_file=$(find "$control_dir" -type f -name control 2> /dev/null | head -n 1 || true)
fi

if [ -z "$control_file" ] || [ ! -f "$control_file" ]; then
    printf "%serror:%s control file not found in package\n" "$RED" "$NC" >&2
    exit 1
fi

printf "%sControl metadata:%s\n" "$BLUE" "$NC"
cat "$control_file"
printf "\n"

# Extract Version field from control file
version=$(grep '^Version:' "$control_file" | head -n 1 | sed 's/^Version:[[:space:]]*//' || true)

if [ -z "$version" ]; then
    printf "%serror:%s Version field not found or empty in control file\n" "$RED" "$NC" >&2
    exit 1
fi

printf "%sExtracted Version:%s %s\n" "$YELLOW" "$NC" "$version"
printf "%sNote:%s no additional semantic version checks are enforced.\n" "$BLUE" "$NC"
printf "%s=== Validation Summary: PASSED ===%s\n" "$GREEN" "$NC"

exit 0
