# Security Scanning Documentation

This document provides comprehensive information about the security scanning infrastructure for the openwrt-captive-monitor project.

## Overview

The project uses a multi-layered security scanning approach to identify vulnerabilities, insecure code patterns, and dependency issues before they reach production. All scans are automated and integrated with GitHub's Security tab for centralized vulnerability management.

## Table of Contents

* [Security Scanning Tools](#security-scanning-tools)
* [Workflow Triggers](#workflow-triggers)
* [Scanner Details](#scanner-details)
* [Integration with CI/CD](#integration-with-cicd)
* [Viewing and Managing Results](#viewing-and-managing-results)
* [Remediation Guidelines](#remediation-guidelines)
* [False Positive Handling](#false-positive-handling)
* [Performance Considerations](#performance-considerations)
* [Troubleshooting](#troubleshooting)

## Security Scanning Tools

### Primary Scanners

#### 1. ShellCheck Security Analysis

**Purpose**: Security-focused static analysis for shell scripts

**Coverage**:

* Security issues in Bash/POSIX shell scripts
* Command injection vulnerabilities
* Unsafe variable expansions
* Path traversal risks

**Configuration**:

* Output format: SARIF (uploaded to GitHub Security)
* Target: All `.sh` files excluding `tests/` directory
* Severity: Warnings and errors only
* Paths excluded: `.git/*`, `tests/*`

**Run frequency**:

* On every pull request to `main`
* On every push to `main`
* Weekly on Tuesday at 00:00 UTC

**Expected duration**: 5-10 minutes

**Workflow file**: `.github/workflows/security-scanning.yml`

#### 2. Dependency Review

**Purpose**: Analyze dependency changes in pull requests

**Coverage**:

* Known vulnerabilities in dependencies
* License compliance (GPL-3.0, AGPL-3.0 denied)
* Dependency health scores

**Configuration**:

* Fail on severity: Moderate and above
* Comment summary in PRs: Always enabled
* Snapshot warnings: Retry enabled

**Run frequency**: On pull requests only

**Expected duration**: 2-5 minutes

**Workflow file**: `.github/workflows/security-scanning.yml`

#### 3. Trivy

**Purpose**: Comprehensive vulnerability and misconfiguration scanner

**Coverage**:

* Vulnerabilities in code and dependencies
* Secret detection (API keys, tokens, passwords)
* Configuration issues (IaC misconfigurations)

**Configuration**:

* Scan type: Filesystem
* Severity: CRITICAL, HIGH, MEDIUM
* Scanners: vuln, secret, misconfig
* Ignore unfixed: Yes (reduces noise)

**Run frequency**:

* On every pull request to `main`
* On every push to `main`
* Weekly on Tuesday at 00:00 UTC

**Expected duration**: 5-10 minutes

**Workflow file**: `.github/workflows/security-scanning.yml`

## Workflow Triggers

### Security Scanning Workflow (`security-scanning.yml`)

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 2'  # Weekly on Tuesday
  workflow_dispatch:       # Manual trigger
```

## Scanner Details

### ShellCheck Configuration

The ShellCheck scanner uses the following configuration:

```yaml
- name: Install ShellCheck and jq
  run: |
    sudo apt-get update
    sudo apt-get install -y shellcheck jq

- name: Run ShellCheck and convert to SARIF
  run: |
    # Find all shell scripts (excluding tests)
    SHELL_SCRIPTS=$(find . -type f -name "*.sh" -not -path "./.git/*" -not -path "./tests/*")
    
    # Run shellcheck and convert to SARIF
    shellcheck --format=json $SHELL_SCRIPTS > shellcheck-output.json || true
    
    # Convert JSON to SARIF format using jq
    jq -f convert-to-sarif.jq shellcheck-output.json > shellcheck-results/shellcheck.sarif
```

### ShellCheck SARIF Conversion

ShellCheck output is converted to SARIF format for GitHub Security integration:

```bash
# Convert JSON output to SARIF format using jq
jq -f convert-to-sarif.jq shellcheck-output.json > shellcheck-results/shellcheck.sarif
```

This allows ShellCheck findings to appear alongside other security alerts in the GitHub Security tab.

### Trivy Scan Configuration

```yaml
- uses: aquasecurity/trivy-action@0.28.0
  with:
    scan-type: 'fs'
    scan-ref: '.'
    format: 'sarif'
    severity: 'CRITICAL,HIGH,MEDIUM'
    exit-code: '0'           # Non-blocking
    ignore-unfixed: true     # Skip unfixable issues
    scanners: 'vuln,secret,misconfig'
```

**Why ignore unfixed vulnerabilities?**

Unfixed vulnerabilities in transitive dependencies can create noise. We focus on actionable items while monitoring for fixes upstream.

### Bandit Configuration

```bash
bandit -r . -f sarif -o bandit-results.sarif --exit-zero
```

The `--exit-zero` flag ensures the workflow doesn't fail, allowing other checks to complete and results to be uploaded.

## Integration with CI/CD

### Status Checks

The following status checks are available for branch protection:

| Check Name | Required for PRs | Blocking |
|------------|------------------|----------|
| ShellCheck Security Analysis | **Yes** | **Yes** |
| Dependency Review | **Yes** | **Yes** |
| Trivy Security Scan | Recommended | Optional |

**Note**: Dependency Review should be required as it directly impacts supply chain security.

### Permissions Model

Security workflows use minimal permissions following the principle of least privilege:

```yaml
# Default for workflow
permissions:
  contents: read

# Security jobs only
jobs:
  analyze:
    permissions:
      security-events: write  # For SARIF upload
      actions: read           # For GitHub API calls
      contents: read          # For checkout
```

### Concurrency Control

Both workflows use concurrency control to prevent resource waste:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

This cancels in-progress scans when new commits are pushed to the same branch.

## Viewing and Managing Results

### Accessing Security Alerts

1. Navigate to the **Security** tab in the GitHub repository
2. Click **Code scanning** in the left sidebar
3. View alerts categorized by:
   * Tool (ShellCheck, Trivy)
   * Severity (Critical, High, Medium, Low)
   * Status (Open, Dismissed, Fixed)
   * Branch

### Alert Details

Each alert provides:

* **Description**: What the vulnerability is
* **Location**: File, line number, and code snippet
* **Severity**: Impact level (Critical/High/Medium/Low)
* **CWE**: Common Weakness Enumeration ID
* **Recommendation**: How to fix the issue
* **Show more**: Detailed explanation and examples

### Filtering and Search

Use GitHub's filtering to focus on specific issues:

```text
is:open severity:high tool:ShellCheck
is:open branch:main
is:dismissed
```

## Remediation Guidelines

### Priority Matrix

| Severity | Response Time | Action Required |
|----------|---------------|-----------------|
| **Critical** | Immediate (same day) | Emergency fix + patch release |
| **High** | 2-3 days | Prioritize in current sprint |
| **Medium** | 1-2 weeks | Include in next release |
| **Low** | 30 days | Backlog + future release |

### Remediation Steps

1. **Assess Impact**
   * Does it affect production code?
   * Is there a known exploit?
   * What's the attack surface?

2. **Research Fix**
   * Check GitHub Security Advisory
   * Review scanner recommendations
   * Search for similar issues and solutions

3. **Implement Fix**
   * Create feature branch
   * Write fix with tests
   * Verify fix resolves alert

4. **Test Thoroughly**
   * Run full test suite
   * Verify no regressions
   * Check fix doesn't introduce new issues

5. **Deploy and Verify**
   * Merge to main
   * Verify alert closes automatically
   * Update documentation if needed

### Common Vulnerability Fixes

#### Command Injection (Shell Scripts)

**Bad**:

```bash
eval $user_input
```

**Good**:

```bash
# Validate and sanitize input
if [[ "$user_input" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    command "$user_input"
fi
```

#### Path Traversal

**Bad**:

```bash
cat "$user_path/config"
```

**Good**:

```bash
# Canonicalize and validate path
safe_path=$(realpath -m "$user_path")
if [[ "$safe_path" == "/safe/base/"* ]]; then
    cat "$safe_path/config"
fi
```

#### Hardcoded Secrets

**Bad**:

```python
API_KEY = "sk-1234567890abcdef"
```

**Good**:

```python
import os
API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable required")
```

## False Positive Handling

### Identifying False Positives

A finding is a false positive if:

* The code is safe due to external validation
* The pattern is required for functionality
* The vulnerability cannot be exploited in context
* The scanner misunderstood the code

### Documenting False Positives

Always document why something is a false positive:

```bash
# False positive: SC2086 (word splitting)
# Intentional word splitting for command arguments
# Arguments are from trusted config file, not user input
# shellcheck disable=SC2086
command $trusted_args
```

### Dismissing Alerts

In GitHub Security tab:

1. Click on the alert
2. Click "Dismiss alert"
3. Select reason:
   * **False positive**: Scanner error
   * **Won't fix**: Accepted risk
   * **Used in tests**: Test code only
4. Add comment explaining the decision
5. Click "Dismiss alert"

### Suppression Comments

| Tool | Suppression Syntax | Example |
|------|-------------------|---------|
| ShellCheck | `# shellcheck disable=SC####` | `# shellcheck disable=SC2086` |
| Trivy | `.trivyignore` file | `CVE-2021-12345` |

### Audit Trail

Maintain an audit trail for all suppressions:

* Comment in code explaining why
* GitHub Security tab comment
* Optional: Add to `.security-exceptions` file

## Performance Considerations

### Workflow Duration

Total time for all security scans:

* **Fast path** (PR with no issues): ~15-25 minutes
* **Full scan** (with findings): ~25-35 minutes
* **Weekly scheduled** (full analysis): ~30-40 minutes

### Optimization Tips

1. **Use caching**: Workflows cache dependencies and build artifacts
2. **Run in parallel**: Security jobs run concurrently
3. **Skip on docs changes**: Consider adding path filters
4. **Fast analysis**: ShellCheck provides rapid static analysis

### Resource Usage

Approximate GitHub Actions minutes consumed:

* Per PR: ~30-40 minutes (all jobs combined)
* Per push to main: ~30-40 minutes
* Weekly scans: ~70-80 minutes (both schedules)

**Monthly estimate**: ~400-600 minutes (assuming 10 PRs/month)

## Troubleshooting

### Common Issues

#### ShellCheck Analysis Fails

**Symptom**: ShellCheck job fails with "No shell scripts found"

**Solution**:

* Verify shell scripts exist in repository
* Check path exclusions aren't removing all files
* Ensure files have correct `.sh` extensions

#### ShellCheck SARIF Upload Fails

**Symptom**: "Invalid SARIF file" error

**Solution**:

* Check jq is installed
* Verify JSON output from shellcheck
* Validate SARIF schema

#### Dependency Review Blocks PR

**Symptom**: PR blocked due to vulnerable dependency

**Solution**:

* Update the vulnerable dependency
* If unfixable, add to allowed list (with justification)
* Check if dependency is truly required

#### Trivy Timeout

**Symptom**: Trivy scan exceeds timeout

**Solution**:

* Increase `timeout-minutes` in workflow
* Use `ignore-unfixed: true`
* Filter severity to CRITICAL, HIGH only

#### Bandit No Files Found

**Symptom**: "No Python files found to analyze"

**Solution**:

* This is expected if no Python files exist
* Empty SARIF file is generated
* No action required

### Getting Help

1. **Check workflow logs**: Detailed output in Actions tab
2. **GitHub Docs**: [Code scanning documentation](https://docs.github.com/en/code-security/code-scanning)
3. **Scanner docs**:
   * [ShellCheck](https://www.shellcheck.net/)
   * [Trivy](https://aquasecurity.github.io/trivy/)
4. **Open an issue**: File a bug report with workflow logs

## Best Practices

1. **Review alerts regularly**: Check Security tab weekly
2. **Fix high/critical issues immediately**: Don't let them accumulate
3. **Document all suppressions**: Future maintainers need context
4. **Keep scanners updated**: Use latest action versions
5. **Monitor false positive rate**: Adjust configuration if too noisy
6. **Educate team**: Share security findings and lessons learned
7. **Integrate with branch protection**: Require key security checks
8. **Test fixes thoroughly**: Security fixes can introduce regressions

## Future Enhancements

Planned improvements to security scanning:

* [ ] Add custom ShellCheck checks for OpenWrt-specific patterns
* [ ] Integrate SAST scanning for OpenWrt Makefile
* [ ] Add secret scanning with Git history analysis
* [ ] Implement automated dependency updates (Dependabot)
* [ ] Add container scanning for Docker images (if applicable)
* [ ] Create security scorecard integration
* [ ] Add SBOM (Software Bill of Materials) generation

---

## Related Documentation

* [SECURITY.md](../.github/SECURITY.md) - Security policy and vulnerability reporting
* [CONTRIBUTING.md](contributing/CONTRIBUTING.md) - Contribution guidelines
* [CI_WORKFLOW_SIMPLIFIED.md](CI_WORKFLOW_SIMPLIFIED.md) - CI/CD workflow overview
* [RELEASE_PROCESS.md](release/RELEASE_PROCESS.md) - Release and deployment process

---

Last updated: 2024-11-13
Maintained by: openwrt-captive-monitor security team
