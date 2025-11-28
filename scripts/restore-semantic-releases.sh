#!/bin/bash
# restore-semantic-releases.sh - Restore historical semantic version releases
#
# This script restores missing semantic version releases (v0.1.x, v1.0.x)
# by recreating tags and GitHub releases based on CHANGELOG.md content.
#
# Usage:
#   bash scripts/restore-semantic-releases.sh [--dry-run]
#
# Requirements:
#   - gh CLI authenticated with repo and workflow permissions
#   - git repository with full history
#   - CHANGELOG.md with semantic version entries

set -euo pipefail

# Отключить пейджер для git команд
export GIT_PAGER=cat
export PAGER=cat

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Source utility libraries
source "${SCRIPT_DIR}/lib/changelog-parser.sh"
source "${SCRIPT_DIR}/lib/commit-finder.sh"

# Configuration
CHANGELOG_FILE="${PROJECT_ROOT}/docs/release/CHANGELOG.md"
DRY_RUN=false
LOG_FILE="${PROJECT_ROOT}/restore-semantic-releases.log"

# Semantic versions to restore (from requirements)
SEMANTIC_VERSIONS=(
  "v0.1.0"
  "v0.1.1"
  "v0.1.2"
  "v1.0.1"
  "v1.0.3"
)

# Counters for reporting
RESTORED_COUNT=0
SKIPPED_COUNT=0
ERROR_COUNT=0
declare -a ERRORS=()

# Logging functions
log_info() {
  local msg="[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $*"
  echo "$msg"
  echo "$msg" >> "$LOG_FILE"
}

log_success() {
  local msg="[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $*"
  echo "$msg"
  echo "$msg" >> "$LOG_FILE"
}

log_warn() {
  local msg="[WARNING] $(date '+%Y-%m-%d %H:%M:%S') - $*"
  echo "$msg" >&2
  echo "$msg" >> "$LOG_FILE"
}

log_error() {
  local msg="[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $*"
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
  
  # Check CHANGELOG.md
  if [ ! -f "$CHANGELOG_FILE" ]; then
    log_error "CHANGELOG.md not found at: $CHANGELOG_FILE"
    exit 1
  fi
  
  log_success "Prerequisites check passed"
}

# Check if release already exists
release_exists() {
  local version=$1
  
  if gh release view "$version" &> /dev/null; then
    return 0
  else
    return 1
  fi
}

# Check if tag already exists
tag_exists() {
  local version=$1
  
  if git rev-parse --verify "${version}" &> /dev/null 2>&1; then
    return 0
  else
    return 1
  fi
}

# Create git tag for version
create_tag() {
  local version=$1
  local commit_sha=$2
  
  log_info "Creating tag $version at commit $commit_sha"
  
  if [ "$DRY_RUN" = true ]; then
    log_info "[DRY-RUN] Would create tag: git tag -a $version $commit_sha -m 'Release $version'"
    return 0
  fi
  
  # Create annotated tag
  if git tag -a "$version" "$commit_sha" -m "Release $version"; then
    log_success "Created tag $version"
    
    # Push tag to remote
    if git push origin "$version"; then
      log_success "Pushed tag $version to origin"
      return 0
    else
      log_error "Failed to push tag $version"
      return 1
    fi
  else
    log_error "Failed to create tag $version"
    return 1
  fi
}

# Create GitHub release
create_release() {
  local version=$1
  local changelog=$2
  
  log_info "Creating GitHub release for $version"
  
  # Prepare release notes with historical marker
  local release_notes="**Historical Release - Restored from CHANGELOG**

$changelog"
  
  local title="$version - Historical Release"
  
  if [ "$DRY_RUN" = true ]; then
    log_info "[DRY-RUN] Would create release:"
    log_info "  Title: $title"
    log_info "  Tag: $version"
    log_info "  Notes: (${#release_notes} characters)"
    return 0
  fi
  
  # Create release with retry logic
  local max_retries=3
  local retry_count=0
  
  while [ $retry_count -lt $max_retries ]; do
    if gh release create "$version" \
        --title "$title" \
        --notes "$release_notes"; then
      log_success "Created release $version"
      return 0
    fi
    
    retry_count=$((retry_count + 1))
    if [ $retry_count -lt $max_retries ]; then
      local wait_time=$((2 ** retry_count))
      log_warn "Release creation failed, retrying in ${wait_time}s... (attempt $retry_count/$max_retries)"
      sleep $wait_time
    fi
  done
  
  log_error "Failed to create release $version after $max_retries attempts"
  return 1
}

# Restore a single semantic release
restore_semantic_release() {
  local version=$1
  
  log_info "========================================="
  log_info "Processing version: $version"
  log_info "========================================="
  
  # Check if release already exists
  if release_exists "$version"; then
    log_info "Release $version already exists, skipping"
    SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
    return 0
  fi
  
  # Get changelog for this version
  log_info "Extracting changelog for $version from CHANGELOG.md"
  local changelog
  if ! changelog=$(get_changelog_for_version "$version" "$CHANGELOG_FILE"); then
    log_error "Failed to extract changelog for $version"
    ERROR_COUNT=$((ERROR_COUNT + 1))
    return 1
  fi
  
  if [ -z "$changelog" ]; then
    log_error "Empty changelog for $version"
    ERROR_COUNT=$((ERROR_COUNT + 1))
    return 1
  fi
  
  log_info "Changelog extracted (${#changelog} characters)"
  
  # Get date hint from CHANGELOG
  local date_hint
  date_hint=$(get_version_date "$version" "$CHANGELOG_FILE" || echo "")
  
  if [ -n "$date_hint" ]; then
    log_info "Date hint from CHANGELOG: $date_hint"
  fi
  
  # Find commit for this version
  log_info "Finding commit for $version"
  local commit_sha
  
  # Use timeout to prevent hanging (15 seconds max)
  if ! commit_sha=$(timeout 15s bash -c "source ${SCRIPT_DIR}/lib/commit-finder.sh; find_commit_for_version '$version' '$date_hint'" 2>/dev/null || echo ""); then
    commit_sha=""
  fi
  
  if [ -z "$commit_sha" ]; then
    log_warn "Could not automatically find commit for $version (timed out or not found)"
    
    # Fallback strategy: Use commit that added/moved CHANGELOG with these versions
    log_info "Using fallback strategy: finding commit that contains CHANGELOG with $version"
    
    # Find commit where CHANGELOG.md (in any location) contains this version
    local changelog_commit
    changelog_commit=$(timeout 10s git --no-pager log --all --format="%H" -S"$version" -- "*CHANGELOG.md" --max-count=1 2>/dev/null || echo "")
    
    if [ -n "$changelog_commit" ]; then
      commit_sha="$changelog_commit"
      log_warn "Using CHANGELOG commit as fallback: $commit_sha"
    else
      # Last resort: use earliest commit
      log_info "Attempting to use earliest commit as final fallback"
      commit_sha=$(git --no-pager log --all --reverse --format="%H" --max-count=1 2>/dev/null || echo "")
      
      if [ -n "$commit_sha" ]; then
        log_warn "Using earliest commit as fallback: $commit_sha"
      else
        log_error "Could not find any suitable commit for $version"
        ERROR_COUNT=$((ERROR_COUNT + 1))
        return 1
      fi
    fi
  fi
  
  log_success "Found commit: $commit_sha"
  
  # Get commit details for logging
  local commit_date
  commit_date=$(get_commit_date "$commit_sha")
  local commit_msg
  commit_msg=$(get_commit_message "$commit_sha")
  log_info "Commit date: $commit_date"
  log_info "Commit message: $commit_msg"
  
  # Create tag if it doesn't exist
  if ! tag_exists "$version"; then
    if ! create_tag "$version" "$commit_sha"; then
      log_error "Failed to create tag for $version"
      ERROR_COUNT=$((ERROR_COUNT + 1))
      return 1
    fi
  else
    log_info "Tag $version already exists"
  fi
  
  # Create GitHub release
  if ! create_release "$version" "$changelog"; then
    log_error "Failed to create release for $version"
    ERROR_COUNT=$((ERROR_COUNT + 1))
    return 1
  fi
  
  RESTORED_COUNT=$((RESTORED_COUNT + 1))
  log_success "Successfully restored $version"
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
      -h|--help)
        echo "Usage: $0 [--dry-run]"
        echo ""
        echo "Restore historical semantic version releases from CHANGELOG.md"
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
  echo "=== Semantic Release Restoration Log ===" > "$LOG_FILE"
  echo "Started at: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
  echo "" >> "$LOG_FILE"
  
  if [ "$DRY_RUN" = true ]; then
    log_info "DRY-RUN MODE: No changes will be made"
  fi
  
  log_info "Starting semantic release restoration"
  log_info "Versions to restore: ${SEMANTIC_VERSIONS[*]}"
  
  # Check prerequisites
  check_prerequisites
  
  # Process each semantic version
  for version in "${SEMANTIC_VERSIONS[@]}"; do
    # Continue processing even if one fails (error resilience)
    restore_semantic_release "$version" || true
  done
  
  # Print summary
  echo ""
  log_info "========================================="
  log_info "Restoration Summary"
  log_info "========================================="
  log_info "Total versions processed: ${#SEMANTIC_VERSIONS[@]}"
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
  
  log_success "Semantic release restoration completed successfully"
}

# Run main function
main "$@"
