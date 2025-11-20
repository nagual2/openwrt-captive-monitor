#!/bin/sh
# shellcheck shell=ash
# Helper to bump date-based version metadata before creating a tag.
#
# This script is intended for maintainers who need to cut a manual
# date-based release (vYYYY.M.D.N) without relying on the auto-version
# workflow.
#
# Behavior:
#   - With an explicit argument, it treats the value as a clean
#     date-based version (YYYY.M.D.N, without leading "v").
#   - With no arguments, it computes the next version for *today*
#     by scanning existing tags (vYYYY.M.D.N) and incrementing N.
#   - It then delegates to scripts/update-version-metadata.sh to
#     update the root VERSION file and PKG_VERSION in the package
#     Makefile.
#   - PKG_RELEASE is left as a small integer (e.g. 1, 2, 3) and is
#     not modified by this helper.
#
# After running this script, you should:
#   1. Commit the version metadata change
#   2. Create a matching tag: v<version>
#   3. Push the tag to trigger the release workflow
#
# Example (manual release flow):
#   ./scripts/bump-date-version.sh 2025.11.20.11
#   git commit -am "chore: bump version to 2025.11.20.11"
#   git tag -a v2025.11.20.11 -m "Release v2025.11.20.11"
#   git push origin v2025.11.20.11

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

# shellcheck source=scripts/lib/colors.sh
. "$script_dir/lib/colors.sh"

print_usage() {
    cat << 'EOF'
Usage: scripts/bump-date-version.sh [YYYY.M.D.N]

Bump date-based version metadata before creating a release tag.

Behavior:
  - If an explicit version is provided (YYYY.M.D.N), that value is used.
  - If no argument is provided, the script computes the next version
    for today based on existing vYYYY.M.D.N tags.

The helper updates:
  - VERSION (root file) → YYYY.M.D.N
  - PKG_VERSION in package/openwrt-captive-monitor/Makefile → YYYY.M.D.N

PKG_RELEASE is intentionally left unchanged but must remain a small
integer (e.g. 1, 2, 3). The tag-build-release workflow enforces this.

After running this script:
  1. Review and commit the changes to VERSION and the Makefile.
  2. Create a matching tag: v<YYYY.M.D.N>.
  3. Push the tag to trigger the release build.

Examples:
  # Use an explicit date-based version
  scripts/bump-date-version.sh 2025.11.20.11

  # Let the script compute today's next version and print it
  scripts/bump-date-version.sh
EOF
}

if [ "$#" -gt 1 ]; then
    printf '%serror:%s expected at most one argument (YYYY.M.D.N)\n' "$RED" "$NC" >&2
    print_usage >&2
    exit 1
fi

new_version=""

if [ "$#" -eq 1 ]; then
    # Allow either clean version (YYYY.M.D.N) or v-prefixed tag
    raw_version=$1
    # Strip a single leading 'v' for convenience
    case "$raw_version" in
        v*) new_version=${raw_version#v} ;;
        *)  new_version=$raw_version ;;
    esac
else
    # No explicit version provided: compute the next version for today
    if ! command -v git > /dev/null 2>&1; then
        printf '%serror:%s git is required to compute the next version automatically\n' "$RED" "$NC" >&2
        printf 'Hint: either install git or provide an explicit version: YYYY.M.D.N\n' >&2
        exit 1
    fi

    {
        cd "$repo_root"

        YEAR=$(date -u +%Y)
        MONTH=$(date -u +%-m)
        DAY=$(date -u +%-d)
        DATE_PREFIX="v${YEAR}.${MONTH}.${DAY}"

        # Fetch tags if possible, but don't fail hard if network is unavailable
        if git rev-parse --git-dir > /dev/null 2>&1; then
            git fetch --tags --force > /dev/null 2>&1 || true
        fi

        LAST_SEQUENCE=$(git tag --list "${DATE_PREFIX}.*" \
            | sed -nE "s/^${DATE_PREFIX}\.([0-9]+)$/\\1/p" \
            | sort -n \
            | tail -n1)

        if [ -z "$LAST_SEQUENCE" ]; then
            NEXT_SEQUENCE=1
        else
            NEXT_SEQUENCE=$((LAST_SEQUENCE + 1))
        fi

        new_version="${YEAR}.${MONTH}.${DAY}.${NEXT_SEQUENCE}"
    }
fi

# Delegate validation and metadata updates to the canonical helper.
# This ensures VERSION and PKG_VERSION are updated in a consistent way.
printf '%sinfo:%s updating version metadata to %s\n' "$BLUE" "$NC" "$new_version"
"$script_dir/update-version-metadata.sh" "$new_version"

printf '%sNew date-based version:%s %s\n' "$GREEN" "$NC" "$new_version"
printf 'Create a matching tag (example): git tag -a "v%s" -m "Release v%s" && git push origin "v%s"\n' \
    "$new_version" "$new_version" "$new_version"
