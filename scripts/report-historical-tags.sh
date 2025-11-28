#!/bin/sh
# shellcheck shell=ash
#
# report-historical-tags.sh - Show presence of historical semantic-version tags
#
# This helper reports whether the known semantic-version tags referenced in the
# documentation (v0.1.x and v1.0.x) exist in the current clone, and if they do,
# which commit they currently point to. It is intended as a read-only aid for
# maintainers restoring tags and GitHub Releases after history cleanup.
#
# Usage:
#   scripts/report-historical-tags.sh
#
# The script is safe to run from any subdirectory inside the repository.

set -eu

# Move to the repository root if possible so git commands behave predictably.
if git_root=$(git rev-parse --show-toplevel 2>/dev/null); then
    cd "$git_root" || exit 1
fi

HISTORICAL_TAGS="v0.1.0 v0.1.1 v0.1.2 v1.0.1 v1.0.3 v1.0.6 v1.0.8"

printf '%s
' "Historical semantic-version tags status:"
printf '  %-8s  %-8s  %s
' "Tag" "Status" "Target commit (if present)"
printf '  %-8s  %-8s  %s
' "--------" "--------" "--------------------------"

for tag in $HISTORICAL_TAGS; do
    if git rev-parse -q --verify "refs/tags/$tag" >/dev/null; then
        # Tag exists locally; show short SHA so maintainers can cross-check it.
        sha=$(git rev-parse --short "refs/tags/$tag" 2>/dev/null || echo "?")
        status="present"
    else
        sha=""
        status="missing"
    fi
    printf '  %-8s  %-8s  %s
' "$tag" "$status" "$sha"
done

printf '\n%s
' "See docs/release/HISTORICAL_TAGS_RESTORATION.md for restoration guidance."
