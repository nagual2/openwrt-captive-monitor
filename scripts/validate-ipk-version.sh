#!/bin/sh
# shellcheck shell=ash
# Validate .ipk control metadata Version field against branch-specific rules
#
# Usage: validate-ipk-version.sh <ipk_file> <branch_type>
#   ipk_file: Path to .ipk package file
#   branch_type: Either "main" or "pr"
#
# Exit codes:
#   0: Validation passed
#   1: Validation failed or error
set -eu

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

# Temporary directory path (created lazily when needed)
# Defined early so cleanup can safely reference it even if creation fails
# or script exits before it's set.
temp_dir=""

# shellcheck disable=SC2317  # cleanup is invoked via trap
cleanup() {
    # Remove temp directory if it was created
    if [ -n "$temp_dir" ] && [ -d "$temp_dir" ]; then
        rm -rf "$temp_dir"
    fi
}

# Ensure cleanup runs on script exit or interruption
trap 'cleanup' EXIT INT TERM

print_usage() {
    cat << 'EOF'
Usage: validate-ipk-version.sh <ipk_file> <branch_type>

Validate .ipk control metadata Version field against branch-specific rules.

Arguments:
  ipk_file     Path to .ipk package file
  branch_type  One of "main", "pr", or "release"

Branch-specific rules:
  main:    Version must match ^[0-9][0-9\.]*-dev(-[0-9]{8}([0-9]{2})?)?$
           (must include -dev suffix)
  pr:      Version must match ^[0-9][0-9\.]*(-[0-9]{8}([0-9]{2})?)?$
           (must NOT include -dev suffix; non-main validation builds)
  release: Version must match ^[0-9][0-9\.]*(-[0-9]{8}([0-9]{2})?)?$
           (must NOT include -dev suffix; final tag-based releases)

Exit codes:
  0: Validation passed
  1: Validation failed or error
EOF
}

require_command() {
    local cmd="$1"
    if ! command -v "$cmd" > /dev/null 2>&1; then
        printf "%serror:%s required command '%s' not found in PATH\n" "$RED" "$NC" "$cmd" >&2
        exit 1
    fi
}

# Check required commands
require_command ar
require_command tar
require_command grep
require_command mktemp

if [ $# -lt 2 ]; then
    print_usage
    exit 1
fi

ipk_file="$1"
branch_type="$2"

if [ ! -f "$ipk_file" ]; then
    printf "%serror:%s IPK file not found: %s\n" "$RED" "$NC" "$ipk_file" >&2
    exit 1
fi

if [ "$branch_type" != "main" ] && [ "$branch_type" != "pr" ] && [ "$branch_type" != "release" ]; then
    printf "%serror:%s branch_type must be 'main', 'pr', or 'release', got: %s\n" "$RED" "$NC" "$branch_type" >&2
    exit 1
fi

printf "%s=== Validating IPK Version ===%s\n" "$CYAN" "$NC"
printf "Package: %s\n" "$ipk_file"
printf "Branch type: %s\n" "$branch_type"
printf "\n"

# Create temporary directory for extraction
temp_dir=$(mktemp -d)

work_dir="$temp_dir/ipk"
mkdir -p "$work_dir"

# Extract .ipk archive (ar archive)
(
    cd "$work_dir"
    ar x "$ipk_file" 2> /dev/null
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
tar -xzf "$work_dir/control.tar.gz" -C "$control_dir" 2> /dev/null || {
    printf "%serror:%s failed to extract control archive\n" "$RED" "$NC" >&2
    exit 1
}

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
version=$(grep '^Version:' "$control_file" | head -n 1 | sed 's/^Version: *//' || true)

if [ -z "$version" ]; then
    printf "%serror:%s Version field not found in control file\n" "$RED" "$NC" >&2
    exit 1
fi

printf "%sExtracted Version:%s %s\n" "$YELLOW" "$NC" "$version"
printf "\n"

# Validate version based on branch type
validation_passed=0

if [ "$branch_type" = "main" ]; then
    # Main branch: Version must include -dev suffix
    # Pattern: ^[0-9][0-9\.]*-dev(-[0-9]{8}([0-9]{2})?)?$
    printf "%sValidating main branch rules:%s\n" "$CYAN" "$NC"
    printf "  - Version must include '-dev' suffix\n"
    printf "  - Pattern: ^[0-9][0-9\\.]*-dev(-[0-9]{8}([0-9]{2})?)?$\n"
    printf "\n"

    # Check if version matches pattern
    # Using grep with extended regex for validation
    if printf '%s\n' "$version" | grep -Eq '^[0-9][0-9.]*-dev(-[0-9]{8}([0-9]{2})?)?$'; then
        validation_passed=1
        printf "%s✓ Validation PASSED:%s Version correctly includes '-dev' suffix\n" "$GREEN" "$NC"
    else
        printf "%s✗ Validation FAILED:%s Version does not match main branch pattern\n" "$RED" "$NC" >&2
        printf "  Expected: version with '-dev' suffix (e.g., 1.0.8-dev or 1.0.8-dev-20240101)\n" >&2
        printf "  Got: %s\n" "$version" >&2
    fi
else
    # PR/non-main branch: Version must NOT include -dev suffix
    # Pattern: ^[0-9][0-9\.]*(-[0-9]{8}([0-9]{2})?)?$
    printf "%sValidating PR/non-main branch rules:%s\n" "$CYAN" "$NC"
    printf "  - Version must NOT include '-dev' suffix\n"
    printf "  - Pattern: ^[0-9][0-9\\.]*(-[0-9]{8}([0-9]{2})?)?$\n"
    printf "\n"

    # Check if version matches pattern (without -dev)
    if printf '%s\n' "$version" | grep -Eq '^[0-9][0-9.]*(-[0-9]{8}([0-9]{2})?)?$'; then
        # Also verify it does NOT contain -dev
        if printf '%s\n' "$version" | grep -q -- '-dev'; then
            printf "%s✗ Validation FAILED:%s Version incorrectly includes '-dev' suffix for PR/non-main branch\n" "$RED" "$NC" >&2
            printf "  Expected: version without '-dev' suffix (e.g., 1.0.8 or 1.0.8-20240101)\n" >&2
            printf "  Got: %s\n" "$version" >&2
        else
            validation_passed=1
            printf "%s✓ Validation PASSED:%s Version correctly excludes '-dev' suffix\n" "$GREEN" "$NC"
        fi
    else
        printf "%s✗ Validation FAILED:%s Version does not match PR/non-main branch pattern\n" "$RED" "$NC" >&2
        printf "  Expected: version without '-dev' suffix (e.g., 1.0.8 or 1.0.8-20240101)\n" >&2
        printf "  Got: %s\n" "$version" >&2
    fi
fi

printf "\n"

# Validate PKG_RELEASE format by checking the date suffix in Version
# The Version format includes PKG_RELEASE as: VERSION-RELEASE
# For date-based releases, it should be YYYYMMDD or YYYYMMDDHHMM
if printf '%s\n' "$version" | grep -Eq -- '-[0-9]{8}([0-9]{2})?$'; then
    date_suffix=$(printf '%s\n' "$version" | sed -n 's/.*-\([0-9]\{8\}\([0-9]\{2\}\)\?\)$/\1/p')
    printf "%sPKG_RELEASE validation:%s\n" "$CYAN" "$NC"
    printf "  Date suffix found: %s\n" "$date_suffix"

    # Basic validation: check if it's a plausible date
    if [ ${#date_suffix} -eq 8 ] || [ ${#date_suffix} -eq 10 ]; then
        printf "%s  ✓ Date format valid%s (YYYYMMDD or YYYYMMDDHHMM)\n" "$GREEN" "$NC"
    else
        printf "%s  ✗ Date format invalid%s (expected YYYYMMDD or YYYYMMDDHHMM)\n" "$RED" "$NC" >&2
        validation_passed=0
    fi
else
    printf "%sNote:%s No date-based PKG_RELEASE suffix detected (optional)\n" "$YELLOW" "$NC"
fi

printf "\n"

if [ "$validation_passed" -eq 1 ]; then
    printf "%s=== Validation Summary: PASSED ===%s\n" "$GREEN" "$NC"
    exit 0
else
    printf "%s=== Validation Summary: FAILED ===%s\n" "$RED" "$NC" >&2
    exit 1
fi
