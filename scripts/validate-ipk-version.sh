#!/bin/sh
# shellcheck shell=ash
# Validate .ipk control metadata Version field against branch-specific rules
#
# Usage: validate-ipk-version.sh <ipk_file> <branch_type>
#   ipk_file: Path to .ipk package file
#   branch_type: One of "main", "pr", or "release"
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

Version format (shared base):
  <date-version>: YYYY.M.D.N where:
    - YYYY is a 4-digit year (e.g., 2025)
    - M is month 1-12 (no leading zero required)
    - D is day 1-31 (no leading zero required)
    - N is a numeric build counter for that date
  Regex for <date-version>:
    ^[0-9]{4}\.(1[0-2]|[1-9])\.(3[01]|[12][0-9]|[1-9])\.[0-9]+$

Branch-specific rules:
  main:    Version must be <date-version>-dev-<PKG_RELEASE>
           Regex: ^[0-9]{4}\.(1[0-2]|[1-9])\.(3[01]|[12][0-9]|[1-9])\.[0-9]+-dev-[0-9]+$
           Example: 2025.11.20.2-dev-1
  pr:      Version must be <date-version>-<PKG_RELEASE> (no -dev)
           Regex: ^[0-9]{4}\.(1[0-2]|[1-9])\.(3[01]|[12][0-9]|[1-9])\.[0-9]+-[0-9]+$
           Example: 2025.11.20.2-1
  release: Same as "pr" (tagged release builds use clean versions without -dev)

PKG_RELEASE must be a purely numeric, non-negative integer (^[0-9]+$).

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

# Shared base regex for the date-based version component (YYYY.M.D.N)
base_regex='^[0-9]{4}\.(1[0-2]|[1-9])\.(3[01]|[12][0-9]|[1-9])\.[0-9]+'

if [ "$branch_type" = "main" ]; then
    # Main branch: <date-version>-dev-<PKG_RELEASE>
    printf "%sValidating main branch rules:%s\n" "$CYAN" "$NC"
    printf "  - Base version must be date-based: YYYY.M.D.N\n"
    printf "  - PKG_RELEASE must be numeric (^[0-9]+$)\n"
    printf "  - Expected Version format: <YYYY.M.D.N>-dev-<PKG_RELEASE>\n"
    printf "    Example: 2025.11.20.2-dev-1\n"
    printf "\n"

    main_pattern='^[0-9]{4}\.(1[0-2]|[1-9])\.(3[01]|[12][0-9]|[1-9])\.[0-9]+-dev-[0-9]+$'

    if printf '%s\n' "$version" | grep -Eq "$main_pattern"; then
        validation_passed=1
        printf "%s✓ Validation PASSED:%s Version matches main branch pattern\n" "$GREEN" "$NC"
    else
        printf "%s✗ Validation FAILED:%s Version does not match main branch pattern\n" "$RED" "$NC" >&2
        # Provide more detailed diagnostics
        if ! printf '%s\n' "$version" | grep -q -- '-dev-'; then
            printf "  Expected: version with '-dev-' and numeric PKG_RELEASE (e.g., 2025.11.20.2-dev-1)\n" >&2
            printf "  Got: %s\n" "$version" >&2
        else
            base_part=$(printf '%s\n' "$version" | sed 's/-dev-[^-]*$//')
            release_part=$(printf '%s\n' "$version" | sed 's/.*-dev-//')
            if ! printf '%s\n' "$base_part" | grep -Eq "${base_regex}$"; then
                printf "  Base component '%s' is not a valid date-based version (expected YYYY.M.D.N)\n" "$base_part" >&2
            elif ! printf '%s\n' "$release_part" | grep -Eq '^[0-9]+$'; then
                printf "  PKG_RELEASE component '%s' must be numeric (e.g., 1, 2, 3)\n" "$release_part" >&2
            else
                printf "  Got: %s\n" "$version" >&2
            fi
        fi
    fi
else
    # PR and tagged release builds: <date-version>-<PKG_RELEASE> (no -dev)
    printf "%sValidating PR/release rules:%s\n" "$CYAN" "$NC"
    printf "  - Base version must be date-based: YYYY.M.D.N\n"
    printf "  - PKG_RELEASE must be numeric (^[0-9]+$)\n"
    printf "  - Expected Version format: <YYYY.M.D.N>-<PKG_RELEASE>\n"
    printf "    Example: 2025.11.20.2-1\n"
    printf "  - '-dev' suffix is not allowed\n"
    printf "\n"

    pr_pattern='^[0-9]{4}\.(1[0-2]|[1-9])\.(3[01]|[12][0-9]|[1-9])\.[0-9]+-[0-9]+$'

    if printf '%s\n' "$version" | grep -Eq "$pr_pattern"; then
        if printf '%s\n' "$version" | grep -q -- '-dev'; then
            printf "%s✗ Validation FAILED:%s Version incorrectly includes '-dev' suffix for non-main build\n" "$RED" "$NC" >&2
            printf "  Expected: version without '-dev' (e.g., 2025.11.20.2-1)\n" >&2
            printf "  Got: %s\n" "$version" >&2
        else
            validation_passed=1
            printf "%s✓ Validation PASSED:%s Version matches PR/release pattern\n" "$GREEN" "$NC"
        fi
    else
        printf "%s✗ Validation FAILED:%s Version does not match PR/release pattern\n" "$RED" "$NC" >&2
        base_part=$(printf '%s\n' "$version" | sed 's/-[^-]*$//')
        release_part=$(printf '%s\n' "$version" | sed 's/.*-//')
        if printf '%s\n' "$version" | grep -q -- '-dev'; then
            printf "  '-dev' suffix is not allowed for PR/release builds\n" >&2
        fi
        if ! printf '%s\n' "$base_part" | grep -Eq "${base_regex}$"; then
            printf "  Base component '%s' is not a valid date-based version (expected YYYY.M.D.N)\n" "$base_part" >&2
        elif ! printf '%s\n' "$release_part" | grep -Eq '^[0-9]+$'; then
            printf "  PKG_RELEASE component '%s' must be numeric (e.g., 1, 2, 3)\n" "$release_part" >&2
        else
            printf "  Got: %s\n" "$version" >&2
        fi
    fi
fi

printf "\n"

if [ "$validation_passed" -eq 1 ]; then
    printf "%s=== Validation Summary: PASSED ===%s\n" "$GREEN" "$NC"
    exit 0
else
    printf "%s=== Validation Summary: FAILED ===%s\n" "$RED" "$NC" >&2
    exit 1
fi
