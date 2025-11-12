#!/bin/bash
set -euo pipefail

REPO="nagual2/openwrt-captive-monitor"
TOKEN="${GITHUB_TOKEN:-}"

# Use git authentication if available
if [ -z "$TOKEN" ]; then
    # Try to extract token from git remote URL
    TOKEN=$(git config --get --global github.token 2> /dev/null || echo "")
fi

if [ -z "$TOKEN" ]; then
    echo "⚠️  WARNING: GITHUB_TOKEN not set, will use public API (limited rate limit)"
    echo ""
fi

echo "📋 FETCHING LAST 150 COMMITS FROM GITHUB..."
echo "Repository: $REPO"
echo ""

# Fetch commits - get 150 per page to get all we can
if [ -n "$TOKEN" ]; then
    COMMITS_JSON=$(curl -s -H "Authorization: token $TOKEN" \
        "https://api.github.com/repos/$REPO/commits?per_page=150")
else
    COMMITS_JSON=$(curl -s \
        "https://api.github.com/repos/$REPO/commits?per_page=150")
fi

# Check if we got valid JSON
if ! echo "$COMMITS_JSON" | jq . > /dev/null 2>&1; then
    echo "❌ Error fetching commits from GitHub API"
    exit 1
fi

TOTAL=$(echo "$COMMITS_JSON" | jq '. | length')
echo "Total commits fetched: $TOTAL"
echo ""

# Part 1: Script changes (prioritize script keywords over other keywords)
echo "=== PART 1: SCRIPT CHANGES (user's code) ==="
echo "Commits that modified actual scripts/business logic:"
echo ""

SCRIPT_COMMITS=$(echo "$COMMITS_JSON" | jq -r '.[] | 
  select(
    .commit.message | 
    test("script|[.]sh|[.]lua|[.]js|src/|bin/|lib/|captive|monitor|detection|interception|handler|chain|dns|http|proxy|firewall|iptables|nftables|procd|uci"; "i")
  ) |
  "\(.sha[0:7]) | \(.commit.message | split("\n")[0]) | Author: \(.commit.author.name) | Date: \(.commit.author.date[0:10])"')

SCRIPT_COUNT=$(echo "$SCRIPT_COMMITS" | grep -c . || echo 0)
echo "$SCRIPT_COMMITS" | head -75

echo ""
echo "=== PART 2: OTHER CHANGES (CI/CD, config, docs, etc) ==="
echo "Commits that modified workflow, config, docs, or infrastructure:"
echo ""

# For OTHER, we want commits that DON'T match script keywords but DO match other keywords
OTHER_COMMITS=$(echo "$COMMITS_JSON" | jq -r '.[] | 
  select(
    (.commit.message | test("script|[.]sh|[.]lua|[.]js|src/|bin/|lib/|captive|monitor|detection|interception|handler|chain|dns|http|proxy|firewall|iptables|nftables|procd|uci"; "i") | not) and
    (.commit.message | test("workflow|github|action|ci|cd|makefile|config|readme|doc|build|test|lint|format|license|changelog|bump|release|version"; "i"))
  ) |
  "\(.sha[0:7]) | \(.commit.message | split("\n")[0]) | Author: \(.commit.author.name) | Date: \(.commit.author.date[0:10])"')

OTHER_COUNT=$(echo "$OTHER_COMMITS" | grep -c . || echo 0)
echo "$OTHER_COMMITS" | head -75

echo ""
echo "=== 📊 STATISTICS ==="
echo "Total commits analyzed: $TOTAL"
echo "Part 1 (Script changes): $SCRIPT_COUNT commits"
echo "Part 2 (Other changes): $OTHER_COUNT commits"
echo "Uncategorized: $((TOTAL - SCRIPT_COUNT - OTHER_COUNT)) commits"
echo ""
echo "Breakdown:"
if [ "$TOTAL" -gt 0 ]; then
    SCRIPT_PCT=$((SCRIPT_COUNT * 100 / TOTAL))
    OTHER_PCT=$((OTHER_COUNT * 100 / TOTAL))
    UNCATEGORIZED_PCT=$(((TOTAL - SCRIPT_COUNT - OTHER_COUNT) * 100 / TOTAL))
    echo "  - Scripts/Logic: $SCRIPT_PCT% ($SCRIPT_COUNT commits)"
    echo "  - CI/CD/Config/Docs: $OTHER_PCT% ($OTHER_COUNT commits)"
    echo "  - Uncategorized: $UNCATEGORIZED_PCT% ($((TOTAL - SCRIPT_COUNT - OTHER_COUNT)) commits)"
fi
echo ""

# Show uncategorized commits if any
UNCATEGORIZED_COMMITS=$(echo "$COMMITS_JSON" | jq -r '.[] | 
  select(
    (.commit.message | test("script|[.]sh|[.]lua|[.]js|src/|bin/|lib/|captive|monitor|detection|interception|handler|chain|dns|http|proxy|firewall|iptables|nftables|procd|uci"; "i") | not) and
    (.commit.message | test("workflow|github|action|ci|cd|makefile|config|readme|doc|build|test|lint|format|license|changelog|bump|release|version"; "i") | not)
  ) |
  "\(.sha[0:7]) | \(.commit.message | split("\n")[0]) | Author: \(.commit.author.name) | Date: \(.commit.author.date[0:10])"')

if [ -n "$UNCATEGORIZED_COMMITS" ]; then
    echo "=== UNCATEGORIZED COMMITS ==="
    echo "These commits don't clearly fit either category:"
    echo ""
    echo "$UNCATEGORIZED_COMMITS"
    echo ""
fi

echo "✅ Analysis complete!"
