#!/bin/sh

TEST_DIR=$(cd "$(dirname "$0")" && pwd)
REPO_ROOT=$(cd "$TEST_DIR/.." && pwd)
SCRIPT="$REPO_ROOT/package/openwrt-captive-monitor/files/usr/sbin/auth_conn4.sh"
MOCK_BIN="$TEST_DIR/mock_bin"

# Setup environment
export PATH="$MOCK_BIN:$PATH"
export TEST_LOG_FILE="$TEST_DIR/test.log"

# Cleanup
rm -f "$TEST_LOG_FILE"
rm -f /tmp/conn4_cookies.txt

echo "Running tests..."

# Test 1: Internet is available
echo "Test 1: Already Online"
export MOCK_INTERNET_STATUS="online"
if sh "$SCRIPT"; then
    echo "PASS: Script exited with 0"
else
    echo "FAIL: Script exited with non-zero"
    exit 1
fi

if grep -q "Internet is available" "$TEST_LOG_FILE"; then
    echo "PASS: Logged internet availability"
else
    echo "FAIL: Did not log internet availability"
    exit 1
fi

# Cleanup for next test
rm -f "$TEST_LOG_FILE"

# Test 2: Internet is offline (mocking portal detection is harder, just checking it attempts)
echo "Test 2: Offline"
export MOCK_INTERNET_STATUS="offline"

# We expect the script to fail or continue. In our mock curl, we return 000 for generate_204.
# The script will try to detect portal.
# Our mock curl returns a Location header for neverssl.
# The script will try to fetch landing page.
# This test is just a smoke test to see if it runs without syntax errors.

# Note: The script might hang or fail if subsequent curls don't behave as expected.
# But let's try running it.

# We anticipate exit 0 or 1 depending on flow.
sh "$SCRIPT" >/dev/null 2>&1
EXIT_CODE=$?

echo "Script exit code: $EXIT_CODE"
if grep -q "Internet not available" "$TEST_LOG_FILE"; then
    echo "PASS: Detected offline status"
else
    echo "FAIL: Did not detect offline status"
    exit 1
fi

echo "All tests passed!"
exit 0
