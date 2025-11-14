# Workflow Diagnostics Tools

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---


This document describes the tools available for diagnosing GitHub Actions workflow failures.

## Tools Available

### 1. `scripts/parse-latest-failed-workflows.sh`

**Purpose**: Analyzes the two most recent failed GitHub Actions workflows to identify root causes and extract error details.

**Features**:
- Fetches the two latest failed workflow runs
- Displays detailed run information (status, branch, timestamps)
- Lists all failed jobs and their failed steps
- Downloads workflow logs and extracts them
- Identifies and highlights error messages from logs
- Provides color-coded output for easy reading

**Usage**:
```bash
export GITHUB_TOKEN="your_github_token"
./scripts/parse-latest-failed-workflows.sh [REPO]
```

**Examples**:
```bash
# Use default repository (nagual2/openwrt-captive-monitor)
./scripts/parse-latest-failed-workflows.sh

# Use custom repository
./scripts/parse-latest-failed-workflows.sh "owner/repo-name"
```

**Requirements**:
- `GITHUB_TOKEN` environment variable must be set
- GitHub token needs `actions:read` permission on the repository
- `curl`, `jq`, `unzip`, and standard Unix tools must be available

**Output**:
- Run details with timestamps
- List of failed jobs and steps
- Downloaded logs extracted and analyzed
- Error lines highlighted with context
- Summary of all log files found

### 2. `scripts/diagnose-github-actions.sh`

**Purpose**: Provides comprehensive diagnostics including overview of recent runs, failure statistics, and common patterns.

**Features**:
- Shows recent workflow runs (successful, failed, cancelled)
- Calculates failure and success rates
- Identifies common failure patterns across multiple runs
- Provides recommendations based on failure analysis

**Usage**:
```bash
export GITHUB_TOKEN="your_github_token"
./scripts/diagnose-github-actions.sh [REPO] [DAYS] [LIMIT]
```

**Examples**:
```bash
# Use defaults (last 7 days, 15 runs)
./scripts/diagnose-github-actions.sh

# Custom parameters
./scripts/diagnose-github-actions.sh "nagual2/openwrt-captive-monitor" 30 50
```

**Output**:
- List of recent workflow runs with status
- Failure statistics and success rates
- Common failure patterns
- Recommendations for fixes

## Setting Up GitHub Token

### Creating a Personal Access Token (PAT)

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select scopes:
   - `repo` (full repository access)
   - `actions` (read workflow runs)
4. Copy the token and store it securely

### Setting the Token

```bash
# Set for current session only
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# For persistent use (add to ~/.bashrc or ~/.zshrc)
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

## Workflow Failure Analysis

When workflows fail, the tools will help identify:

### Common Failure Points

1. **Feed Update Failures** - External feed mirrors timing out or becoming unavailable
   - Look for errors like "failed to update feeds" or network timeouts
   - Check error logs for feed URL issues

2. **Build Failures** - SDK build environment issues
   - Check for missing dependencies or SDK configuration problems
   - Look for compiler errors or linker issues

3. **External Dependencies** - Network or service issues
   - CDN download failures
   - GitHub API rate limiting
   - DNS resolution issues

### Analyzing Error Output

The scripts will extract and display:
- **Fatal errors** (shown in red) - workflow-stopping issues
- **Errors** (shown in yellow) - significant problems
- **Warnings** - potential issues to investigate

## Troubleshooting

### "GITHUB_TOKEN environment variable not set"
Set your GitHub token:
```bash
export GITHUB_TOKEN="your_token_here"
```

### "No failed runs found"
The repository may have no recent failures or your token may not have sufficient permissions. Check:
- Token has `actions:read` permission
- Recent workflows have actually failed (check GitHub UI)

### "Could not download logs"
This may indicate:
- Network connectivity issues
- Token authentication failed
- GitHub API rate limit exceeded
- Run ID is invalid

## Common Patterns in Failures

Based on historical analysis, the following patterns have been identified:

1. **Feed Update Retries** - Current retry logic (5 attempts, 31 seconds max) insufficient
   - Recommendation: Increase to 10 attempts with exponential backoff (300+ seconds total)
   - Add jitter to prevent thundering herd effect

2. **Cache Issues** - Stale feed cache causing update failures
   - Recommendation: Clear `feeds/` directory and `feeds.conf.old` before retries

3. **Network Timeouts** - SDK downloads and package feeds timing out
   - Recommendation: Increase curl/wget timeout limits to 60 seconds

## Integration with CI Workflows

The diagnostic tools are designed to support the following CI workflows:
- `.github/workflows/build.yml` - Main build pipeline
- `.github/workflows/build-openwrt-package.yml` - Package-specific builds
- `.github/workflows/ci.yml` - General CI pipeline

## See Also

- `DIAGNOSTICS_INDEX.md` - Navigation hub for all diagnostic information
- `DIAGNOSTIC_SUMMARY.md` - Executive summary of identified issues
- `DIAGNOSTIC_REPORT.md` - Technical analysis of failure patterns
- `GITHUB_ACTIONS_DIAGNOSTICS.md` - Detailed tool usage guide
