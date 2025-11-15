#!/bin/sh
# shellcheck shell=ash
set -eu

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

# Source shared color definitions so output formatting stays consistent
# shellcheck source=lib/colors.sh
. "$(dirname "$0")/lib/colors.sh"

# Ensure token is present
if [ -z "$TOKEN" ]; then
    printf "%s❌ ERROR: GITHUB_TOKEN environment variable not set%s\n" "$RED" "$NC"
    echo "Please set GITHUB_TOKEN to authenticate with GitHub API"
    exit 1
fi

AUTH_HEADER="-H Authorization: token $TOKEN"

printf "%s════════════════════════════════════════════════════════════════%s\n" "$BLUE" "$NC"
printf "%s🔍 PARSING LATEST FAILED WORKFLOWS%s\n" "$BLUE" "$NC"
printf "%s════════════════════════════════════════════════════════════════%s\n" "$BLUE" "$NC"
printf "Repository: %s\n" "$REPO"
printf "\n"

# Get the two most recent failed runs
printf "%s📋 Fetching latest failed runs...%s\n" "$CYAN" "$NC"
printf "\n"

FAILED_RUNS=$(curl -s $AUTH_HEADER \
    "https://api.github.com/repos/$REPO/actions/runs?status=failure&per_page=10" |
    jq -r '.workflow_runs[] | "\(.id)|\(.name)|\(.head_branch)|\(.run_number)"')

if [ -z "$FAILED_RUNS" ]; then
    printf "%s⚠️  No failed runs found%s\n" "$YELLOW" "$NC"
    exit 0
fi

printf "%s\n" "Found failed runs:"
echo "$FAILED_RUNS" | head -5
printf "\n"

# Function to analyze a single run
analyze_run() {
    local RUN_ID="$1"
    local RUN_NUMBER="$2"

    if [ -z "$RUN_ID" ] || [ "$RUN_ID" = "null" ]; then
        return
    fi

    printf "%s════════════════════════════════════════════════════════════════%s\n" "$BLUE" "$NC"
    printf "%s📌 ANALYZING RUN #%s (ID: %s)%s\n" "$MAGENTA" "$RUN_NUMBER" "$RUN_ID" "$NC"
    printf "%s════════════════════════════════════════════════════════════════%s\n" "$BLUE" "$NC"
    printf "\n"

    # Get run info
    printf "%s--- RUN DETAILS ---%s\n" "$CYAN" "$NC"
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

    printf "\n"
    printf "%s--- FAILED JOBS ---%s\n" "$CYAN" "$NC"
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

    printf "\n"
    printf "%s--- DOWNLOADING LOGS ---%s\n" "$CYAN" "$NC"
    LOGS_FILE="run-${RUN_ID}-logs.zip"
    TEMP_DIR=$(mktemp -d)

    if curl -s $AUTH_HEADER \
        "https://api.github.com/repos/$REPO/actions/runs/$RUN_ID/attempts/1/logs" \
        -L -o "$LOGS_FILE" 2>&1; then

        if [ -f "$LOGS_FILE" ] && [ -s "$LOGS_FILE" ]; then
            FILE_SIZE=$(stat -f%z "$LOGS_FILE" 2> /dev/null || stat -c%s "$LOGS_FILE" 2> /dev/null || echo "unknown")
            printf "%s✓ Logs downloaded (%s bytes)%s\n" "$GREEN" "$FILE_SIZE" "$NC"

            # Extract logs to temp directory
            if unzip -q "$LOGS_FILE" -d "$TEMP_DIR" 2> /dev/null; then
                printf "%s✓ Logs extracted%s\n" "$GREEN" "$NC"

                printf "\n"
                printf "%s--- 🔴 ERROR LINES ---%s\n" "$RED" "$NC"

                # Find and display error lines
                ERROR_FOUND=0
                find "$TEMP_DIR" -name "*.txt" 2> /dev/null | sort | while read -r logfile; do
                    if [ -f "$logfile" ] && grep -qi "error\|failed\|fatal\|exception\|panic\|warning" "$logfile" 2> /dev/null; then
                        ERROR_FOUND=1
                        printf '\n'
                        printf '%s📄 %s:%s\n' "$YELLOW" "$(basename "$logfile")" "$NC"
                        printf '%s\n' '---'

                        # Show context around errors - top 20 error lines
                        "[ -f "$logfile" ] && grep -i "error\|failed\|fatal\|exception\|panic" "$logfile" 2> /dev/null | head -20 | while read -r line; do
                            if echo "$line" | grep -qi "fatal\|exception\|panic"; then
                                printf "%s%s%s\n" "$RED" "$line" "$NC"
                            elif echo "$line" | grep -qi "failed"; then
                                printf "%s%s%s\n" "$RED" "$line" "$NC"
                            elif echo "$line" | grep -qi "error"; then
                                printf "%s%s%s\n" "$YELLOW" "$line" "$NC"
                            else
                                printf "%s%s%s\n" "$YELLOW" "$line" "$NC"
                            fi
                        done
                    fi
                done

                if [ "$ERROR_FOUND" -eq 0 ]; then
                    printf "%s⚠️  No error patterns found in logs%s\n" "$YELLOW" "$NC"
                fi

                printf "\n"
                printf "%s--- LOG FILES SUMMARY ---%s\n" "$CYAN" "$NC"
                find "$TEMP_DIR" -name "*.txt" 2>/dev/null | sort | while read -r logfile; do
                    if [ -f "$logfile" ]; then
                        SIZE=$(wc -l < "$logfile" 2>/dev/null || echo "0")
                        printf "  %s: %s lines\n" "$(basename "$logfile")" "$SIZE"
                    fi
                done
            else
                printf "%s⚠️  Could not extract logs%s\n" "$RED" "$NC"
            fi

            rm -f "$LOGS_FILE"
        else
            printf "%s⚠️  Downloaded file is empty%s\n" "$RED" "$NC"
        fi
    else
        printf "%s⚠️  Could not download logs%s\n" "$RED" "$NC"
    fi

    # Cleanup temp directory
    rm -rf "$TEMP_DIR"

    printf "\n"
    printf "\n"
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

printf "%s════════════════════════════════════════════════════════════════%s\n" "$BLUE" "$NC"
printf "%s✅ Analysis complete%s\n" "$GREEN" "$NC"
printf "%s════════════════════════════════════════════════════════════════%s\n" "$BLUE" "$NC"
