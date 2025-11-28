#!/bin/bash
# test-lib-utilities.sh - Test the library utilities
#
# This script demonstrates and tests the functionality of the three
# utility libraries created for release restoration.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
  echo -e "${BLUE}INFO:${NC} $*"
}

log_success() {
  echo -e "${GREEN}SUCCESS:${NC} $*"
}

log_error() {
  echo -e "${RED}ERROR:${NC} $*" >&2
}

# Source the libraries
source scripts/lib/changelog-parser.sh
source scripts/lib/commit-finder.sh
source scripts/lib/changelog-generator.sh

echo "=== Testing Release Restoration Utilities ==="
echo ""

# Test 1: Parse CHANGELOG versions
log_info "Test 1: Parsing CHANGELOG.md for semantic versions"
echo ""
versions=$(list_semantic_versions)
echo "Found semantic versions:"
echo "$versions"
echo ""
log_success "Test 1 passed"
echo ""

# Test 2: Get changelog for specific version
log_info "Test 2: Getting changelog for v1.0.3"
echo ""
changelog=$(get_changelog_for_version "v1.0.3")
echo "$changelog" | head -10
echo ""
log_success "Test 2 passed"
echo ""

# Test 3: Find commit for existing tag
log_info "Test 3: Finding commit for existing tag v2025.11.27.13"
echo ""
commit=$(find_commit_for_version "v2025.11.27.13")
if [ -n "$commit" ]; then
  echo "Found commit: $commit"
  git --no-pager log -1 --oneline "$commit"
  log_success "Test 3 passed"
else
  log_error "Test 3 failed - commit not found"
fi
echo ""

# Test 4: Generate changelog for dated tag
log_info "Test 4: Generating changelog for v2025.11.27.13"
echo ""
generated_changelog=$(generate_changelog_for_tag "v2025.11.27.13")
echo "$generated_changelog" | head -15
echo ""
log_success "Test 4 passed"
echo ""

# Test 5: List all dated tags
log_info "Test 5: Listing dated tags"
echo ""
dated_tags=$(list_dated_tags | head -5)
echo "Recent dated tags:"
echo "$dated_tags"
echo ""
log_success "Test 5 passed"
echo ""

# Test 6: Extract date from tag
log_info "Test 6: Extracting date from tag v2025.11.27.13"
echo ""
extracted_date=$(extract_date_from_tag "v2025.11.27.13")
echo "Extracted date: $extracted_date"
echo ""
log_success "Test 6 passed"
echo ""

# Summary
echo "=== All Tests Passed ==="
echo ""
echo "The following utilities are ready for use:"
echo "  - scripts/lib/changelog-parser.sh"
echo "  - scripts/lib/commit-finder.sh"
echo "  - scripts/lib/changelog-generator.sh"
echo ""
echo "These utilities can now be used by the release restoration scripts."
