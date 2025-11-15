#!/bin/sh
# shellcheck shell=ash
set -eu

if (set -o pipefail) 2> /dev/null; then
    # shellcheck disable=SC3040
    set -o pipefail
fi

###############################################################################
# Parse Latest Failed Workflows Script
#
# Analyzes the two most recent failed GitHub Actions workflows to identify
# root causes, extract error messages, and provide detailed failure analysis.
#
# Usage: ./scripts/parse-latest-failed-workflows.sh [REPO]
# Example: ./scripts/parse-latest-failed-workflows.sh "nagual2/openwrt-captive-monitor"
###############################################################################

REPO="${1:-nagual2/openwrt-captive-monitor}"
TOKEN="${GITHUB_TOKEN:-}"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Ensure token is present
if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ ERROR: GITHUB_TOKEN environment variable not set${NC}"
    echo "Please set GITHUB_TOKEN to authenticate with GitHub API"
    exit 1
fi

AUTH_HEADER="-H Authorization: token $TOKEN"

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🔍 PARSING LATEST FAILED WORKFLOWS${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo "Repository: $REPO"
echo ""

# Get the two most recent failed runs
echo -e "${CYAN}📋 Fetching latest failed runs...${NC}"
echo ""

FAILED_RUNS=$(curl -s $AUTH_HEADER \
    "https://api.github.com/repos/$REPO/actions/runs?status=failure&per_page=10" |
    jq -r '.workflow_runs[] | "\(.id)|\(.name)|\(.head_branch)|\(.run_number)"')

if [ -z "$FAILED_RUNS" ]; then
    echo -e "${YELLOW}⚠️  No failed runs found${NC}"
    exit 0
fi

echo "Found failed runs:"
echo "$FAILED_RUNS" | head -5
echo ""

# Function to analyze a single run
analyze_run() {
    local RUN_ID="$1"
    local RUN_NUMBER="$2"

    if [ -z "$RUN_ID" ] || [ "$RUN_ID" = "null" ]; then
        return
    fi

    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${MAGENTA}📌 ANALYZING RUN #${RUN_NUMBER} (ID: ${RUN_ID})${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo ""

    # Get run info
    echo -e "${CYAN}--- RUN DETAILS ---${NC}"
    curl -s $AUTH_HEADER \
        "https://api.github.com/repos/$REPO/actions/runs/$RUN_ID" |
        jq '{
          name: .name,
          status: .status,
          conclusion: .conclusion,
          branch: .head_branch,
          created: .created_at,
          updated: .updated_at,
          run_number: .run_number
        }'

    echo ""
    echo -e "${CYAN}--- FAILED JOBS ---${NC}"
    curl -s $AUTH_HEADER \
        "https://api.github.com/repos/$REPO/actions/runs/$RUN_ID/jobs" |
        jq '.jobs[] | select(.conclusion == "failure") | {
          name: .name,
          conclusion: .conclusion,
          started_at: .started_at,
          completed_at: .completed_at,
          steps: [.steps[] | select(.conclusion != "success") | {
            name: .name,
            conclusion: .conclusion,
            number: .number
          }]
        }'

    echo ""
    echo -e "${CYAN}--- DOWNLOADING LOGS ---${NC}"
    LOGS_FILE="run-${RUN_ID}-logs.zip"
    TEMP_DIR=$(mktemp -d)

    if curl -s $AUTH_HEADER \
        "https://api.github.com/repos/$REPO/actions/runs/$RUN_ID/attempts/1/logs" \
        -L -o "$LOGS_FILE" 2>&1; then

        if [ -f "$LOGS_FILE" ] && [ -s "$LOGS_FILE" ]; then
            FILE_SIZE=$(stat -f%z "$LOGS_FILE" 2> /dev/null || stat -c%s "$LOGS_FILE" 2> /dev/null || echo "unknown")
            echo -e "${GREEN}✓ Logs downloaded ($FILE_SIZE bytes)${NC}"

            # Extract logs to temp directory
            if unzip -q "$LOGS_FILE" -d "$TEMP_DIR" 2> /dev/null; then
                echo -e "${GREEN}✓ Logs extracted${NC}"

                echo ""
                echo -e "${RED}--- 🔴 ERROR LINES ---${NC}"

                # Find and display error lines
                ERROR_FOUND=0
                find "$TEMP_DIR" -name "*.txt" 2> /dev/null | sort | while read -r logfile; do
                    if grep -qi "error\|failed\|fatal\|exception\|panic\|warning" "$logfile" 2> /dev/null; then
                        ERROR_FOUND=1
                        echo ""
                        echo -e "${YELLOW}📄 $(basename "$logfile"):${NC}"
                        echo "---"

                        # Show context around errors - top 20 error lines
                        grep -i "error\|failed\|fatal\|exception\|panic" "$logfile" 2> /dev/null | head -20 | while read -r line; do
                            if echo "$line" | grep -qi "fatal\|exception\|panic"; then
                                echo -e "${RED}$line${NC}"
                            elif echo "$line" | grep -qi "failed"; then
                                echo -e "${RED}$line${NC}"
                            elif echo "$line" | grep -qi "error"; then
                                echo -e "${YELLOW}$line${NC}"
                            else
                                echo -e "${YELLOW}$line${NC}"
                            fi
                        done
                    fi
                done

                if [ "$ERROR_FOUND" -eq 0 ]; then
                    echo -e "${YELLOW}⚠️  No error patterns found in logs${NC}"
                fi

                echo ""
                echo -e "${CYAN}--- LOG FILES SUMMARY ---${NC}"
                find "$TEMP_DIR" -name "*.txt" 2> /dev/null | sort | while read -r logfile; do
                    SIZE=$(wc -l < "$logfile")
                    echo "  $(basename "$logfile"): $SIZE lines"
                done
            else
                echo -e "${RED}⚠️  Could not extract logs${NC}"
            fi

            rm -f "$LOGS_FILE"
        else
            echo -e "${RED}⚠️  Downloaded file is empty${NC}"
        fi
    else
        echo -e "${RED}⚠️  Could not download logs${NC}"
    fi

    # Cleanup temp directory
    rm -rf "$TEMP_DIR"

    echo ""
    echo ""
}

# Analyze the two most recent failures
count=0
echo "$FAILED_RUNS" | while read -r line; do
    count=$((count + 1))

    if [ "$count" -gt 2 ]; then
        break
    fi

    RUN_ID=$(echo "$line" | cut -d'|' -f1)
    RUN_NUMBER=$(echo "$line" | cut -d'|' -f4)

    analyze_run "$RUN_ID" "$RUN_NUMBER"
done

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Analysis complete${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
