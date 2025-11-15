#!/bin/sh
# shellcheck shell=ash
set -eu

###############################################################################
# GitHub Actions Failure Diagnostics Script
#
# Fetches and analyzes GitHub Actions workflow runs to identify failure
# patterns, root causes, and provides targeted fix recommendations.
#
# Usage: ./scripts/diagnose-github-actions.sh [REPO] [DAYS] [LIMIT]
# Examples:
#   ./scripts/diagnose-github-actions.sh
#   ./scripts/diagnose-github-actions.sh "owner/repo" 30 50
###############################################################################

REPO="${1:-nagual2/openwrt-captive-monitor}"
DAYS="${2:-7}"
LIMIT="${3:-15}"
TOKEN="${GITHUB_TOKEN:-}"

# ANSI color codes (POSIX-safe)
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
NC='\033[0m' # No Color

# Disable colors if NO_COLOR is set or stdout is not a TTY
if [ -n "${NO_COLOR:-}" ] || [ ! -t 1 ]; then
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

printf "%s=== GitHub Actions Failure Diagnostics ===%s\n" "$BLUE" "$NC"
printf "Repository: %s\n" "$REPO"
printf "Time Period: Last %s days\n" "$DAYS"
printf "Limit: %s runs\n" "$LIMIT"
printf "\n"

# Build auth header if token available
AUTH_HEADER=""
if [ -n "$TOKEN" ]; then
    AUTH_HEADER="-H Authorization: token $TOKEN"
fi

###############################################################################
# Section 1: Latest Workflow Runs Overview
###############################################################################

printf "%s=== 📊 Latest %s Workflow Runs ===%s\n" "$BLUE" "$LIMIT" "$NC"
printf "\n"

curl -s $AUTH_HEADER \
    "https://api.github.com/repos/$REPO/actions/runs?per_page=$LIMIT" |
    jq -r '.workflow_runs[] |
        "\(.created_at | split("T")[0]) | \(.created_at | split("T")[1] | split("Z")[0]) | \(.name) | \(.head_branch) | \(.conclusion)"' |
    while read -r DATE TIME WORKFLOW BRANCH CONCLUSION; do
        if [ "$CONCLUSION" = "success" ]; then
            printf "%s✓%s %s %s | %s | %s\n" "$GREEN" "$NC" "$DATE" "$TIME" "$WORKFLOW" "$BRANCH"
        elif [ "$CONCLUSION" = "failure" ]; then
            printf "%s✗%s %s %s | %s | %s\n" "$RED" "$NC" "$DATE" "$TIME" "$WORKFLOW" "$BRANCH"
        else
            printf "%s⊘%s %s %s | %s | %s\n" "$YELLOW" "$NC" "$DATE" "$TIME" "$WORKFLOW" "$BRANCH"
        fi
    done

printf "\n"

###############################################################################
# Section 2: Latest Failed Run Details
###############################################################################

printf "%s=== ❌ Latest Failed Run Analysis ===%s\n" "$BLUE" "$NC"
printf "\n"

LATEST_FAILED=$(curl -s $AUTH_HEADER \
    "https://api.github.com/repos/$REPO/actions/runs?status=failure&per_page=1" |
    jq -r '.workflow_runs[0] | .id // empty')

if [ -n "$LATEST_FAILED" ] && [ "$LATEST_FAILED" != "null" ]; then
    printf "Failed Run ID: %s\n" "$LATEST_FAILED"
    printf "\n"

    # Get run metadata
    printf "%s--- RUN METADATA ---%s\n" "$BLUE" "$NC"
    curl -s $AUTH_HEADER \
        "https://api.github.com/repos/$REPO/actions/runs/$LATEST_FAILED" |
        jq '{
            name: .name,
            status: .status,
            conclusion: .conclusion,
            branch: .head_branch,
            created: .created_at,
            attempt: .run_attempt
        }'
    printf "\n"

    # Get failed jobs and steps
    printf "%s--- FAILED JOBS AND STEPS ---%s\n" "$BLUE" "$NC"
    curl -s $AUTH_HEADER \
        "https://api.github.com/repos/$REPO/actions/runs/$LATEST_FAILED/jobs" |
        jq '.jobs[] |
            select(.conclusion != "success") |
            {
                job_name: .name,
                status: .status,
                conclusion: .conclusion,
                failed_steps: [
                    .steps[] |
                    select(.conclusion != "success" and .conclusion != "skipped") |
                    {
                        number: .number,
                        name: .name,
                        conclusion: .conclusion
                    }
                ]
            }' | head -50
    printf "\n"
else
    printf "%s\n" "No failed runs found"
fi

###############################################################################
# Section 3: Failure Statistics
###############################################################################

printf "%s=== 📈 Failure Statistics (Last %s Days) ===%s\n" "$BLUE" "$DAYS" "$NC"
printf "\n"

STATS=$(curl -s $AUTH_HEADER \
    "https://api.github.com/repos/$REPO/actions/runs?per_page=100" |
    jq '{
        total: (.workflow_runs | length),
        succeeded: ([.workflow_runs[] | select(.conclusion == "success")] | length),
        failed: ([.workflow_runs[] | select(.conclusion == "failure")] | length),
        cancelled: ([.workflow_runs[] | select(.conclusion == "cancelled")] | length)
    }')

TOTAL=$(echo "$STATS" | jq -r '.total')
SUCCEEDED=$(echo "$STATS" | jq -r '.succeeded')
FAILED=$(echo "$STATS" | jq -r '.failed')
# shellcheck disable=SC2034
CANCELLED=$(echo "$STATS" | jq -r '.cancelled')
SUCCESS_RATE=$(((SUCCEEDED * 100) / TOTAL))

echo "$STATS" | jq .
printf "\n"
printf "Success Rate: %s%s%%%s (%s/%s)\n" "$GREEN" "$SUCCESS_RATE" "$NC" "$SUCCEEDED" "$TOTAL"

if [ "$FAILED" -gt 0 ]; then
    FAILURE_RATE=$(((FAILED * 100) / TOTAL))
    printf "Failure Rate: %s%s%%%s (%s/%s)\n" "$RED" "$FAILURE_RATE" "$NC" "$FAILED" "$TOTAL"
fi

printf "\n"

###############################################################################
# Section 4: Common Failure Patterns
###############################################################################

printf "%s=== 🔍 Common Failure Patterns ===%s\n" "$BLUE" "$NC"
printf "\n"

echo "Analyzing last 10 failed runs for patterns..."
FAILURES=$(curl -s $AUTH_HEADER \
    "https://api.github.com/repos/$REPO/actions/runs?status=failure&per_page=10" |
    jq -r '.workflow_runs[] | .id')

PATTERN_COUNT=0

echo "$FAILURES" | while read -r RUN_ID; do
    if [ -z "$RUN_ID" ] || [ "$RUN_ID" = "null" ]; then
        continue
    fi

    FAILED_STEPS=$(curl -s $AUTH_HEADER \
        "https://api.github.com/repos/$REPO/actions/runs/$RUN_ID/jobs" |
        jq -r '.jobs[] |
            select(.conclusion == "failure") |
            .steps[] |
            select(.conclusion == "failure") |
            .name' | tr '\n' '; ')

    if [ -n "$FAILED_STEPS" ]; then
        printf "  Run %s: Failed steps: %s\n" "$RUN_ID" "$FAILED_STEPS"
        PATTERN_COUNT=$((PATTERN_COUNT + 1))
    fi
done

if [ "$PATTERN_COUNT" -eq 0 ]; then
    printf "  %s\n" "No clear failure patterns found in recent runs"
fi

printf "\n"

###############################################################################
# Section 5: Recommendations
###############################################################################

if [ "$FAILED" -gt 5 ]; then
    printf "%s=== ⚠️  RECOMMENDATIONS ===%s\n" "$YELLOW" "$NC"
    printf "\n"
    echo "High failure rate detected (${FAILURE_RATE}%). Consider:"
    echo "  1. Check external dependencies (feed mirrors, CDNs, GitHub API limits)"
    echo "  2. Review retry logic configuration (timeouts, backoff strategy)"
    echo "  3. Analyze workflow logs for specific error messages"
    echo "  4. Check GitHub Status for service incidents"
    printf "\n"
fi

printf "%s=== Report Complete ===%s\n" "$BLUE" "$NC"
