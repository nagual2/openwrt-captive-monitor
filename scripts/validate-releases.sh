#!/bin/bash
# validate-releases.sh - Validate release integrity
#
# This script checks that all expected releases exist on GitHub:
# - Semantic versions from CHANGELOG.md (v0.1.0, v0.1.1, v0.1.2, v1.0.1, v1.0.3)
# - Date-based versions from git tags (vYYYY.M.D.N)
#
# Requirements: 5.1, 5.2, 5.3, 5.4
#
# Usage:
#   bash scripts/validate-releases.sh

set -euo pipefail

# Отключить интерактивные элементы
export GIT_PAGER=cat
export PAGER=cat

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source library functions
# shellcheck source=scripts/lib/colors.sh
. "$SCRIPT_DIR/lib/colors.sh"
# shellcheck source=scripts/lib/changelog-parser.sh
. "$SCRIPT_DIR/lib/changelog-parser.sh"

# Logging functions
log_info() {
  printf "%s[INFO]%s %s\n" "$BLUE" "$NC" "$*"
}

log_success() {
  printf "%s[SUCCESS]%s %s\n" "$GREEN" "$NC" "$*"
}

log_error() {
  printf "%s[ERROR]%s %s\n" "$RED" "$NC" "$*" >&2
}

log_warn() {
  printf "%s[WARNING]%s %s\n" "$YELLOW" "$NC" "$*"
}

# Check if gh CLI is available and authenticated
check_gh_auth() {
  if ! command -v gh &> /dev/null; then
    log_error "GitHub CLI (gh) is not installed"
    log_error "Install from: https://cli.github.com/"
    return 1
  fi
  
  if ! gh auth status &> /dev/null; then
    log_error "GitHub CLI is not authenticated"
    log_error "Run: gh auth login"
    return 1
  fi
  
  return 0
}

# Get all releases from GitHub
# Output: List of tag names, one per line
get_all_releases() {
  log_info "Fetching releases from GitHub..."
  
  # Get all releases (up to 1000, should be enough)
  # Parse the text output to extract tag names
  gh release list --limit 1000 2>/dev/null | awk '{print $1}' || {
    log_error "Failed to fetch releases from GitHub"
    return 1
  }
}

# Check if a release exists
# Args:
#   $1 - tag name
#   $2 - list of release tags (one per line)
# Returns: 0 if exists, 1 if not
release_exists() {
  local tag=$1
  local releases_list=$2
  
  echo "$releases_list" | grep -q "^${tag}$"
}

# Validate semantic releases
# Args:
#   $1 - list of release tags (one per line)
# Returns: 0 if all present, 1 if any missing
validate_semantic_releases() {
  local releases_list=$1
  local changelog_file="$PROJECT_ROOT/docs/release/CHANGELOG.md"
  
  log_info "Validating semantic releases..."
  
  # Expected semantic versions
  local expected_versions=("v0.1.0" "v0.1.1" "v0.1.2" "v1.0.1" "v1.0.3")
  local missing_versions=()
  local found_count=0
  
  for version in "${expected_versions[@]}"; do
    if release_exists "$version" "$releases_list"; then
      log_success "  ✅ $version - present"
      ((found_count++))
    else
      log_warn "  ❌ $version - MISSING"
      missing_versions+=("$version")
    fi
  done
  
  echo ""
  log_info "Semantic releases: $found_count/${#expected_versions[@]}"
  
  if [ ${#missing_versions[@]} -gt 0 ]; then
    log_warn "Missing semantic releases:"
    for version in "${missing_versions[@]}"; do
      log_warn "  - $version"
    done
    return 1
  fi
  
  return 0
}

# Get all dated tags from repository
# Output: List of tags matching vYYYY.M.D.N format
get_dated_tags() {
  log_info "Fetching dated tags from repository..."
  
  # Get all tags matching dated format (vYYYY.M.D.N)
  git --no-pager tag -l "v20[0-9][0-9].*" | sort -V
}

# Validate dated releases
# Args:
#   $1 - list of release tags (one per line)
# Returns: 0 if all present, 1 if any missing
validate_dated_releases() {
  local releases_list=$1
  local missing_tags=()
  local found_count=0
  local total_count=0
  
  # Get all dated tags (suppress log message)
  local dated_tags
  dated_tags=$(git --no-pager tag -l "v20[0-9][0-9].*" 2>/dev/null | sort -V)
  
  log_info "Validating dated releases..."
  
  if [ -z "$dated_tags" ]; then
    log_info "No dated tags found in repository"
    return 0
  fi
  
  # Check each dated tag
  while IFS= read -r tag; do
    ((total_count++))
    
    if release_exists "$tag" "$releases_list"; then
      found_count=$((found_count + 1))
    else
      missing_tags+=("$tag")
    fi
  done <<< "$dated_tags"
  
  log_info "Dated releases: $found_count/$total_count"
  
  if [ ${#missing_tags[@]} -gt 0 ]; then
    log_warn "Missing dated releases (showing first 10):"
    local count=0
    for tag in "${missing_tags[@]}"; do
      if [ $count -ge 10 ]; then
        log_warn "  ... and $((${#missing_tags[@]} - 10)) more"
        break
      fi
      log_warn "  - $tag"
      ((count++))
    done
    return 1
  fi
  
  return 0
}

# Generate summary report
# Args:
#   $1 - semantic validation result (0=pass, 1=fail)
#   $2 - dated validation result (0=pass, 1=fail)
#   $3 - list of release tags (one per line)
generate_report() {
  local semantic_result=$1
  local dated_result=$2
  local releases_list=$3
  
  echo ""
  echo "═══════════════════════════════════════════════════════════"
  echo "              Release Integrity Report"
  echo "═══════════════════════════════════════════════════════════"
  echo ""
  
  # Count releases by type
  local semantic_count
  semantic_count=$(echo "$releases_list" | grep -cE "^v[0-9]+\.[0-9]+\.[0-9]+$" || true)
  
  local dated_count
  dated_count=$(echo "$releases_list" | grep -cE "^v20[0-9]{2}\." || true)
  
  local total_count
  total_count=$(echo "$releases_list" | wc -l)
  
  echo "Release Statistics:"
  echo "  Semantic releases: $semantic_count"
  echo "  Dated releases: $dated_count"
  echo "  Total releases: $total_count"
  echo ""
  
  # Validation results
  echo "Validation Results:"
  
  if [ "$semantic_result" -eq 0 ]; then
    printf "  Semantic releases: %s✅ PASS%s\n" "$GREEN" "$NC"
  else
    printf "  Semantic releases: %s❌ FAIL%s\n" "$RED" "$NC"
  fi
  
  if [ "$dated_result" -eq 0 ]; then
    printf "  Dated releases: %s✅ PASS%s\n" "$GREEN" "$NC"
  else
    printf "  Dated releases: %s❌ FAIL%s\n" "$RED" "$NC"
  fi
  
  echo ""
  
  # Overall status
  if [ "$semantic_result" -eq 0 ] && [ "$dated_result" -eq 0 ]; then
    printf "%s✅ All releases present - Integrity check PASSED%s\n" "$GREEN" "$NC"
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    return 0
  else
    printf "%s❌ Missing releases detected - Integrity check FAILED%s\n" "$RED" "$NC"
    echo ""
    echo "To restore missing releases, run:"
    echo "  bash scripts/restore-releases.sh"
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    return 1
  fi
}

# Main function
main() {
  log_info "Starting release integrity validation..."
  echo ""
  
  # Check prerequisites
  if ! check_gh_auth; then
    exit 1
  fi
  
  # Get all releases
  local releases_list
  releases_list=$(get_all_releases)
  
  if [ -z "$releases_list" ]; then
    log_warn "No releases found on GitHub"
    releases_list=""
  fi
  
  echo ""
  
  # Validate semantic releases
  local semantic_result=0
  validate_semantic_releases "$releases_list" || semantic_result=$?
  
  echo ""
  
  # Validate dated releases
  local dated_result=0
  validate_dated_releases "$releases_list" || dated_result=$?
  
  # Generate report
  generate_report "$semantic_result" "$dated_result" "$releases_list" || exit 1
}

# Run main function
main "$@"
