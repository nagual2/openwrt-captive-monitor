#!/bin/bash

# Script to identify and delete Windows-incompatible GitHub artifacts
# Windows filename restrictions: : * ? " < > | ; , . ! @ # $ % ^ & + = ~ ` ' \ ( ) [ ] { }

set -euo pipefail

# Check for help flag
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    cat << 'EOF'
Usage: delete-windows-incompatible-artifacts.sh [OPTIONS]

Options:
  --help, -h              Show this help message
  --dry-run, -d           Run in dry-run mode (default)
  --execute, -e           Actually delete artifacts (use with caution)

Environment Variables:
  GITHUB_TOKEN            GitHub token with repo scope (required)
  GITHUB_REPOSITORY       Repository in format owner/repo (optional, auto-detected)
  GITHUB_REPOSITORY_OWNER Repository owner (optional, auto-detected)
  DRY_RUN                 Set to 'false' to actually delete artifacts

Examples:
  # Dry run (safe)
  ./delete-windows-incompatible-artifacts.sh
  ./delete-windows-incompatible-artifacts.sh --dry-run
  
  # Actually delete artifacts
  ./delete-windows-incompatible-artifacts.sh --execute
  DRY_RUN=false ./delete-windows-incompatible-artifacts.sh

Description:
  This script identifies and deletes GitHub artifacts whose names contain
  Windows-incompatible characters. Windows has strict filename restrictions
  and the following characters are not allowed:
  
  : * ? " < > | ; , . ! @ # $ % ^ & + = ~ ` ' \ ( ) [ ] { }
  
  Always run with --dry-run first to see what would be deleted.
EOF
    exit 0
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_OWNER="${GITHUB_REPOSITORY_OWNER:-$(git config --get remote.origin.url | sed -n 's/.*github.com.\([^/]*\)\/.*/\1/p')}"
REPO_NAME="${GITHUB_REPOSITORY:-$(basename -s .git $(git config --get remote.origin.url))}"
DRY_RUN="${DRY_RUN:-true}"  # Default to dry-run for safety

# Function to check if a string contains Windows-incompatible characters
has_windows_incompatible_chars() {
    local name="$1"
    # Check for any Windows-incompatible characters using a simple loop
    local incompatible=':"*?<>|;,.!@#$%^&+=~`'"'"'\()[]{}'
    
    for (( i=0; i<${#name}; i++ )); do
        local char="${name:$i:1}"
        if [[ "$incompatible" == *"$char"* ]]; then
            return 0
        fi
    done
    
    return 1
}

echo -e "${BLUE}=== Windows-Incompatible Artifact Cleanup ===${NC}"
echo -e "${BLUE}Repository: ${REPO_OWNER}/${REPO_NAME}${NC}"
echo -e "${BLUE}Mode: ${DRY_RUN}${NC}"
echo ""

# Check if GitHub token is available
if [ -z "${GITHUB_TOKEN:-}" ]; then
    echo -e "${RED}Error: GITHUB_TOKEN environment variable is not set${NC}"
    echo "Please set GITHUB_TOKEN with appropriate permissions (repo scope)"
    exit 1
fi

# Export token for gh CLI
export GITHUB_TOKEN

# Function to list all artifacts
list_artifacts() {
    echo -e "${BLUE}Fetching all artifacts...${NC}"
    gh api --paginate \
        -H "Accept: application/vnd.github+json" \
        "/repos/${REPO_OWNER}/${REPO_NAME}/actions/artifacts" \
        --jq '.artifacts[] | {id: .id, name: .name, created_at: .created_at, size_in_bytes: .size_in_bytes}'
}

# Function to delete an artifact
delete_artifact() {
    local artifact_id="$1"
    local artifact_name="$2"
    
    if [ "$DRY_RUN" = "true" ]; then
        echo -e "${YELLOW}[DRY RUN] Would delete artifact: ${artifact_name} (ID: ${artifact_id})${NC}"
        return 0
    else
        echo -e "${RED}Deleting artifact: ${artifact_name} (ID: ${artifact_id})${NC}"
        if gh api --silent -X DELETE "/repos/${REPO_OWNER}/${REPO_NAME}/actions/artifacts/${artifact_id}" -f confirm=true; then
            echo -e "${GREEN}✓ Successfully deleted artifact: ${artifact_name}${NC}"
            return 0
        else
            echo -e "${RED}✗ Failed to delete artifact: ${artifact_name}${NC}"
            return 1
        fi
    fi
}

# Main execution
main() {
    local total_artifacts=0
    local incompatible_artifacts=0
    local deleted_count=0
    local failed_count=0
    
    echo -e "${BLUE}Scanning artifacts for Windows-incompatible characters...${NC}"
    echo ""
    
    # Get artifacts and process them
    while IFS= read -r artifact; do
        if [ -z "$artifact" ]; then
            continue
        fi
        
        total_artifacts=$((total_artifacts + 1))
        
        # Parse artifact info using jq
        local artifact_id=$(echo "$artifact" | jq -r '.id')
        local artifact_name=$(echo "$artifact" | jq -r '.name')
        local created_at=$(echo "$artifact" | jq -r '.created_at')
        local size_bytes=$(echo "$artifact" | jq -r '.size_in_bytes')
        
        # Check for Windows-incompatible characters
        if has_windows_incompatible_chars "$artifact_name"; then
            incompatible_artifacts=$((incompatible_artifacts + 1))
            
            echo -e "${YELLOW}🚫 Found Windows-incompatible artifact:${NC}"
            echo -e "   Name: ${RED}${artifact_name}${NC}"
            echo -e "   ID: ${artifact_id}"
            echo -e "   Created: ${created_at}"
            echo -e "   Size: ${size_bytes} bytes"
            
            # Show which characters are problematic
            local problematic_chars=""
            for (( i=0; i<${#artifact_name}; i++ )); do
                local char="${artifact_name:$i:1}"
                if [[ "$char" =~ $WINDOWS_INCOMPATIBLE_PATTERN ]]; then
                    problematic_chars+="$char "
                fi
            done
            
            if [ -n "$problematic_chars" ]; then
                echo -e "   Problematic characters: ${RED}${problematic_chars}${NC}"
            fi
            echo ""
            
            # Delete the artifact
            if delete_artifact "$artifact_id" "$artifact_name"; then
                deleted_count=$((deleted_count + 1))
            else
                failed_count=$((failed_count + 1))
            fi
            echo ""
        else
            echo -e "${GREEN}✓ Compatible artifact: ${artifact_name}${NC}"
        fi
        
    done <<< "$(list_artifacts)"
    
    # Summary
    echo -e "${BLUE}=== Cleanup Summary ===${NC}"
    echo -e "Total artifacts scanned: ${total_artifacts}"
    echo -e "Windows-incompatible artifacts found: ${incompatible_artifacts}"
    
    if [ "$DRY_RUN" = "true" ]; then
        echo -e "${YELLOW}Artifacts that would be deleted: ${deleted_count}${NC}"
        echo -e "${YELLOW}Run with DRY_RUN=false to actually delete artifacts${NC}"
    else
        echo -e "${GREEN}Artifacts successfully deleted: ${deleted_count}${NC}"
        echo -e "${RED}Artifacts failed to delete: ${failed_count}${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}=== Safe Artifact Patterns ===${NC}"
    echo "Safe artifact names should only contain:"
    echo "- Letters (a-z, A-Z)"
    echo "- Numbers (0-9)"
    echo "- Hyphens (-)"
    echo "- Underscores (_)"
    echo "- Periods (.) - though included in filter per ticket requirements"
    echo ""
    
    if [ "$DRY_RUN" = "false" ] && [ "$failed_count" -gt 0 ]; then
        exit 1
    fi
}

# Parse command line arguments
if [[ "${1:-}" == "--execute" ]] || [[ "${1:-}" == "-e" ]]; then
    DRY_RUN="false"
    echo -e "${RED}⚠️  EXECUTION MODE: Will actually delete artifacts!${NC}"
    echo ""
elif [[ "${1:-}" == "--dry-run" ]] || [[ "${1:-}" == "-d" ]]; then
    DRY_RUN="true"
fi

# Run main function
main