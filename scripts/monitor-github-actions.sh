#!/bin/sh
# shellcheck shell=ash
set -eu

###############################################################################
# GitHub Actions Monitor Script
#
# Provides comprehensive monitoring and analysis of GitHub Actions workflows.
# Helps identify failing checks and provides actionable fixes.
#
# Usage: ./scripts/monitor-github-actions.sh [REPO] [BRANCH]
###############################################################################

REPO="${1:-nagual2/openwrt-captive-monitor}"
BRANCH="${2:-$(git branch --show-current 2> /dev/null || echo 'main')}"
TOKEN="${GITHUB_TOKEN:-}"

# Source shared color definitions
# shellcheck source=lib/colors.sh
. "$(dirname "$0")/lib/colors.sh"

printf "%s=== 🚀 GITHUB ACTIONS MONITOR ===%s\n" "$BLUE" "$NC"
printf "Repository: %s\n" "$REPO"
printf "Branch: %s\n" "$BRANCH"
printf "\n"

# Build auth header if token available
AUTH_HEADER=""
if [ -n "$TOKEN" ]; then
    AUTH_HEADER="-H Authorization: token $TOKEN"
    printf "%s✓ Using GitHub token for authentication%s\n" "$GREEN" "$NC"
else
    printf "%s⚠️  No GITHUB_TOKEN found, using unauthenticated access (rate limited)%s\n" "$YELLOW" "$NC"
fi

printf "\n"

###############################################################################
# Function to get PR information
###############################################################################

get_pr_info() {
    if [ -n "$TOKEN" ]; then
        # Try to find PR for this branch
        PR_INFO=$(curl -s $AUTH_HEADER \
            "https://api.github.com/repos/$REPO/pulls?head=$BRANCH&state=open" |
            jq -r '.[0] // empty')

        if [ -n "$PR_INFO" ] && [ "$PR_INFO" != "null" ]; then
            PR_NUMBER=$(echo "$PR_INFO" | jq -r '.number')
            PR_STATUS=$(echo "$PR_INFO" | jq -r '.state')
            PR_MERGEABLE=$(echo "$PR_INFO" | jq -r '.mergeable // "unknown"')

            printf "%s--- 📋 PULL REQUEST INFO ---%s\n" "$CYAN" "$NC"
            printf "PR Number: %s\n" "$PR_NUMBER"
            printf "Status: %s\n" "$PR_STATUS"
            printf "Mergeable: %s\n" "$PR_MERGEABLE"
            printf "\n"

            # Get PR status checks
            printf "%s--- 🔍 STATUS CHECKS ---%s\n" "$CYAN" "$NC"
            curl -s $AUTH_HEADER \
                "https://api.github.com/repos/$REPO/pulls/$PR_NUMBER/status" |
                jq -r '.statuses[] |
                    "\(.context): \(.state) (\(.created_at))"' |
                while read -r status_line; do
                    if echo "$status_line" | grep -q "success"; then
                        printf "%s✓%s %s\n" "$GREEN" "$NC" "$status_line"
                    elif echo "$status_line" | grep -q "failure\|error"; then
                        printf "%s✗%s %s\n" "$RED" "$NC" "$status_line"
                    elif echo "$status_line" | grep -q "pending"; then
                        printf "%s⏳%s %s\n" "$YELLOW" "$NC" "$status_line"
                    else
                        printf "%s⊘%s %s\n" "$YELLOW" "$NC" "$status_line"
                    fi
                done
            printf "\n"

            return "$PR_NUMBER"
        fi
    fi

    return 0
}

###############################################################################
# Function to get latest workflow runs
###############################################################################

get_workflow_runs() {
    printf "%s--- 📊 LATEST WORKFLOW RUNS ---%s\n" "$CYAN" "$NC"

    # Get runs for this branch
    curl -s $AUTH_HEADER \
        "https://api.github.com/repos/$REPO/actions/runs?branch=$BRANCH&per_page=10" |
        jq -r '.workflow_runs[] |
            "\(.id)|\(.name)|\(.status)|\(.conclusion)|\(.created_at)|\(.html_url)"' |
        while IFS='|' read -r run_id name status conclusion created_at html_url; do
            if [ -n "$run_id" ] && [ "$run_id" != "null" ]; then
                case "$conclusion" in
                    "success")
                        printf "%s✓%s %s | %s | %s\n" "$GREEN" "$NC" "$name" "$status" "$created_at"
                        ;;
                    "failure")
                        printf "%s✗%s %s | %s | %s\n" "$RED" "$NC" "$name" "$status" "$created_at"
                        printf "    🔗 %s\n" "$html_url"
                        ;;
                    "cancelled")
                        printf "%s⊘%s %s | %s | %s\n" "$YELLOW" "$NC" "$name" "$status" "$created_at"
                        ;;
                    *)
                        printf "%s⏳%s %s | %s | %s\n" "$YELLOW" "$NC" "$name" "$status" "$created_at"
                        ;;
                esac
            fi
        done
    printf "\n"
}

###############################################################################
# Function to analyze failed runs
###############################################################################

analyze_failures() {
    printf "%s--- ❌ FAILED RUN ANALYSIS ---%s\n" "$CYAN" "$NC"

    # Get latest failed run
    FAILED_RUN=$(curl -s $AUTH_HEADER \
        "https://api.github.com/repos/$REPO/actions/runs?branch=$BRANCH&status=failure&per_page=1" |
        jq -r '.workflow_runs[0] | .id // empty')

    if [ -n "$FAILED_RUN" ] && [ "$FAILED_RUN" != "null" ]; then
        printf "Latest failed run ID: %s\n" "$FAILED_RUN"

        # Get run details
        RUN_DETAILS=$(curl -s $AUTH_HEADER \
            "https://api.github.com/repos/$REPO/actions/runs/$FAILED_RUN")

        WORKFLOW_NAME=$(echo "$RUN_DETAILS" | jq -r '.name')
        TRIGGER_EVENT=$(echo "$RUN_DETAILS" | jq -r '.event')
        COMMIT_SHA=$(echo "$RUN_DETAILS" | jq -r '.head_sha' | cut -c1-8)

        printf "Workflow: %s\n" "$WORKFLOW_NAME"
        printf "Trigger: %s\n" "$TRIGGER_EVENT"
        printf "Commit: %s\n" "$COMMIT_SHA"
        printf "\n"

        # Get failed jobs
        printf "Failed jobs:\n"
        curl -s $AUTH_HEADER \
            "https://api.github.com/repos/$REPO/actions/runs/$FAILED_RUN/jobs" |
            jq -r '.jobs[] |
                select(.conclusion == "failure") |
                "  \(.name): \(.conclusion) (started: \(.started_at))"' |
            while read -r job_line; do
                printf "%s%s%s\n" "$RED" "$job_line" "$NC"
            done

        printf "\n"

        # Provide specific fix recommendations based on workflow
        case "$WORKFLOW_NAME" in
            "CI")
                printf "%s💡 CI FAILURE FIXES:%s\n" "$BLUE" "$NC"
                printf "1. Check for shell script syntax errors\n"
                printf "2. Verify POSIX compatibility (avoid bash-specific features)\n"
                printf "3. Check for pipe issues: run ./scripts/check-pipe-guards.sh\n"
                printf "4. Validate workflows: ./scripts/validate-workflows.sh\n"
                printf "\n"
                ;;
            "Security Scanning")
                printf "%s💡 SECURITY SCANNING FAILURE FIXES:%s\n" "$BLUE" "$NC"
                printf "1. Check for new security vulnerabilities\n"
                printf "2. Update dependencies if needed\n"
                printf "3. Review any CodeQL findings\n"
                printf "\n"
                ;;
            "Release Please")
                printf "%s💡 RELEASE FAILURE FIXES:%s\n" "$BLUE" "$NC"
                printf "1. Check version format and changelog\n"
                printf "2. Verify release configuration\n"
                printf "3. Ensure all required status checks pass\n"
                printf "\n"
                ;;
        esac

        return "$FAILED_RUN"
    else
        printf "%s✓ No failed runs found for branch %s%s\n" "$GREEN" "$BRANCH" "$NC"
        return 0
    fi
}

###############################################################################
# Function to provide actionable recommendations
###############################################################################

provide_recommendations() {
    printf "%s=== 🎯 ACTIONABLE RECOMMENDATIONS ===%s\n" "$BLUE" "$NC"
    printf "\n"

    printf "1. %sIMMEDIATE ACTIONS:%s\n" "$YELLOW" "$NC"
    printf "   • Run pipe guards check: ./scripts/check-pipe-guards.sh\n"
    printf "   • Validate workflows: ./scripts/validate-workflows.sh\n"
    printf "   • Test locally with BusyBox: busybox ash tests/run.sh\n"
    printf "\n"

    printf "2. %sIF CI FAILURES:%s\n" "$YELLOW" "$NC"
    printf "   • Check for 'set -euo pipefail' in workflows (should be conditional)\n"
    printf "   • Verify all scripts use #!/bin/sh shebang\n"
    printf "   • Ensure shellcheck SC3040 is disabled for conditional pipefail\n"
    printf "\n"

    printf "3. %sIF SECURITY FAILURES:%s\n" "$YELLOW" "$NC"
    printf "   • Review dependency updates\n"
    printf "   • Check for new vulnerability findings\n"
    printf "   • Validate CodeQL configuration\n"
    printf "\n"

    printf "4. %sMONITORING COMMANDS:%s\n" "$YELLOW" "$NC"
    printf "   • Monitor workflows: ./scripts/diagnose-github-actions.sh\n"
    printf "   • Parse failures: ./scripts/parse-latest-failed-workflows.sh\n"
    printf "   • Check pipes: ./scripts/check-pipe-guards.sh\n"
    printf "\n"
}

###############################################################################
# Main execution
###############################################################################

# Get PR information
get_pr_info
PR_NUMBER=$?

# Get workflow runs
get_workflow_runs

# Analyze failures
analyze_failures
FAILED_RUN=$?

# Provide recommendations
provide_recommendations

# Summary
printf "%s=== 📋 SUMMARY ===%s\n" "$BLUE" "$NC"
if [ "$PR_NUMBER" -gt 0 ]; then
    printf "Pull Request: #%s\n" "$PR_NUMBER"
fi

if [ "$FAILED_RUN" -gt 0 ]; then
    printf "Latest Failed Run: %s\n" "$FAILED_RUN"
    printf "%s⚠️  Action required: Fix failing workflows%s\n" "$YELLOW" "$NC"
else
    printf "%s✓ No critical issues detected%s\n" "$GREEN" "$NC"
fi

printf "\n%s=== Monitor complete ===%s\n" "$BLUE" "$NC"
