# GitHub Actions Failure Diagnostics

## Overview

This directory contains diagnostic tools and reports for analyzing GitHub Actions workflow failures in the openwrt-captive-monitor project.

**Current Status:** 50% failure rate in build workflows  
**Primary Issue:** Feed update failures in build pipeline  
**Ready for Implementation:** Yes ✅

## Problem Summary

### Critical Failure
The "Update feeds" step in build workflows is failing ~50% of the time, blocking:
- Main branch builds
- All feature branch builds
- Release automation
- Package validation

### Impact
- 50 failed runs out of 100 recent attempts
- Affects all workflow types and branches
- Complete build pipeline instability
- Production release blocked

## Diagnostic Files

### 1. **DIAGNOSTIC_SUMMARY.md** (Start here)
Executive summary of the issue with:
- Key findings and statistics
- Root causes ranked by severity
- Immediate action items
- Implementation roadmap

**Read this first for quick understanding of the problem.**

### 2. **DIAGNOSTIC_REPORT.md** (Detailed analysis)
Comprehensive technical report including:
- Failure patterns and execution flow
- Current retry logic review
- Root cause analysis (4 issues identified)
- Recommended fixes (Priority 1-3)
- Acceptance criteria validation

**Read this for detailed technical information.**

### 3. **ACTIONS_DIAGNOSTIC_DATA.json** (Machine-readable)
Complete diagnostic data in JSON format:
- Failure statistics and trends
- Detailed failure records
- Structured recommendations
- Implementation priorities

**Use this for programmatic analysis or integration.**

## Diagnostic Scripts

### 1. **diagnose-actions.sh** (One-time diagnostic)
Standalone script that fetches and analyzes GitHub Actions failures.

```bash
# Run immediate diagnosis
./diagnose-actions.sh

# Output includes:
# - Latest 15 workflow runs
# - Latest failed run details
# - Job steps and failures
# - Failure statistics
```

**Requires:** curl, jq, and optional GITHUB_TOKEN environment variable  
**Output:** Printed to console

### 2. **scripts/diagnose-github-actions.sh** (Reusable tool)
Command-line diagnostic tool with customizable parameters.

```bash
# Default (current repo, 7 days, 15 runs)
./scripts/diagnose-github-actions.sh

# Custom repository and time period
./scripts/diagnose-github-actions.sh "owner/repo" 30 50

# Parameters:
#   REPO - GitHub repository (default: nagual2/openwrt-captive-monitor)
#   DAYS - Time period in days (default: 7)
#   LIMIT - Number of runs to analyze (default: 15)

# Features:
# - Color-coded output (✓✗⊘)
# - Run history with timestamps
# - Failed job and step analysis
# - Common failure pattern detection
# - Smart recommendations based on failure rate
```

**Requires:** curl, jq, and optional GITHUB_TOKEN environment variable  
**Output:** Formatted console output with color coding

## Root Causes Identified

### 1. Network Dependency on External Feed Mirrors (Severity: Critical)
- OpenWrt feed update process fails intermittently
- No fallback mechanisms for mirror outages
- No resilience to transient connectivity issues

### 2. Inadequate Retry Logic (Severity: Critical)
- Current: 5 attempts, max 31 seconds total
- Wait times too short: 1s, 2s, 4s, 8s, 16s
- No jitter (causes thundering herd problem)
- No intermediate cache clearing

### 3. Missing Network Diagnostics (Severity: High)
- Failures don't log the actual error reason
- No distinction between timeout, DNS, rate limit, or 404
- Makes debugging extremely difficult

### 4. Cache Management Issues (Severity: High)
- Feed cache persists across retries
- Corrupted cache not cleared
- State files not refreshed between attempts

## Recommended Fixes

### Priority 1: Immediate Fixes (Critical)
1. **Enhance retry logic** (effort: low, impact: high)
   - Increase attempts: 5 → 10
   - Longer wait times: max 300+ seconds
   - Add exponential backoff with jitter

2. **Add network diagnostics** (effort: medium, impact: high)
   - Log DNS resolution tests
   - Test mirror connectivity
   - Capture curl/wget verbose output
   - Distinguish failure types

3. **Aggressive cache clearing** (effort: low, impact: medium)
   - Clear `feeds/` between retries
   - Run `git clean -fdx`
   - Remove `feeds.conf.old`

4. **Configure timeouts** (effort: low, impact: medium)
   - Add curl `--max-time 60`
   - Add wget `--timeout 60`
   - Set git timeout to 300 seconds

### Priority 2: Resilience Improvements
1. Implement feed mirror fallback (use alternative mirrors if primary fails)
2. Add GitHub Actions workflow-level retry
3. Enhanced error logging and debugging output

### Priority 3: Long-term Optimization
1. Pre-built feeds cache
2. Feed mirror health monitoring
3. Evaluate GitHub Packages registry usage

## Workflow Failure Timeline

```
✅ Checkout code
✅ Setup dependencies  
✅ Download OpenWrt SDK from GitHub CDN
✅ Extract OpenWrt SDK
✅ Setup SDK environment
✅ Clean SDK environment
✅ Copy package to SDK
❌ Update feeds <-- FAILURE POINT (50% of builds fail here)
⏭️  Build package with SDK (skipped if feeds fail)
⏭️  Validate built package (skipped if feeds fail)
⏭️  Upload artifacts (skipped if feeds fail)
```

## Affected Workflows

1. **.github/workflows/build.yml** (Lines 353-424)
   - "Update feeds" step fails
   - Blocks entire SDK build pipeline

2. **.github/workflows/build-openwrt-package.yml** (Lines 122-191)
   - "Update and install feeds" step fails
   - Alternative build method also affected

3. **.github/workflows/ci.yml**
   - Linting and testing pass (100% success)
   - Build step fails downstream

## Statistics

- **Total runs (7 days):** 100
- **Succeeded:** 47 (47%)
- **Failed:** 50 (50%)
- **Cancelled:** 3 (3%)
- **Primary failure point:** "Update feeds" step
- **Affected branches:** main, feature/*, fix/*

## Implementation Guide

### Step 1: Review Diagnostics
1. Read `DIAGNOSTIC_SUMMARY.md` for overview
2. Read `DIAGNOSTIC_REPORT.md` for technical details
3. Understand root causes and recommended fixes

### Step 2: Implement Fixes
1. Start with Priority 1 fixes (retry logic enhancement)
2. Add network diagnostics
3. Implement cache clearing strategy

### Step 3: Test and Validate
1. Create feature branch for fixes
2. Run multiple test iterations to validate improvements
3. Monitor success rate for stability

### Step 4: Deploy and Monitor
1. Merge fixes to main
2. Monitor failure rate improvement
3. Proceed with Priority 2-3 fixes as needed

## Running Future Diagnostics

After fixes are implemented, use the diagnostic tool to track improvements:

```bash
# Daily check
./scripts/diagnose-github-actions.sh

# Weekly comprehensive check
./scripts/diagnose-github-actions.sh "nagual2/openwrt-captive-monitor" 7 50

# Monthly trend analysis
./scripts/diagnose-github-actions.sh "nagual2/openwrt-captive-monitor" 30 100
```

## Environment Setup

### Requirements
- bash shell
- curl (for API calls)
- jq (for JSON parsing)

### Authentication (Optional)
```bash
export GITHUB_TOKEN="your-github-token-here"
./scripts/diagnose-github-actions.sh
```

Note: Without token, you have lower API rate limits (60 req/hr) but diagnostics will still work.

## Troubleshooting

### "jq: command not found"
Install jq: `sudo apt-get install jq` (Ubuntu/Debian)

### "curl: command not found"
Install curl: `sudo apt-get install curl` (Ubuntu/Debian)

### "Cannot access GitHub API"
- Check internet connection
- Verify repository name is correct
- If rate limited, set GITHUB_TOKEN environment variable

### No failed runs found
- Repository may have recently fixed issues
- Try longer time period: `./scripts/diagnose-github-actions.sh "repo" 30 50`

## Support and Questions

For questions about these diagnostics:
1. Review the diagnostic reports for detailed explanations
2. Check workflow logs at https://github.com/nagual2/openwrt-captive-monitor/actions
3. Refer to recommended fixes in DIAGNOSTIC_REPORT.md

## File Manifest

- `DIAGNOSTIC_SUMMARY.md` - Executive summary (this is the starting point)
- `DIAGNOSTIC_REPORT.md` - Detailed technical analysis
- `ACTIONS_DIAGNOSTIC_DATA.json` - Machine-readable diagnostic data
- `diagnose-actions.sh` - One-time diagnostic script (in repo root)
- `scripts/diagnose-github-actions.sh` - Reusable diagnostic tool
- `GITHUB_ACTIONS_DIAGNOSTICS.md` - This file

## Related Documentation

- `.github/workflows/build.yml` - Build with SDK workflow
- `.github/workflows/build-openwrt-package.yml` - Build Package workflow
- `.github/workflows/ci.yml` - CI pipeline workflow

---

**Diagnosis Date:** 2025-11-12  
**Status:** ✅ Complete and ready for implementation  
**Next Action:** Review DIAGNOSTIC_SUMMARY.md and begin Priority 1 fixes
