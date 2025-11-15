#!/bin/sh
# shellcheck shell=ash
set -eu

if (set -o pipefail) 2> /dev/null; then
    # shellcheck disable=SC3040
    set -o pipefail
fi

###############################################################################
# GitHub Actions CI Helper Script
#
# Comprehensive helper for monitoring, diagnosing, and fixing GitHub Actions CI issues.
# Integrates pipe guard checking, workflow validation, and status monitoring.
#
# Usage: ./scripts/ci-helper.sh [COMMAND] [OPTIONS]
#
# Commands:
#   check          - Run pipe guards analysis
#   monitor        - Monitor GitHub Actions status
#   validate       - Validate workflow files
#   diagnose       - Diagnose latest failures
#   fix-pipes      - Apply pipe guard fixes automatically
#   all            - Run all checks and diagnostics
###############################################################################

# Source shared color definitions
# shellcheck source=lib/colors.sh
. "$(dirname "$0")/lib/colors.sh"

###############################################################################
# Help function
###############################################################################

show_help() {
    cat << EOF
${BLUE}GitHub Actions CI Helper${NC}

${YELLOW}USAGE:${NC}
    $0 [COMMAND] [OPTIONS]

${YELLOW}COMMANDS:${NC}
    check          Run pipe guards analysis
    monitor        Monitor GitHub Actions status
    validate       Validate workflow files  
    diagnose       Diagnose latest failures
    fix-pipes      Apply pipe guard fixes automatically
    all            Run all checks and diagnostics
    help           Show this help message

${YELLOW}OPTIONS:${NC}
    --repo REPO    Repository name (default: nagual2/openwrt-captive-monitor)
    --branch BRANCH Branch name (default: current branch)
    --token TOKEN  GitHub token (default: \$GITHUB_TOKEN)

${YELLOW}EXAMPLES:${NC}
    $0 check                    # Check pipe guards
    $0 monitor --repo user/repo # Monitor specific repository
    $0 all --branch main        # Run all checks on main branch
    $0 diagnose                  # Diagnose latest failures

EOF
}

###############################################################################
# Parse arguments
###############################################################################

COMMAND="${1:-help}"
REPO="nagual2/openwrt-captive-monitor"
BRANCH=""
TOKEN=""

shift

while [ $# -gt 0 ]; do
    case "$1" in
        --repo)
            REPO="$2"
            shift 2
            ;;
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --token)
            TOKEN="$2"
            shift 2
            ;;
        *)
            printf "%s❌ Unknown option: %s%s\n" "$RED" "$1" "$NC"
            show_help
            exit 1
            ;;
    esac
done

# Set default branch if not specified
if [ -z "$BRANCH" ]; then
    BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
fi

# Set token if provided
if [ -n "$TOKEN" ]; then
    export GITHUB_TOKEN="$TOKEN"
fi

###############################################################################
# Command functions
###############################################################################

cmd_check() {
    printf "%s=== 🔍 RUNNING PIPE GUARDS CHECK ===%s\n" "$BLUE" "$NC"
    if [ -x "$(dirname "$0")/check-pipe-guards.sh" ]; then
        "$(dirname "$0")/check-pipe-guards.sh" .
    else
        printf "%s❌ check-pipe-guards.sh not found or not executable%s\n" "$RED" "$NC"
        return 1
    fi
}

cmd_monitor() {
    printf "%s=== 📊 MONITORING GITHUB ACTIONS ===%s\n" "$BLUE" "$NC"
    if [ -x "$(dirname "$0")/monitor-github-actions.sh" ]; then
        "$(dirname "$0")/monitor-github-actions.sh" "$REPO" "$BRANCH"
    else
        printf "%s❌ monitor-github-actions.sh not found or not executable%s\n" "$RED" "$NC"
        return 1
    fi
}

cmd_validate() {
    printf "%s=== ✅ VALIDATING WORKFLOWS ===%s\n" "$BLUE" "$NC"
    if [ -x "$(dirname "$0")/validate-workflows.sh" ]; then
        "$(dirname "$0")/validate-workflows.sh"
    else
        printf "%s❌ validate-workflows.sh not found or not executable%s\n" "$RED" "$NC"
        return 1
    fi
}

cmd_diagnose() {
    printf "%s=== 🔧 DIAGNOSING FAILURES ===%s\n" "$BLUE" "$NC"
    if [ -x "$(dirname "$0")/diagnose-github-actions.sh" ]; then
        "$(dirname "$0")/diagnose-github-actions.sh" "$REPO"
    else
        printf "%s❌ diagnose-github-actions.sh not found or not executable%s\n" "$RED" "$NC"
        return 1
    fi
}

cmd_fix_pipes() {
    printf "%s=== 🔧 APPLYING PIPE GUARD FIXES ===%s\n" "$BLUE" "$NC"
    
    printf "Checking for scripts that need pipe guard fixes...\n"
    
    # Fix common pipe issues automatically
    find . -name "*.sh" -not -path "./.git/*" -not -path "./node_modules/*" | while read -r script; do
        # Add conditional pipefail pattern if missing
        if ! grep -q "pipefail" "$script" && grep -q "|" "$script"; then
            printf "%s🔧 Adding pipefail to %s%s\n" "$YELLOW" "$script" "$NC"
            
            # Check if script has set -eu already
            if grep -q "set -eu" "$script"; then
                # Add conditional pipefail after set -eu
                sed -i '/set -eu/a\\nif (set -o pipefail) 2> /dev/null; then\n    # shellcheck disable=SC3040\n    set -o pipefail\nfi' "$script"
            elif grep -q "#!/bin/sh" "$script"; then
                # Add after shebang
                sed -i '/#!/bin/sh/a\\nset -eu\n\nif (set -o pipefail) 2> /dev/null; then\n    # shellcheck disable=SC3040\n    set -o pipefail\nfi' "$script"
            fi
        fi
        
        # Fix find commands without error handling
        if grep -q "find.*|.*head" "$script" && ! grep -q "|| true" "$script"; then
            printf "%s🔧 Adding error handling to find pipes in %s%s\n" "$YELLOW" "$script" "$NC"
            sed -i 's/| head/|| true | head/g' "$script"
        fi
    done
    
    printf "%s✓ Pipe guard fixes applied%s\n" "$GREEN" "$NC"
}

cmd_all() {
    printf "%s=== 🚀 RUNNING COMPREHENSIVE CI CHECK ===%s\n" "$BLUE" "$NC"
    printf "\n"
    
    # Run all checks in order
    cmd_check
    printf "\n"
    
    cmd_validate
    printf "\n"
    
    cmd_monitor
    printf "\n"
    
    if [ -n "${GITHUB_TOKEN:-}" ]; then
        cmd_diagnose
        printf "\n"
    else
        printf "%s⚠️  Skipping diagnosis (no GITHUB_TOKEN)%s\n" "$YELLOW" "$NC"
        printf "\n"
    fi
    
    printf "%s=== 📋 SUMMARY ===%s\n" "$BLUE" "$NC"
    printf "All CI checks completed. Review the output above for any issues.\n"
    printf "\n"
    printf "Next steps:\n"
    printf "1. Fix any shellcheck errors found\n"
    printf "2. Address pipe guard warnings\n"
    printf "3. Resolve workflow validation issues\n"
    printf "4. Monitor GitHub Actions status\n"
    printf "\n"
}

###############################################################################
# Main execution
###############################################################################

case "$COMMAND" in
    "check")
        cmd_check
        ;;
    "monitor")
        cmd_monitor
        ;;
    "validate")
        cmd_validate
        ;;
    "diagnose")
        cmd_diagnose
        ;;
    "fix-pipes")
        cmd_fix_pipes
        ;;
    "all")
        cmd_all
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        printf "%s❌ Unknown command: %s%s\n" "$RED" "$COMMAND" "$NC"
        printf "\n"
        show_help
        exit 1
        ;;
esac