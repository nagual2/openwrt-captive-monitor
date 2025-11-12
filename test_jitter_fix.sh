#!/bin/bash
# Test script to verify the jitter fix works correctly

set -euo pipefail

echo "=== Testing Jitter Calculation Fix ==="
echo ""

echo "Testing the original broken code (for reference):"
# shellcheck disable=SC2016
echo 'base_wait=1; jitter=$((base_wait / 5)); wait_time=$((base_wait + RANDOM % jitter))'
if bash -c 'base_wait=1; jitter=$((base_wait / 5)); wait_time=$((base_wait + RANDOM % jitter)); echo "Result: $wait_time"' 2>&1 | grep -q "division by 0"; then
    echo "❌ Original code fails with division by zero (expected)"
else
    echo "⚠️  Original code did not fail as expected"
fi
echo ""

echo "Testing the fixed code:"
# shellcheck disable=SC2016
echo 'base_wait=1; jitter=$((base_wait / 5)); if [ "$jitter" -lt 1 ]; then jitter=1; fi; random_jitter=$((RANDOM % jitter)); wait_time=$((base_wait + random_jitter))'
if bash -c 'base_wait=1; jitter=$((base_wait / 5)); if [ "$jitter" -lt 1 ]; then jitter=1; fi; random_jitter=$((RANDOM % jitter)); wait_time=$((base_wait + random_jitter)); echo "Result: wait_time=$wait_time (base=$base_wait, jitter=$jitter, random_jitter=$random_jitter)"' 2>&1; then
    echo "✅ Fixed code works correctly"
else
    echo "❌ Fixed code failed unexpectedly"
    exit 1
fi
echo ""

echo "=== Testing exponential backoff with jitter across all 10 attempts ==="
echo ""
for attempt in {1..10}; do
    bash -c "
        attempt=$attempt
        base_wait=\$((2 ** (attempt - 1)))
        jitter=\$((base_wait / 5))
        if [ \"\$jitter\" -lt 1 ]; then
            jitter=1
        fi
        random_jitter=\$((RANDOM % jitter))
        wait_time=\$((base_wait + random_jitter))
        printf \"Attempt %2d: base_wait=%4d, jitter=%3d, random_jitter=%3d, wait_time=%4d\\n\" \
            \$attempt \$base_wait \$jitter \$random_jitter \$wait_time
    "
done

echo ""
echo "=== All tests passed! ✅ ==="
