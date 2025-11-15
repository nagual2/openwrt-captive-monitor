#!/bin/sh
# shellcheck shell=ash
set -eu

if (set -o pipefail) 2> /dev/null; then
    # shellcheck disable=SC3040
    set -o pipefail
fi

REPO="nagual2/openwrt-captive-monitor"
TOKEN="${GITHUB_TOKEN:-}"

# Add auth header if token is available
AUTH_HEADER=""
if [ -n "$TOKEN" ]; then
    AUTH_HEADER="-H Authorization: token $TOKEN"
fi

echo "=== 📊 LATEST WORKFLOW RUNS ===="
curl -s $AUTH_HEADER \
    "https://api.github.com/repos/$REPO/actions/runs?per_page=15" |
    jq -r '.workflow_runs[] | "\(.created_at) | \(.name) | \(.head_branch) | \(.conclusion)"'

echo ""
echo "=== ❌ LATEST FAILED RUN DETAILS ===="

# Get latest failed run
LATEST_FAILED=$(curl -s $AUTH_HEADER \
    "https://api.github.com/repos/$REPO/actions/runs?status=failure&per_page=1" |
    jq -r '.workflow_runs[0] | .id // empty')

if [ -n "$LATEST_FAILED" ] && [ "$LATEST_FAILED" != "null" ]; then
    echo "Failed Run ID: $LATEST_FAILED"

    # Get full run details
    echo ""
    echo "--- RUN METADATA ---"
    curl -s $AUTH_HEADER \
        "https://api.github.com/repos/$REPO/actions/runs/$LATEST_FAILED" |
        jq '{
      name: .name,
      status: .status,
      conclusion: .conclusion,
      branch: .head_branch,
      created: .created_at,
      updated: .updated_at,
      attempt: .run_attempt
    }'

    echo ""
    echo "--- JOB STEPS AND FAILURES ---"
    curl -s $AUTH_HEADER \
        "https://api.github.com/repos/$REPO/actions/runs/$LATEST_FAILED/jobs" |
        jq '.jobs[] | {
      name: .name,
      conclusion: .conclusion,
      status: .status,
      steps: [.steps[] | select(.conclusion != "success") | {
        name: .name,
        conclusion: .conclusion,
        output: .output
      }]
    }'

    echo ""
    echo "--- DOWNLOADING FULL LOGS ---"
    LOGS_FILE="latest-failure-logs.zip"

    curl -s $AUTH_HEADER \
        "https://api.github.com/repos/$REPO/actions/runs/$LATEST_FAILED/attempts/1/logs" \
        -L -o "$LOGS_FILE" 2>&1

    if [ -f "$LOGS_FILE" ] && [ -s "$LOGS_FILE" ]; then
        SIZE=$(find . -name "$LOGS_FILE" -printf '%s\n' | head -1)
        echo "✓ Logs downloaded: $(numfmt --to=iec-i --suffix=B "$SIZE" 2> /dev/null || echo "$SIZE bytes")"

        # Extract and parse
        unzip -q "$LOGS_FILE" 2> /dev/null || true

        echo ""
        echo "--- ERROR MESSAGES FROM LOGS ---"
        find . -name "*.txt" 2> /dev/null | head -20 | while read -r logfile; do
            if grep -qi "error\|failed\|fatal\|exception\|panic" "$logfile" 2> /dev/null; then
                echo ""
                echo "📄 FILE: $logfile"
                echo "---"
                grep -i "error\|failed\|fatal\|exception\|panic" "$logfile" 2> /dev/null | head -30
            fi
        done
    else
        echo "⚠️  Could not download logs"
    fi
else
    echo "No failed runs found"
fi

echo ""
echo "=== 📈 FAILURE STATISTICS (LAST 7 DAYS) ===="
SEVEN_DAYS_AGO=$(date -u -d '7 days ago' '+%Y-%m-%dT%H:%M:%SZ')
curl -s $AUTH_HEADER \
    "https://api.github.com/repos/$REPO/actions/runs?per_page=50&created=%3E${SEVEN_DAYS_AGO}" |
    jq '{
    total: (.workflow_runs | length),
    succeeded: ([.workflow_runs[] | select(.conclusion == "success")] | length),
    failed: ([.workflow_runs[] | select(.conclusion == "failure")] | length),
    cancelled: ([.workflow_runs[] | select(.conclusion == "cancelled")] | length)
  }'
