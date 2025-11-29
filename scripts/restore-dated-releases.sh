#!/bin/bash
# restore-dated-releases.sh - Restore missing dated version releases
#
# This script restores missing dated version releases (vYYYY.M.D.N)
# by creating GitHub releases for existing tags that don't have releases.
#
# Usage:
#   bash scripts/restore-dated-releases.sh [--dry-run]
#
# Requirements:
#   - gh CLI authenticated with repo and workflow permissions
#   - git repository with full history
#   - Dated tags already exist in repository

set -euo pipefail

# Отключить пейджер для git команд
export GIT_PAGER=cat
export PAGER=cat

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Source utility libraries
# shellcheck source=lib/changelog-generator.sh
source "${SCRIPT_DIR}/lib/changelog-generator.sh"

# Configuration
DRY_RUN=false
LOG_FILE="${PROJECT_ROOT}/restore-dated-releases.log"

# Counters for reporting
RESTORED_COUNT=0
SKIPPED_COUNT=0
ERROR_COUNT=0
declare -a ERRORS=()
declare -a MISSING_TAGS=()

# Logging functions
log_info() {
    local msg
    msg="[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $*"
    echo "$msg"
    echo "$msg" >> "$LOG_FILE"
}

log_success() {
    local msg
    msg="[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $*"
    echo "$msg"
    echo "$msg" >> "$LOG_FILE"
}

log_warn() {
    local msg
    msg="[WARNING] $(date '+%Y-%m-%d %H:%M:%S') - $*"
    echo "$msg" >&2
    echo "$msg" >> "$LOG_FILE"
}

log_error() {
    local msg
    msg="[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $*"
    echo "$msg" >&2
    echo "$msg" >> "$LOG_FILE"
    ERRORS+=("$msg")
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check gh CLI
    if ! command -v gh &> /dev/null; then
        log_error "gh CLI not found. Please install GitHub CLI."
        exit 1
    fi

    # Check gh authentication
    if ! gh auth status &> /dev/null; then
        log_error "gh CLI not authenticated. Run: gh auth login"
        exit 1
    fi

    # Check git repository
    if ! git rev-parse --git-dir &> /dev/null; then
        log_error "Not in a git repository"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Get all dated tags from remote repository
# Output: One tag per line (vYYYY.M.D.N format)
get_all_dated_tags() {
    # Fetch all tags from remote (log to stderr to not pollute output)
    git fetch --tags --quiet 2> /dev/null || true

    # List all dated tags (vYYYY.M.D.N format)
    # Match pattern: v followed by 4-digit year, 1-2 digit month, 1-2 digit day, and sequence number
    git --no-pager tag -l | grep -E '^v[0-9]{4}\.[0-9]{1,2}\.[0-9]{1,2}\.[0-9]+$' | sort -V
}

# Get all existing releases
# Output: One tag per line
get_existing_releases() {
    # Get all releases (limit to 1000 to handle large repos)
    gh release list --limit 1000 --json tagName --jq '.[].tagName' 2> /dev/null || true
}

# Check if release exists for tag
# Args:
#   $1 - tag name
# Returns: 0 if exists, 1 if not
release_exists() {
    local tag=$1

    if gh release view "$tag" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Extract date from dated tag
# Args:
#   $1 - tag (e.g., "v2025.11.27.10")
# Output: Date in YYYY-MM-DD format
format_date_from_tag() {
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

# Generate changelog for a dated tag
# Args:
#   $1 - tag name
# Output: Changelog text
generate_changelog() {
    local tag=$1

    log_info "Generating changelog for $tag"

    # Use changelog-generator.sh to create changelog
    if ! generate_changelog_for_tag "$tag" "markdown" 2> /dev/null; then
        # Fallback: simple commit list
        log_warn "Failed to generate structured changelog, using simple format"

        local prev_tag
        prev_tag=$(find_previous_tag "$tag" 2> /dev/null || echo "")

        if [ -z "$prev_tag" ]; then
            # No previous tag, list all commits
            git --no-pager log "$tag" --format="- %s (%h)" --no-merges 2> /dev/null || echo "Initial release"
        else
            # List commits between tags
            local commits
            commits=$(git --no-pager log "${prev_tag}..${tag}" --format="- %s (%h)" --no-merges 2> /dev/null || echo "")

            if [ -z "$commits" ]; then
                echo "No changes"
            else
                echo "$commits"
            fi
        fi
    fi
}

# Create GitHub release for dated tag
# Args:
#   $1 - tag name
create_dated_release() {
    local tag=$1

    log_info "Creating GitHub release for $tag"

    # Extract date from tag
    local date
    if ! date=$(format_date_from_tag "$tag"); then
        log_error "Failed to extract date from tag: $tag"
        return 1
    fi

    # Generate changelog
    local changelog
    if ! changelog=$(generate_changelog "$tag"); then
        log_error "Failed to generate changelog for $tag"
        return 1
    fi

    # Prepare release notes with restored marker
    local release_notes="**Restored Release**

$changelog"

    # Format title: vYYYY.M.D.N - YYYY-MM-DD
    local title="${tag} - ${date}"

    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would create release:"
        log_info "  Title: $title"
        log_info "  Tag: $tag"
        log_info "  Date: $date"
        log_info "  Notes: (${#release_notes} characters)"
        return 0
    fi

    # Create release with retry logic
    local max_retries=3
    local retry_count=0

    while [ $retry_count -lt $max_retries ]; do
        if gh release create "$tag" \
            --title "$title" \
            --notes "$release_notes" 2> /dev/null; then
            log_success "Created release $tag"
            return 0
        fi

        retry_count=$((retry_count + 1))
        if [ $retry_count -lt $max_retries ]; then
            local wait_time=$((2 ** retry_count))
            log_warn "Release creation failed, retrying in ${wait_time}s... (attempt $retry_count/$max_retries)"
            sleep $wait_time
        fi
    done

    log_error "Failed to create release $tag after $max_retries attempts"
    return 1
}

# Restore a single dated release
# Args:
#   $1 - tag name
restore_dated_release() {
    local tag=$1

    log_info "Processing tag: $tag"

    # Check if release already exists
    if release_exists "$tag"; then
        log_info "Release $tag already exists, skipping"
        SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
        return 0
    fi

    # Create GitHub release
    if ! create_dated_release "$tag"; then
        log_error "Failed to create release for $tag"
        ERROR_COUNT=$((ERROR_COUNT + 1))
        return 1
    fi

    RESTORED_COUNT=$((RESTORED_COUNT + 1))
    log_success "Successfully restored $tag"
    return 0
}

# Main function
main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            -h | --help)
                echo "Usage: $0 [--dry-run]"
                echo ""
                echo "Restore missing dated version releases (vYYYY.M.D.N)"
                echo ""
                echo "Options:"
                echo "  --dry-run    Show what would be done without making changes"
                echo "  -h, --help   Show this help message"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done

    # Initialize log file
    echo "=== Dated Release Restoration Log ===" > "$LOG_FILE"
    echo "Started at: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"

    if [ "$DRY_RUN" = true ]; then
        log_info "DRY-RUN MODE: No changes will be made"
    fi

    log_info "Starting dated release restoration"

    # Check prerequisites
    check_prerequisites

    # Get all dated tags
    log_info "Collecting dated tags..."
    local all_tags
    all_tags=$(get_all_dated_tags)

    if [ -z "$all_tags" ]; then
        log_warn "No dated tags found in repository"
        log_info "Restoration complete (nothing to do)"
        exit 0
    fi

    local tag_count
    tag_count=$(echo "$all_tags" | wc -l)
    log_info "Found $tag_count dated tags"

    # Get existing releases
    log_info "Collecting existing releases..."
    local existing_releases
    existing_releases=$(get_existing_releases)

    local release_count
    if [ -n "$existing_releases" ]; then
        release_count=$(echo "$existing_releases" | wc -l)
    else
        release_count=0
    fi
    log_info "Found $release_count existing releases"

    # Determine tags without releases
    log_info "Determining tags without releases..."
    local tags_without_releases=""

    while IFS= read -r tag; do
        if [ -z "$tag" ]; then
            continue
        fi

        # Check if release exists for this tag
        if echo "$existing_releases" | grep -q "^${tag}$"; then
            log_info "  $tag - release exists"
        else
            log_info "  $tag - missing release"
            MISSING_TAGS+=("$tag")
            if [ -z "$tags_without_releases" ]; then
                tags_without_releases="$tag"
            else
                tags_without_releases="${tags_without_releases}"$'\n'"${tag}"
            fi
        fi
    done <<< "$all_tags"

    local missing_count=${#MISSING_TAGS[@]}
    log_info "Found $missing_count tags without releases"

    if [ $missing_count -eq 0 ]; then
        log_success "All dated tags have releases, nothing to restore"
        exit 0
    fi

    # Process each tag without release
    log_info "========================================="
    log_info "Restoring releases for $missing_count tags"
    log_info "========================================="

    for tag in "${MISSING_TAGS[@]}"; do
        # Continue processing even if one fails (error resilience)
        restore_dated_release "$tag" || true
        echo ""
    done

    # Print summary
    echo ""
    log_info "========================================="
    log_info "Restoration Summary"
    log_info "========================================="
    log_info "Total dated tags: $tag_count"
    log_info "Tags without releases: $missing_count"
    log_info "Successfully restored: $RESTORED_COUNT"
    log_info "Skipped (already exist): $SKIPPED_COUNT"
    log_info "Errors: $ERROR_COUNT"

    if [ ${#ERRORS[@]} -gt 0 ]; then
        log_info ""
        log_info "Errors encountered:"
        for error in "${ERRORS[@]}"; do
            echo "  - $error"
        done
    fi

    log_info ""
    log_info "Log file: $LOG_FILE"

    # Exit with error if any failures occurred
    if [ $ERROR_COUNT -gt 0 ]; then
        exit 1
    fi

    log_success "Dated release restoration completed successfully"
}

# Run main function
main "$@"
