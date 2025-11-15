#!/bin/sh
# shellcheck shell=ash
set -eu

###############################################################################
# Pipe Guards Check Script
#
# Analyzes shell scripts for proper pipe handling and error checking.
# Identifies potential issues with pipes that might cause failures in CI.
#
# Usage: ./scripts/check-pipe-guards.sh [DIRECTORY]
###############################################################################

DIRECTORY="${1:-.}"

# Source shared color definitions
# shellcheck source=lib/colors.sh
. "$(dirname "$0")/lib/colors.sh"

printf "%s=== 🔍 PIPE GUARDS ANALYSIS ===%s\n" "$BLUE" "$NC"
printf "Directory: %s\n" "$DIRECTORY"
printf "\n"

###############################################################################
# Section 1: Check for pipefail usage
###############################################################################

printf "%s--- Checking pipefail usage ---%s\n" "$CYAN" "$NC"

# Find shell scripts
find "$DIRECTORY" -type f -name "*.sh" | while read -r script; do
    # Skip if it's a binary or in certain directories
    case "$script" in
        *.git/*|*/node_modules/*|*/.git/*) continue ;;
    esac
    
    # Check for pipefail usage
    if grep -q "pipefail" "$script" 2>/dev/null; then
        printf "%s✓%s %s uses pipefail\n" "$GREEN" "$NC" "$script"
        
        # Check if it's the conditional pattern
        if grep -q "set -o pipefail" "$script" && grep -q "set -eu" "$script"; then
            if grep -q "if (set -o pipefail)" "$script"; then
                printf "  %s✓ Uses conditional pipefail pattern%s\n" "$GREEN" "$NC"
            else
                printf "  %s⚠️  Uses direct pipefail (may not be POSIX compatible)%s\n" "$YELLOW" "$NC"
            fi
        fi
    else
        # Check if script uses pipes but no pipefail
        if grep -q "|" "$script" 2>/dev/null; then
            printf "%s⚠️  %s uses pipes but no pipefail%s\n" "$YELLOW" "$NC" "$script"
            
            # Show some pipe examples
            grep -n "|" "$script" 2>/dev/null | head -3 | while read -r line; do
                printf "    %s%s%s\n" "$YELLOW" "$line" "$NC"
            done
        fi
    fi
done

printf "\n"

###############################################################################
# Section 2: Check for potential pipe issues
###############################################################################

printf "%s--- Checking for potential pipe issues ---%s\n" "$CYAN" "$NC"

# Find scripts with pipes that might fail
find "$DIRECTORY" -type f -name "*.sh" | while read -r script; do
    case "$script" in
        *.git/*|*/node_modules/*|*/.git/*) continue ;;
    esac
    
    # Check for common pipe patterns that might fail
    issues_found=0
    
    # Check for grep without proper error handling
    if grep -q "grep.*|" "$script" 2>/dev/null; then
        # Look for grep in pipes
        grep -n "grep.*|" "$script" 2>/dev/null | head -2 | while read -r line; do
            if ! echo "$line" | grep -q "|| true\||| exit 0\|2>/dev/null"; then
                printf "%s⚠️  %s:%s - grep in pipe may fail silently%s\n" "$YELLOW" "$NC" "$script" "$line" "$NC"
                issues_found=1
            fi
        done
    fi
    
    # Check for find pipes without proper error handling
    if grep -q "find.*|" "$script" 2>/dev/null; then
        grep -n "find.*|" "$script" 2>/dev/null | head -2 | while read -r line; do
            if ! echo "$line" | grep -q "|| true\||| exit 0\|2>/dev/null"; then
                printf "%s⚠️  %s:%s - find in pipe may fail silently%s\n" "$YELLOW" "$NC" "$script" "$line" "$NC"
                issues_found=1
            fi
        done
    fi
    
    # Check for curl pipes without proper error handling
    if grep -q "curl.*|" "$script" 2>/dev/null; then
        grep -n "curl.*|" "$script" 2>/dev/null | head -2 | while read -r line; do
            if ! echo "$line" | grep -q "|| true\||| exit 0\|2>/dev/null\|-f\|-s"; then
                printf "%s⚠️  %s:%s - curl in pipe may fail silently%s\n" "$YELLOW" "$NC" "$script" "$line" "$NC"
                issues_found=1
            fi
        done
    fi
    
    if [ "$issues_found" -eq 0 ]; then
        printf "%s✓%s %s - No obvious pipe issues found\n" "$GREEN" "$NC" "$script"
    fi
done

printf "\n"

###############################################################################
# Section 3: Check CI workflow specifically
###############################################################################

printf "%s--- Checking CI workflow for pipe issues ---%s\n" "$CYAN" "$NC"

CI_WORKFLOW=".github/workflows/ci.yml"
if [ -f "$CI_WORKFLOW" ]; then
    printf "Analyzing %s...\n" "$CI_WORKFLOW"
    
    # Check for set -euo pipefail in workflow
    if grep -q "set -euo pipefail" "$CI_WORKFLOW"; then
        printf "%s⚠️  CI workflow uses 'set -euo pipefail' (bash-only)%s\n" "$YELLOW" "$NC"
        grep -n "set -euo pipefail" "$CI_WORKFLOW"
    fi
    
    # Check for pipes in run steps
    printf "\nPipes found in workflow:\n"
    grep -n "|" "$CI_WORKFLOW" 2>/dev/null | while read -r line; do
        printf "  %s%s%s\n" "$YELLOW" "$line" "$NC"
    done
else
    printf "%s⚠️  CI workflow not found%s\n" "$YELLOW" "$NC"
fi

printf "\n"

###############################################################################
# Section 4: Recommendations
###############################################################################

printf "%s=== 💡 RECOMMENDATIONS ===%s\n" "$BLUE" "$NC"
printf "\n"
printf "1. Use conditional pipefail pattern for POSIX compatibility:\n"
printf "   if (set -o pipefail) 2> /dev/null; then\n"
printf "       set -o pipefail\n"
printf "   fi\n"
printf "\n"
printf "2. Add error handling to pipes:\n"
printf "   command | other_command || { echo 'Pipeline failed'; exit 1; }\n"
printf "\n"
printf "3. Use || true for non-critical pipes:\n"
printf "   find . -name '*.log' | head -10 || true\n"
printf "\n"
printf "4. Check exit codes explicitly:\n"
printf "   if command | other_command; then\n"
printf "       echo 'Success'\n"
printf "   else\n"
printf "       echo 'Failed'\n"
printf "       exit 1\n"
printf "   fi\n"
printf "\n"

printf "%s=== Analysis complete ===%s\n" "$BLUE" "$NC"