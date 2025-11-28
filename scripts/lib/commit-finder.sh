#!/bin/bash
# commit-finder.sh - Find git commits for specific versions
#
# This script implements multiple strategies to find the commit SHA
# corresponding to a specific version, useful for recreating tags.
#
# Usage:
#   source scripts/lib/commit-finder.sh
#   find_commit_for_version "v1.0.3" "2025-11-XX"

set -euo pipefail

# Отключить пейджер для git команд
export GIT_PAGER=cat

# Find commit for a version using multiple strategies
# Args:
#   $1 - version (e.g., "v1.0.3")
#   $2 - optional date hint from CHANGELOG (e.g., "2025-11-20")
# Output: commit SHA or empty if not found
find_commit_for_version() {
  local version=$1
  local date_hint="${2:-}"
  
  # Normalize version (ensure v prefix)
  if [[ ! "$version" =~ ^v ]]; then
    version="v${version}"
  fi
  
  local commit_sha=""
  
  # Strategy 1: Check if tag already exists
  commit_sha=$(find_by_existing_tag "$version")
  if [ -n "$commit_sha" ]; then
    echo "$commit_sha"
    return 0
  fi
  
  # Strategy 2: Search commit messages for version
  commit_sha=$(find_by_commit_message "$version")
  if [ -n "$commit_sha" ]; then
    echo "$commit_sha"
    return 0
  fi
  
  # Strategy 3: Search VERSION file changes
  commit_sha=$(find_by_version_file "$version")
  if [ -n "$commit_sha" ]; then
    echo "$commit_sha"
    return 0
  fi
  
  # Strategy 4: Search by date if provided
  if [ -n "$date_hint" ] && [ "$date_hint" != "" ]; then
    commit_sha=$(find_by_date "$version" "$date_hint")
    if [ -n "$commit_sha" ]; then
      echo "$commit_sha"
      return 0
    fi
  fi
  
  # Strategy 5: Search Makefile PKG_VERSION changes
  commit_sha=$(find_by_makefile_version "$version")
  if [ -n "$commit_sha" ]; then
    echo "$commit_sha"
    return 0
  fi
  
  # Not found
  return 1
}

# Strategy 1: Check if tag already exists
find_by_existing_tag() {
  local version=$1
  
  if git rev-parse --verify "${version}" >/dev/null 2>&1; then
    git rev-parse "${version}"
    return 0
  fi
  
  return 1
}

# Strategy 2: Search commit messages
find_by_commit_message() {
  local version=$1
  local version_number="${version#v}"
  
  # Search for version in commit messages
  # Try multiple patterns with max-count to speed up
  local patterns=(
    "^v${version_number}"
    "version ${version_number}"
    "bump.*${version_number}"
    "release.*${version_number}"
    "${version_number}"
  )
  
  for pattern in "${patterns[@]}"; do
    local commit
    commit=$(git --no-pager log --all --oneline --grep="${pattern}" -i --format="%H" --max-count=1 2>/dev/null || echo "")
    if [ -n "$commit" ]; then
      echo "$commit"
      return 0
    fi
  done
  
  return 1
}

# Strategy 3: Search VERSION file changes
find_by_version_file() {
  local version=$1
  local version_number="${version#v}"
  
  if [ ! -f VERSION ]; then
    return 1
  fi
  
  # Search for commits that changed VERSION file to this version
  local commits
  commits=$(git --no-pager log --all -S"${version_number}" --format="%H" -- VERSION)
  
  if [ -n "$commits" ]; then
    # Check each commit to find one that actually contains the version
    while IFS= read -r commit; do
      if [ -n "$commit" ]; then
        # Verify this commit actually contains the version
        local version_content
        version_content=$(git --no-pager show "${commit}:VERSION" 2>/dev/null || echo "")
        if echo "$version_content" | grep -q "^${version_number}$"; then
          echo "$commit"
          return 0
        fi
      fi
    done <<< "$commits"
  fi
  
  return 1
}

# Strategy 4: Search by date
find_by_date() {
  local version=$1
  local date_hint=$2
  
  # Skip if no date hint provided
  if [ -z "$date_hint" ]; then
    return 1
  fi
  
  # If date has XX, try to find commits in that month
  if [[ "$date_hint" =~ ([0-9]{4})-([0-9]{2})-XX ]]; then
    local year="${BASH_REMATCH[1]}"
    local month="${BASH_REMATCH[2]}"
    
    # Get commits from that month
    local since="${year}-${month}-01"
    local until="${year}-${month}-31"
    
    # Find commits in that date range (limit to 1 result)
    local commit
    commit=$(git --no-pager log --all --since="$since" --until="$until" --format="%H" --max-count=1 2>/dev/null || echo "")
    
    if [ -n "$commit" ]; then
      echo "$commit"
      return 0
    fi
  elif [[ "$date_hint" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    # Exact date provided
    # Find commits on or near that date (within 7 days)
    local commit
    commit=$(git --no-pager log --all --since="${date_hint}" --until="${date_hint} +7 days" --format="%H" --max-count=1 2>/dev/null || echo "")
    
    if [ -n "$commit" ]; then
      echo "$commit"
      return 0
    fi
  fi
  
  return 1
}

# Strategy 5: Search Makefile PKG_VERSION changes
find_by_makefile_version() {
  local version=$1
  local version_number="${version#v}"
  
  # Find Makefile in package directory
  local makefile
  makefile=$(find package -name Makefile -type f 2>/dev/null | head -1)
  
  if [ -z "$makefile" ]; then
    return 1
  fi
  
  # Search for commits that changed PKG_VERSION to this version
  local commit
  commit=$(git --no-pager log --all -S"PKG_VERSION:=${version_number}" --format="%H" --max-count=1 -- "$makefile" 2>/dev/null || echo "")
  
  if [ -n "$commit" ]; then
    echo "$commit"
    return 0
  fi
  
  return 1
}

# Get commit date in ISO format
# Args:
#   $1 - commit SHA
# Output: Date in YYYY-MM-DD format
get_commit_date() {
  local commit=$1
  
  git --no-pager show -s --format=%ci "$commit" | cut -d' ' -f1
}

# Get commit message (first line)
# Args:
#   $1 - commit SHA
# Output: First line of commit message
get_commit_message() {
  local commit=$1
  
  git --no-pager log -1 --format=%s "$commit"
}

# Verify commit exists
# Args:
#   $1 - commit SHA
# Returns: 0 if exists, 1 if not
verify_commit_exists() {
  local commit=$1
  
  git rev-parse --verify "${commit}^{commit}" >/dev/null 2>&1
}

# Interactive: Ask user for commit SHA
# Args:
#   $1 - version
# Output: User-provided commit SHA
ask_user_for_commit() {
  local version=$1
  
  echo "Could not automatically find commit for ${version}" >&2
  echo "Please provide commit SHA manually:" >&2
  echo "(You can find it with: git log --all --oneline | grep -i ${version})" >&2
  
  read -r commit_sha
  
  if verify_commit_exists "$commit_sha"; then
    echo "$commit_sha"
    return 0
  else
    echo "ERROR: Invalid commit SHA: $commit_sha" >&2
    return 1
  fi
}
