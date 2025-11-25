#!/usr/bin/env bash
# Git operations wrapper for WSL1 (Windows Subsystem for Linux)
# This script provides functions to work with Git through WSL1 from Windows

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

log_debug() {
    if [[ "${DEBUG:-0}" == "1" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $*"
    fi
}

# Check if WSL1 is available
check_wsl() {
    if ! command -v wsl.exe &> /dev/null; then
        log_error "WSL (wsl.exe) not found. Please install WSL1."
        log_error "Visit: https://docs.microsoft.com/en-us/windows/wsl/install"
        return 1
    fi
    
    log_debug "WSL found: $(command -v wsl.exe)"
    return 0
}

# Convert Windows path to WSL/Linux path
# Example: C:\Users\Admin\project -> /mnt/c/Users/Admin/project
convert_path() {
    local win_path="$1"
    
    # Check if path is already in Linux format
    if [[ "$win_path" =~ ^/mnt/ ]] || [[ "$win_path" =~ ^/ ]]; then
        echo "$win_path"
        return 0
    fi
    
    # Convert Windows path to WSL path
    # C:\Users\... -> /mnt/c/Users/...
    local linux_path
    linux_path=$(echo "$win_path" | sed -e 's|\\|/|g' -e 's|^\([A-Za-z]\):|/mnt/\L\1|')
    
    log_debug "Converted path: $win_path -> $linux_path"
    echo "$linux_path"
}

# Execute command in WSL1
wsl_exec() {
    local cmd="$*"
    
    log_debug "Executing in WSL: $cmd"
    
    if ! wsl.exe bash -c "$cmd"; then
        log_error "WSL command failed: $cmd"
        return 1
    fi
    
    return 0
}

# Execute git command in WSL1
wsl_git() {
    local git_cmd="$*"
    
    log_debug "Executing git command: $git_cmd"
    
    if ! wsl_exec "git $git_cmd"; then
        log_error "Git command failed: $git_cmd"
        return 1
    fi
    
    return 0
}

# Create a new branch
create_branch() {
    local branch_name="$1"
    local base_branch="${2:-main}"
    
    if [[ -z "$branch_name" ]]; then
        log_error "Branch name is required"
        return 1
    fi
    
    log_info "Creating branch: $branch_name (base: $base_branch)"
    
    # Ensure we're on the base branch and it's up to date
    wsl_git "checkout $base_branch" || return 1
    wsl_git "pull origin $base_branch" || return 1
    
    # Create and checkout new branch
    wsl_git "checkout -b $branch_name" || return 1
    
    log_info "Branch $branch_name created successfully"
    return 0
}

# Create a commit with English message
commit() {
    local message="$1"
    local files="${2:-.}"
    
    if [[ -z "$message" ]]; then
        log_error "Commit message is required"
        return 1
    fi
    
    # Validate that message is in English (basic check)
    # Check for common non-ASCII characters
    if echo "$message" | grep -qP '[^\x00-\x7F]'; then
        log_warn "Commit message contains non-ASCII characters"
        log_warn "Please use English for commit messages"
        return 1
    fi
    
    log_info "Creating commit: $message"
    
    # Add files
    wsl_git "add $files" || return 1
    
    # Create commit
    wsl_git "commit -m \"$message\"" || return 1
    
    log_info "Commit created successfully"
    return 0
}

# Format issue reference in commit message
# Converts: "Fix bug #123" or "Fix bug 123" to "Fix bug (#123)"
format_issue_ref() {
    local message="$1"
    
    # Replace standalone numbers after keywords with (#number)
    # Matches: fix #123, fixes #123, close #123, closes #123, resolve #123, resolves #123
    local formatted
    formatted=$(echo "$message" | sed -E 's/(fix|fixes|close|closes|resolve|resolves|ref|refs|see) #?([0-9]+)/\1 (#\2)/gi')
    
    echo "$formatted"
}

# Create a pull request using GitHub CLI
create_pr() {
    local title="$1"
    local body="${2:-}"
    local base_branch="${3:-main}"
    
    if [[ -z "$title" ]]; then
        log_error "PR title is required"
        return 1
    fi
    
    # Format issue references in title and body
    title=$(format_issue_ref "$title")
    if [[ -n "$body" ]]; then
        body=$(format_issue_ref "$body")
    fi
    
    log_info "Creating pull request: $title"
    
    # Check if gh CLI is available in WSL
    if ! wsl_exec "command -v gh &> /dev/null"; then
        log_error "GitHub CLI (gh) not found in WSL"
        log_error "Install: https://cli.github.com/"
        return 1
    fi
    
    # Get current branch
    local current_branch
    current_branch=$(wsl_exec "git branch --show-current")
    
    log_info "Current branch: $current_branch"
    log_info "Base branch: $base_branch"
    
    # Push current branch
    wsl_git "push -u origin $current_branch" || return 1
    
    # Create PR
    local pr_cmd="gh pr create --title \"$title\" --base \"$base_branch\""
    
    if [[ -n "$body" ]]; then
        pr_cmd="$pr_cmd --body \"$body\""
    fi
    
    if ! wsl_exec "$pr_cmd"; then
        log_error "Failed to create pull request"
        return 1
    fi
    
    log_info "Pull request created successfully"
    return 0
}

# Merge a pull request
merge_pr() {
    local pr_number="$1"
    local merge_method="${2:-squash}"
    
    if [[ -z "$pr_number" ]]; then
        log_error "PR number is required"
        return 1
    fi
    
    # Validate merge method
    if [[ ! "$merge_method" =~ ^(merge|squash|rebase)$ ]]; then
        log_error "Invalid merge method: $merge_method"
        log_error "Valid methods: merge, squash, rebase"
        return 1
    fi
    
    log_info "Merging PR #$pr_number using $merge_method method"
    
    # Check if gh CLI is available
    if ! wsl_exec "command -v gh &> /dev/null"; then
        log_error "GitHub CLI (gh) not found in WSL"
        return 1
    fi
    
    # Merge PR
    if ! wsl_exec "gh pr merge $pr_number --$merge_method --delete-branch"; then
        log_error "Failed to merge PR #$pr_number"
        return 1
    fi
    
    log_info "PR #$pr_number merged successfully"
    return 0
}

# Push changes to remote
push() {
    local branch="${1:-}"
    local force="${2:-false}"
    
    if [[ -z "$branch" ]]; then
        # Get current branch
        branch=$(wsl_exec "git branch --show-current")
    fi
    
    log_info "Pushing to branch: $branch"
    
    local push_cmd="push origin $branch"
    
    if [[ "$force" == "true" ]]; then
        log_warn "Force pushing to $branch"
        push_cmd="push --force-with-lease origin $branch"
    fi
    
    if ! wsl_git "$push_cmd"; then
        log_error "Failed to push to $branch"
        return 1
    fi
    
    log_info "Pushed successfully to $branch"
    return 0
}

# Get current repository status
status() {
    log_info "Repository status:"
    wsl_git "status"
}

# Show usage information
usage() {
    cat << EOF
Usage: $0 <command> [arguments]

Git operations wrapper for WSL1

COMMANDS:
    create-branch <name> [base]     Create a new branch
    commit <message> [files]        Create a commit with English message
    create-pr <title> [body] [base] Create a pull request
    merge-pr <number> [method]      Merge a pull request
    push [branch] [force]           Push changes to remote
    status                          Show repository status

EXAMPLES:
    # Create a feature branch
    $0 create-branch feature/optimize-build

    # Create a commit
    $0 commit "Add Docker SDK optimization"

    # Create a pull request
    $0 create-pr "Optimize build with Docker SDK" "This PR adds Docker SDK images"

    # Merge a pull request
    $0 merge-pr 123 squash

    # Push changes
    $0 push feature/optimize-build

ENVIRONMENT VARIABLES:
    DEBUG=1                         Enable debug output

NOTES:
    - All commit messages must be in English
    - Issue references are automatically formatted: #123 -> (#123)
    - WSL1 must be installed and configured
    - GitHub CLI (gh) required for PR operations

EOF
    exit 0
}

# Main function
main() {
    # Check WSL availability
    if ! check_wsl; then
        exit 1
    fi
    
    # Parse command
    local command="${1:-}"
    
    if [[ -z "$command" ]]; then
        usage
    fi
    
    case "$command" in
        create-branch)
            shift
            create_branch "$@"
            ;;
        commit)
            shift
            commit "$@"
            ;;
        create-pr)
            shift
            create_pr "$@"
            ;;
        merge-pr)
            shift
            merge_pr "$@"
            ;;
        push)
            shift
            push "$@"
            ;;
        status)
            status
            ;;
        -h|--help|help)
            usage
            ;;
        *)
            log_error "Unknown command: $command"
            usage
            ;;
    esac
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
