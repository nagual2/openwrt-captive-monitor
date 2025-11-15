#!/bin/sh
# shellcheck shell=ash
set -eu

if (set -o pipefail) 2> /dev/null; then
    # shellcheck disable=SC3040
    set -o pipefail
fi

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

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== GitHub Actions Failure Diagnostics ===${NC}"
echo "Repository: $REPO"
echo "Time Period: Last $DAYS days"
echo "Limit: $LIMIT runs"
echo ""

# Build auth header if token available
AUTH_HEADER=""
if [ -n "$TOKEN" ]; then
    AUTH_HEADER="-H Authorization: token $TOKEN"
fi

###############################################################################
# Section 1: Latest Workflow Runs Overview
###############################################################################

echo -e "${BLUE}=== 📊 Latest $LIMIT Workflow Runs ===${NC}"
echo ""

curl -s $AUTH_HEADER \
    "https://api.github.com/repos/$REPO/actions/runs?per_page=$LIMIT" |
    jq -r '.workflow_runs[] |
        "\(.created_at | split("T")[0]) | \(.created_at | split("T")[1] | split("Z")[0]) | \(.name) | \(.head_branch) | \(.conclusion)"' |
    while read -r DATE TIME WORKFLOW BRANCH CONCLUSION; do
        if [ "$CONCLUSION" = "success" ]; then
            echo -e "${GREEN}✓${NC} $DATE $TIME | $WORKFLOW | $BRANCH"
        elif [ "$CONCLUSION" = "failure" ]; then
            echo -e "${RED}✗${NC} $DATE $TIME | $WORKFLOW | $BRANCH"
        else
            echo -e "${YELLOW}⊘${NC} $DATE $TIME | $WORKFLOW | $BRANCH"
        fi
    done

echo ""

###############################################################################
# Section 2: Latest Failed Run Details
###############################################################################

echo -e "${BLUE}=== ❌ Latest Failed Run Analysis ===${NC}"
echo ""

LATEST_FAILED=$(curl -s $AUTH_HEADER \
    "https://api.github.com/repos/$REPO/actions/runs?status=failure&per_page=1" |
    jq -r '.workflow_runs[0] | .id // empty')

if [ -n "$LATEST_FAILED" ] && [ "$LATEST_FAILED" != "null" ]; then
    echo "Failed Run ID: $LATEST_FAILED"
    echo ""

    # Get run metadata
    echo -e "${BLUE}--- RUN METADATA ---${NC}"
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
    echo ""

    # Get failed jobs and steps
    echo -e "${BLUE}--- FAILED JOBS AND STEPS ---${NC}"
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
    echo ""
else
    echo "No failed runs found"
fi

###############################################################################
# Section 3: Failure Statistics
###############################################################################

echo -e "${BLUE}=== 📈 Failure Statistics (Last $DAYS Days) ===${NC}"
echo ""

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
echo ""
echo -e "Success Rate: ${GREEN}${SUCCESS_RATE}%${NC} ($SUCCEEDED/$TOTAL)"

if [ "$FAILED" -gt 0 ]; then
    FAILURE_RATE=$(((FAILED * 100) / TOTAL))
    echo -e "Failure Rate: ${RED}${FAILURE_RATE}%${NC} ($FAILED/$TOTAL)"
fi

echo ""

###############################################################################
# Section 4: Common Failure Patterns
###############################################################################

echo -e "${BLUE}=== 🔍 Common Failure Patterns ===${NC}"
echo ""

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
        echo "  Run $RUN_ID: Failed steps: $FAILED_STEPS"
        PATTERN_COUNT=$((PATTERN_COUNT + 1))
    fi
done

if [ "$PATTERN_COUNT" -eq 0 ]; then
    echo "  No clear failure patterns found in recent runs"
fi

echo ""

###############################################################################
# Section 5: Recommendations
###############################################################################

if [ "$FAILED" -gt 5 ]; then
    echo -e "${YELLOW}=== ⚠️  RECOMMENDATIONS ===${NC}"
    echo ""
    echo "High failure rate detected (${FAILURE_RATE}%). Consider:"
    echo "  1. Check external dependencies (feed mirrors, CDNs, GitHub API limits)"
    echo "  2. Review retry logic configuration (timeouts, backoff strategy)"
    echo "  3. Analyze workflow logs for specific error messages"
    echo "  4. Check GitHub Status for service incidents"
    echo ""
fi

echo -e "${BLUE}=== Report Complete ===${NC}"
