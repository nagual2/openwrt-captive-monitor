#!/bin/sh
# shellcheck shell=ash
# Test script for version calculation logic
# This validates the date-based version scheme vYYYY.M.D.N

set -eu

echo "=== Testing Date-Based Version Calculation ==="
echo ""

# Test function
test_version_calculation() {
	local test_name="$1"
	local existing_tags="$2"
	local expected_version="$3"

	echo "Test: $test_name"
	echo "Existing tags: ${existing_tags:-<none>}"

	# Calculate version using the same logic as the workflow
	YEAR=$(date -u +%Y)
	MONTH=$(date -u +%-m)
	DAY=$(date -u +%-d)
	DATE_PREFIX="v${YEAR}.${MONTH}.${DAY}"

	# Simulate tag listing
	if [ -n "$existing_tags" ]; then
		LAST_SEQUENCE=$(echo "$existing_tags" | sed -nE "s/^${DATE_PREFIX}\.([0-9]+)$/\1/p" | sort -n | tail -n1)
	else
		LAST_SEQUENCE=""
	fi

	if [ -z "$LAST_SEQUENCE" ]; then
		NEXT_SEQUENCE=1
	else
		NEXT_SEQUENCE=$((LAST_SEQUENCE + 1))
	fi

	NEW_TAG="${DATE_PREFIX}.${NEXT_SEQUENCE}"

	echo "Expected: $expected_version"
	echo "Got: $NEW_TAG"

	if [ "$NEW_TAG" = "$expected_version" ]; then
		echo "✅ PASS"
	else
		echo "❌ FAIL"
		return 1
	fi

	echo ""
}

# Get current date for test assertions
YEAR=$(date -u +%Y)
MONTH=$(date -u +%-m)
DAY=$(date -u +%-d)
TODAY="v${YEAR}.${MONTH}.${DAY}"

echo "Today's date prefix: $TODAY"
echo ""

# Test cases
echo "Running test cases..."
echo ""

# Test 1: No existing tags for today
test_version_calculation \
	"No tags for today" \
	"" \
	"${TODAY}.1"

# Test 2: One tag exists for today
test_version_calculation \
	"One tag exists (${TODAY}.1)" \
	"${TODAY}.1" \
	"${TODAY}.2"

# Test 3: Multiple tags exist for today
test_version_calculation \
	"Multiple tags exist (${TODAY}.1, ${TODAY}.2)" \
	"${TODAY}.1
${TODAY}.2" \
	"${TODAY}.3"

# Test 4: Non-sequential tags (should use highest)
test_version_calculation \
	"Non-sequential tags (${TODAY}.1, ${TODAY}.5)" \
	"${TODAY}.1
${TODAY}.5" \
	"${TODAY}.6"

# Test 5: Large sequence number
test_version_calculation \
	"Large sequence (${TODAY}.99)" \
	"${TODAY}.99" \
	"${TODAY}.100"

echo "=== All tests completed ==="
echo ""

# Test regex pattern matching
echo "Testing regex pattern matching..."
echo ""

# Function to test if a tag matches the date pattern
matches_pattern() {
	local tag="$1"
	local pattern="^v[0-9]{4}\.(1[0-2]|[1-9])\.(3[01]|[12][0-9]|[1-9])\.[0-9]+$"

	if echo "$tag" | grep -qE "$pattern"; then
		return 0
	else
		return 1
	fi
}

# Test valid tags
echo "Testing valid tags:"
for tag in \
	"v2025.1.15.1" \
	"v2025.12.31.999" \
	"v2024.2.5.1" \
	"v2025.1.1.1"; do
	if matches_pattern "$tag"; then
		echo "  ✅ $tag - matches pattern"
	else
		echo "  ❌ $tag - SHOULD match but doesn't"
	fi
done
echo ""

# Test invalid tags
echo "Testing invalid tags (should NOT match):"
for tag in \
	"v2025.01.15.1" \
	"v2025.1.05.1" \
	"2025.1.15.1" \
	"v2025.1.15" \
	"v2025.13.1.1" \
	"v2025.1.32.1"; do
	if matches_pattern "$tag"; then
		echo "  ❌ $tag - should NOT match but does"
	else
		echo "  ✅ $tag - correctly rejected"
	fi
done

echo ""
echo "=== Testing complete ==="
