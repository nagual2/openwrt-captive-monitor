#!/bin/bash
# changelog-parser.sh - Extract version information from CHANGELOG.md
#
# This script parses CHANGELOG.md to extract semantic version information
# including version numbers, dates, and changelog content.
#
# Usage:
#   source scripts/lib/changelog-parser.sh
#   parse_changelog_versions
#   get_changelog_for_version "v1.0.3"

set -euo pipefail

# Parse all semantic versions from CHANGELOG.md
# Output format: VERSION|DATE|FIRST_LINE
# Example: v1.0.3|2025-11-XX|### Changed
parse_changelog_versions() {
    local changelog_file="${1:-docs/release/CHANGELOG.md}"

    if [ ! -f "$changelog_file" ]; then
        echo "ERROR: CHANGELOG file not found: $changelog_file" >&2
        return 1
    fi

    # Extract semantic versions (v0.1.x, v1.0.x format)
    # Match patterns like: ## [1.0.3](...) or ## v0.1.1
    # Exclude dated versions (vYYYY.M.D.N format)
    awk '
    /^## \[?[0-9]+\.[0-9]+\.[0-9]+\]?/ {
      # Skip if this looks like a dated version (year 2000+)
      if (match($0, /\[?20[0-9]{2}\.[0-9]+\.[0-9]+/)) {
        next
      }
      
      # Extract version
      match($0, /[0-9]+\.[0-9]+\.[0-9]+/)
      version = "v" substr($0, RSTART, RLENGTH)
      
      # Try to extract date from the line
      date = ""
      if (match($0, /[0-9]{4}-[0-9]{2}-[0-9]{2}/)) {
        date = substr($0, RSTART, RLENGTH)
      }
      
      # Get next non-empty line as first line of content
      getline
      while (length($0) == 0 && getline > 0) {}
      first_line = $0
      
      # Output in pipe-delimited format
      print version "|" date "|" first_line
    }
    
    /^## v[0-9]+\.[0-9]+\.[0-9]+/ {
      # Extract version (already has v prefix)
      match($0, /v[0-9]+\.[0-9]+\.[0-9]+/)
      version = substr($0, RSTART, RLENGTH)
      
      # No date in this format
      date = ""
      
      # Get next non-empty line
      getline
      while (length($0) == 0 && getline > 0) {}
      first_line = $0
      
      print version "|" date "|" first_line
    }
  ' "$changelog_file"
}

# Get full changelog content for a specific version
# Args:
#   $1 - version (e.g., "v1.0.3" or "1.0.3")
# Output: Full changelog text for that version
get_changelog_for_version() {
    local version=$1
    local changelog_file="${2:-docs/release/CHANGELOG.md}"

    # Normalize version (ensure v prefix)
    if [[ ! "$version" =~ ^v ]]; then
        version="v${version}"
    fi

    # Remove v prefix for matching
    local version_number="${version#v}"

    if [ ! -f "$changelog_file" ]; then
        echo "ERROR: CHANGELOG file not found: $changelog_file" >&2
        return 1
    fi

    # Extract content between version header and next version header
    awk -v ver="$version_number" '
    BEGIN { found = 0; printing = 0 }
    
    # Match version header (with or without v prefix, with or without brackets)
    /^## / {
      if (printing) {
        # Found next version, stop printing
        exit
      }
      
      # Check if this is our version
      if (match($0, /[0-9]+\.[0-9]+\.[0-9]+/)) {
        found_ver = substr($0, RSTART, RLENGTH)
        if (found_ver == ver) {
          found = 1
          printing = 1
          next
        }
      }
    }
    
    # Print lines if we are in the right section
    printing { print }
    
    END {
      if (!found) {
        print "ERROR: Version " ver " not found in CHANGELOG" > "/dev/stderr"
        exit 1
      }
    }
  ' "$changelog_file"
}

# List all semantic versions found in CHANGELOG
# Output: One version per line (e.g., v1.0.3)
list_semantic_versions() {
    local changelog_file="${1:-docs/release/CHANGELOG.md}"

    parse_changelog_versions "$changelog_file" | cut -d'|' -f1
}

# Check if a version exists in CHANGELOG
# Args:
#   $1 - version to check (e.g., "v1.0.3" or "1.0.3")
# Returns: 0 if exists, 1 if not
version_exists_in_changelog() {
    local version=$1
    local changelog_file="${2:-docs/release/CHANGELOG.md}"

    # Normalize version
    if [[ ! "$version" =~ ^v ]]; then
        version="v${version}"
    fi

    list_semantic_versions "$changelog_file" | grep -q "^${version}$"
}

# Get date for a version from CHANGELOG
# Args:
#   $1 - version (e.g., "v1.0.3")
# Output: Date string or empty if not found
get_version_date() {
    local version=$1
    local changelog_file="${2:-docs/release/CHANGELOG.md}"

    # Normalize version
    if [[ ! "$version" =~ ^v ]]; then
        version="v${version}"
    fi

    parse_changelog_versions "$changelog_file" | grep "^${version}|" | cut -d'|' -f2
}
