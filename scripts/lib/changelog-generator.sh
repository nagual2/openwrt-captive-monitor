#!/bin/bash
# changelog-generator.sh - Generate changelog from git log
#
# This script generates changelog content from git commit history,
# useful for creating release notes for dated releases.
#
# Usage:
#   source scripts/lib/changelog-generator.sh
#   generate_changelog_for_tag "v2025.11.27.10"

set -euo pipefail

# Отключить пейджер для git команд
export GIT_PAGER=cat

# Generate changelog for a specific tag
# Args:
#   $1 - tag name (e.g., "v2025.11.27.10")
#   $2 - optional format (default: "markdown")
# Output: Changelog text
generate_changelog_for_tag() {
    local tag=$1
    local format="${2:-markdown}"

    if ! git rev-parse --verify "${tag}" > /dev/null 2>&1; then
        echo "ERROR: Tag ${tag} does not exist" >&2
        return 1
    fi

    # Find previous tag
    local prev_tag
    prev_tag=$(find_previous_tag "$tag")

    if [ -z "$prev_tag" ]; then
        # No previous tag, get all commits up to this tag
        generate_changelog_from_start "$tag" "$format"
    else
        # Generate changelog between two tags
        generate_changelog_between_tags "$prev_tag" "$tag" "$format"
    fi
}

# Find the previous tag before the given tag
# Args:
#   $1 - current tag
# Output: Previous tag name or empty if none
find_previous_tag() {
    local current_tag=$1

    # Get commit SHA for current tag
    local current_commit
    current_commit=$(git rev-list -n 1 "$current_tag" 2> /dev/null)

    if [ -z "$current_commit" ]; then
        return 1
    fi

    # Find previous tag (chronologically)
    git --no-pager describe --tags --abbrev=0 "${current_commit}^" 2> /dev/null || true
}

# Generate changelog from repository start to tag
# Args:
#   $1 - tag name
#   $2 - format (markdown, plain)
generate_changelog_from_start() {
    local tag=$1
    local format=$2

    local commits
    commits=$(git --no-pager log "$tag" --format="%H|%s|%an|%ai" --no-merges)

    format_changelog "$commits" "$format"
}

# Generate changelog between two tags
# Args:
#   $1 - previous tag
#   $2 - current tag
#   $3 - format (markdown, plain)
generate_changelog_between_tags() {
    local prev_tag=$1
    local current_tag=$2
    local format=$3

    local commits
    commits=$(git --no-pager log "${prev_tag}..${current_tag}" --format="%H|%s|%an|%ai" --no-merges)

    if [ -z "$commits" ]; then
        echo "No commits between ${prev_tag} and ${current_tag}"
        return 0
    fi

    format_changelog "$commits" "$format"
}

# Format changelog from commit data
# Args:
#   $1 - commit data (pipe-delimited: SHA|subject|author|date)
#   $2 - format (markdown, plain)
format_changelog() {
    local commits=$1
    local format=$2

    if [ "$format" = "markdown" ]; then
        format_changelog_markdown "$commits"
    else
        format_changelog_plain "$commits"
    fi
}

# Format changelog as markdown
format_changelog_markdown() {
    local commits=$1

    echo "### Changes"
    echo ""

    # Group commits by type (conventional commits)
    local feat_commits=""
    local fix_commits=""
    local docs_commits=""
    local ci_commits=""
    local other_commits=""

    while IFS='|' read -r sha subject _author _date; do
        local short_sha="${sha:0:7}"

        # Categorize by conventional commit type
        if [[ $subject =~ ^feat:.*$ ]] || [[ $subject =~ ^feat\(.*\):.*$ ]]; then
            feat_commits="${feat_commits}- ${subject#feat:} (${short_sha})"$'\n'
        elif [[ $subject =~ ^fix:.*$ ]] || [[ $subject =~ ^fix\(.*\):.*$ ]]; then
            fix_commits="${fix_commits}- ${subject#fix:} (${short_sha})"$'\n'
        elif [[ $subject =~ ^docs:.*$ ]] || [[ $subject =~ ^docs\(.*\):.*$ ]]; then
            docs_commits="${docs_commits}- ${subject#docs:} (${short_sha})"$'\n'
        elif [[ $subject =~ ^ci:.*$ ]] || [[ $subject =~ ^ci\(.*\):.*$ ]]; then
            ci_commits="${ci_commits}- ${subject#ci:} (${short_sha})"$'\n'
        else
            other_commits="${other_commits}- ${subject} (${short_sha})"$'\n'
        fi
    done <<< "$commits"

    # Output grouped commits
    if [ -n "$feat_commits" ]; then
        echo "#### Features"
        echo ""
        echo -n "$feat_commits"
        echo ""
    fi

    if [ -n "$fix_commits" ]; then
        echo "#### Bug Fixes"
        echo ""
        echo -n "$fix_commits"
        echo ""
    fi

    if [ -n "$docs_commits" ]; then
        echo "#### Documentation"
        echo ""
        echo -n "$docs_commits"
        echo ""
    fi

    if [ -n "$ci_commits" ]; then
        echo "#### CI/CD"
        echo ""
        echo -n "$ci_commits"
        echo ""
    fi

    if [ -n "$other_commits" ]; then
        echo "#### Other Changes"
        echo ""
        echo -n "$other_commits"
        echo ""
    fi
}

# Format changelog as plain text
format_changelog_plain() {
    local commits=$1

    echo "Changes:"
    echo ""

    while IFS='|' read -r sha subject _author _date; do
        local short_sha="${sha:0:7}"
        echo "- ${subject} (${short_sha})"
    done <<< "$commits"
}

# Generate changelog for date-based release
# This creates a standardized changelog for dated releases
# Args:
#   $1 - tag name (e.g., "v2025.11.27.10")
generate_dated_release_changelog() {
    local tag=$1

    # Extract date from tag (vYYYY.M.D.N -> YYYY-MM-DD)
    local date
    date=$(extract_date_from_tag "$tag")

    echo "## ${tag} - ${date}"
    echo ""

    generate_changelog_for_tag "$tag" "markdown"
}

# Extract date from dated tag
# Args:
#   $1 - tag (e.g., "v2025.11.27.10")
# Output: Date in YYYY-MM-DD format
extract_date_from_tag() {
    local tag=$1

    # Remove v prefix
    tag="${tag#v}"

    # Extract YYYY.M.D.N
    if [[ $tag =~ ^([0-9]{4})\.([0-9]{1,2})\.([0-9]{1,2})\.[0-9]+$ ]]; then
        local year="${BASH_REMATCH[1]}"
        local month="${BASH_REMATCH[2]}"
        local day="${BASH_REMATCH[3]}"

        # Format with leading zeros
        printf "%s-%02d-%02d" "$year" "$month" "$day"
    else
        echo "ERROR: Invalid dated tag format: $tag" >&2
        return 1
    fi
}

# Count commits between tags
# Args:
#   $1 - previous tag (or empty for start)
#   $2 - current tag
# Output: Number of commits
count_commits_between() {
    local prev_tag=$1
    local current_tag=$2

    if [ -z "$prev_tag" ]; then
        git --no-pager rev-list --count "$current_tag"
    else
        git --no-pager rev-list --count "${prev_tag}..${current_tag}"
    fi
}

# Get list of all tags (sorted by date)
# Output: One tag per line, newest first
list_all_tags() {
    git --no-pager tag -l --sort=-creatordate
}

# Get list of dated tags only (vYYYY.M.D.N format)
# Output: One tag per line, newest first
list_dated_tags() {
    git --no-pager tag -l --sort=-creatordate | grep -E '^v[0-9]{4}\.[0-9]{1,2}\.[0-9]{1,2}\.[0-9]+$'
}

# Get list of semantic version tags only (vX.Y.Z format)
# Output: One tag per line, newest first
list_semantic_tags() {
    git --no-pager tag -l --sort=-creatordate | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$'
}
