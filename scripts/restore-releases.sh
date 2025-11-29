#!/bin/bash
# restore-releases.sh - Main script for restoring all missing releases
#
# This script orchestrates the restoration of both semantic and dated releases
# by calling the appropriate restoration scripts in the correct order.
#
# Usage:
#   bash scripts/restore-releases.sh [--dry-run]
#
# Requirements:
#   - gh CLI authenticated with repo and workflow permissions
#   - git repository with full history
#   - CHANGELOG.md with semantic version entries
#   - Dated tags already exist in repository

set -euo pipefail

# Отключить пейджер для git команд
export GIT_PAGER=cat
export PAGER=cat

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Configuration
DRY_RUN=false
LOG_FILE="${PROJECT_ROOT}/restore-releases.log"

# Counters for overall reporting
TOTAL_SEMANTIC_RESTORED=0
TOTAL_SEMANTIC_SKIPPED=0
TOTAL_SEMANTIC_ERRORS=0
TOTAL_DATED_RESTORED=0
TOTAL_DATED_SKIPPED=0
TOTAL_DATED_ERRORS=0

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

  # Check restoration scripts exist
  if [ ! -f "${SCRIPT_DIR}/restore-semantic-releases.sh" ]; then
    log_error "restore-semantic-releases.sh not found"
    exit 1
  fi

  if [ ! -f "${SCRIPT_DIR}/restore-dated-releases.sh" ]; then
    log_error "restore-dated-releases.sh not found"
    exit 1
  fi

  log_success "Prerequisites check passed"
}

# Parse statistics from log file
# Args:
#   $1 - log file path
#   $2 - pattern to search for (e.g., "Successfully restored:")
# Output: Number extracted from the line
parse_stat_from_log() {
  local log_file=$1
  local pattern=$2

  if [ ! -f "$log_file" ]; then
    echo "0"
    return
  fi

  # Extract the line with the pattern and get the number after the colon
  local value
  value=$(grep "$pattern" "$log_file" | tail -1 | sed -E 's/.*: ([0-9]+).*/\1/' || echo "0")

  # Validate it's a number
  if ! [[ "$value" =~ ^[0-9]+$ ]]; then
    value="0"
  fi

  echo "$value"
}

# Restore semantic releases (Priority 1)
restore_semantic_releases() {
  log_info "========================================="
  log_info "Phase 1: Restoring Semantic Releases"
  log_info "========================================="
  log_info "Priority: 1 (Critical - Historical versions)"
  log_info ""

  local semantic_script="${SCRIPT_DIR}/restore-semantic-releases.sh"
  local semantic_log="${PROJECT_ROOT}/restore-semantic-releases.log"

  # Build command with optional dry-run flag
  local cmd="bash ${semantic_script}"
  if [ "$DRY_RUN" = true ]; then
    cmd="${cmd} --dry-run"
  fi

  log_info "Executing: $cmd"

  # Run semantic restoration script
  # Continue even if it fails (error resilience - Requirement 4.5)
  local exit_code=0
  if ! $cmd; then
    exit_code=$?
    log_error "Semantic release restoration failed with exit code: $exit_code"
    log_warn "Continuing with dated releases despite errors..."
  else
    log_success "Semantic release restoration completed"
  fi

  # Parse statistics from semantic log
  if [ -f "$semantic_log" ]; then
    TOTAL_SEMANTIC_RESTORED=$(parse_stat_from_log "$semantic_log" "Successfully restored:")
    TOTAL_SEMANTIC_SKIPPED=$(parse_stat_from_log "$semantic_log" "Skipped (already exist):")
    TOTAL_SEMANTIC_ERRORS=$(parse_stat_from_log "$semantic_log" "Errors:")

    log_info "Semantic releases - Restored: $TOTAL_SEMANTIC_RESTORED, Skipped: $TOTAL_SEMANTIC_SKIPPED, Errors: $TOTAL_SEMANTIC_ERRORS"
  fi

  echo ""
  return $exit_code
}

# Restore dated releases (Priority 2)
restore_dated_releases() {
  log_info "========================================="
  log_info "Phase 2: Restoring Dated Releases"
  log_info "========================================="
  log_info "Priority: 2 (Important - Post-migration versions)"
  log_info ""

  local dated_script="${SCRIPT_DIR}/restore-dated-releases.sh"
  local dated_log="${PROJECT_ROOT}/restore-dated-releases.log"

  # Build command with optional dry-run flag
  local cmd="bash ${dated_script}"
  if [ "$DRY_RUN" = true ]; then
    cmd="${cmd} --dry-run"
  fi

  log_info "Executing: $cmd"

  # Run dated restoration script
  # Continue even if it fails (error resilience - Requirement 4.5)
  local exit_code=0
  if ! $cmd; then
    exit_code=$?
    log_error "Dated release restoration failed with exit code: $exit_code"
  else
    log_success "Dated release restoration completed"
  fi

  # Parse statistics from dated log
  if [ -f "$dated_log" ]; then
    TOTAL_DATED_RESTORED=$(parse_stat_from_log "$dated_log" "Successfully restored:")
    TOTAL_DATED_SKIPPED=$(parse_stat_from_log "$dated_log" "Skipped (already exist):")
    TOTAL_DATED_ERRORS=$(parse_stat_from_log "$dated_log" "Errors:")

    log_info "Dated releases - Restored: $TOTAL_DATED_RESTORED, Skipped: $TOTAL_DATED_SKIPPED, Errors: $TOTAL_DATED_ERRORS"
  fi

  echo ""
  return $exit_code
}

# Generate final report
generate_report() {
  log_info "========================================="
  log_info "Final Restoration Report"
  log_info "========================================="
  log_info ""

  # Semantic releases summary
  log_info "Semantic Releases (Priority 1):"
  log_info "  Successfully restored: $TOTAL_SEMANTIC_RESTORED"
  log_info "  Skipped (already exist): $TOTAL_SEMANTIC_SKIPPED"
  log_info "  Errors: $TOTAL_SEMANTIC_ERRORS"
  log_info ""

  # Dated releases summary
  log_info "Dated Releases (Priority 2):"
  log_info "  Successfully restored: $TOTAL_DATED_RESTORED"
  log_info "  Skipped (already exist): $TOTAL_DATED_SKIPPED"
  log_info "  Errors: $TOTAL_DATED_ERRORS"
  log_info ""

  # Overall summary
  local total_restored=$((TOTAL_SEMANTIC_RESTORED + TOTAL_DATED_RESTORED))
  local total_skipped=$((TOTAL_SEMANTIC_SKIPPED + TOTAL_DATED_SKIPPED))
  local total_errors=$((TOTAL_SEMANTIC_ERRORS + TOTAL_DATED_ERRORS))

  log_info "Overall Summary:"
  log_info "  Total restored: $total_restored"
  log_info "  Total skipped: $total_skipped"
  log_info "  Total errors: $total_errors"
  log_info ""

  # Log file locations
  log_info "Detailed logs:"
  log_info "  Main log: $LOG_FILE"
  log_info "  Semantic log: ${PROJECT_ROOT}/restore-semantic-releases.log"
  log_info "  Dated log: ${PROJECT_ROOT}/restore-dated-releases.log"
  log_info ""

  # Success/failure determination
  if [ $total_errors -eq 0 ]; then
    if [ $total_restored -eq 0 ] && [ $total_skipped -gt 0 ]; then
      log_success "All releases already exist - nothing to restore"
      return 0
    elif [ $total_restored -gt 0 ]; then
      log_success "Release restoration completed successfully"
      log_success "Restored $total_restored releases"
      return 0
    else
      log_warn "No releases were restored (nothing to do)"
      return 0
    fi
  else
    log_error "Release restoration completed with $total_errors errors"
    log_error "Please review the logs for details"
    return 1
  fi
}

# Print usage information
print_usage() {
  cat << EOF
Usage: $0 [OPTIONS]

Restore all missing releases (semantic and dated) for the project.

This script orchestrates the restoration process by:
  1. Restoring semantic releases (v0.1.x, v1.0.x) from CHANGELOG.md
  2. Restoring dated releases (vYYYY.M.D.N) from existing tags

Options:
  --dry-run    Show what would be done without making changes
  -h, --help   Show this help message

Examples:
  # Restore all missing releases
  $0

  # Preview what would be restored
  $0 --dry-run

Requirements:
  - gh CLI authenticated with repo and workflow permissions
  - git repository with full history
  - CHANGELOG.md with semantic version entries
  - Dated tags already exist in repository

For more information, see:
  - .kiro/specs/restore-missing-releases/requirements.md
  - .kiro/specs/restore-missing-releases/design.md

EOF
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
        print_usage
        exit 0
        ;;
      *)
        echo "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
    esac
  done

  # Initialize main log file
  echo "=== Release Restoration Log ===" > "$LOG_FILE"
  echo "Started at: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
  echo "" >> "$LOG_FILE"

  if [ "$DRY_RUN" = true ]; then
    log_info "========================================="
    log_info "DRY-RUN MODE"
    log_info "========================================="
    log_info "No changes will be made to the repository"
    log_info ""
  fi

  log_info "Starting release restoration process"
  log_info "Project: $(basename "$PROJECT_ROOT")"
  log_info ""

  # Check prerequisites
  check_prerequisites
  echo ""

  # Track overall success
  local semantic_exit=0
  local dated_exit=0

  # Phase 1: Restore semantic releases (Priority 1 - Critical)
  # Requirement 4.1: Semantic releases first
  restore_semantic_releases || semantic_exit=$?

  # Phase 2: Restore dated releases (Priority 2)
  # Requirement 4.1: Dated releases second
  restore_dated_releases || dated_exit=$?

  # Generate final report
  # Requirement 4.4: Report with breakdown by type
  generate_report
  local report_exit=$?

  # Determine final exit code
  # Exit with error if either phase had errors
  if [ $semantic_exit -ne 0 ] || [ $dated_exit -ne 0 ] || [ $report_exit -ne 0 ]; then
    log_error "Restoration process completed with errors"
    exit 1
  fi

  log_success "Restoration process completed successfully"
  exit 0
}

# Run main function
main "$@"
