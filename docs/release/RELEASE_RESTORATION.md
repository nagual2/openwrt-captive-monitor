# Release Restoration Guide

This guide explains how to use the release restoration scripts to recover missing releases.

## Quick Start

```bash
# Restore all missing releases
bash scripts/restore-releases.sh

# Validate integrity
bash scripts/validate-releases.sh
```

## Available Scripts

### Main Scripts

| Script | Purpose | Requirements |
|--------|---------|--------------|
| `scripts/restore-releases.sh` | Main orchestration script | 5.1, 5.2, 5.3, 5.4 |
| `scripts/restore-semantic-releases.sh` | Restore semantic versions | 1.1, 1.2, 1.3, 1.4 |
| `scripts/restore-dated-releases.sh` | Restore dated versions | 2.1, 2.2, 2.3, 2.4 |
| `scripts/validate-releases.sh` | Validate release integrity | 5.1, 5.2, 5.3, 5.4 |

### Library Scripts

| Script | Purpose |
|--------|---------|
| `scripts/lib/changelog-parser.sh` | Parse CHANGELOG.md |
| `scripts/lib/commit-finder.sh` | Locate commits for versions |
| `scripts/lib/changelog-generator.sh` | Generate changelogs from git log |
| `scripts/lib/colors.sh` | Color output utilities |

## Semantic Release Restoration

### What It Does

Restores historical semantic releases (v0.1.0, v0.1.1, v0.1.2, v1.0.1, v1.0.3) from CHANGELOG.md.

### Usage

```bash
bash scripts/restore-semantic-releases.sh
```

### Process

1. **Parse CHANGELOG.md** - Extract version information
2. **Find Commits** - Locate commits using multiple strategies:
   - Search commit messages
   - Search by date from CHANGELOG
   - Search VERSION file changes
3. **Create Tags** - Create git tags for each version
4. **Create Releases** - Generate GitHub releases with:
   - Original changelog from CHANGELOG.md
   - Historical marker: "Historical Release - Restored from CHANGELOG"

### Output

```
[INFO] Starting semantic release restoration...
[INFO] Parsing CHANGELOG.md...
[SUCCESS] Found 5 semantic versions
[INFO] Restoring v0.1.0...
[SUCCESS] ✅ v0.1.0 restored successfully
...
[SUCCESS] Restored 5 semantic releases
```

## Dated Release Restoration

### What It Does

Creates GitHub releases for all dated tags (vYYYY.M.D.N) that don't have releases.

### Usage

```bash
bash scripts/restore-dated-releases.sh
```

### Process

1. **Get Dated Tags** - Retrieve all tags matching vYYYY.M.D.N format
2. **Check Existing Releases** - Identify tags without releases
3. **Generate Changelogs** - Create changelogs from git commit history
4. **Create Releases** - Generate releases with:
   - Title format: "vYYYY.M.D.N - YYYY-MM-DD"
   - Changelog from git log
   - Restored marker

### Output

```
[INFO] Starting dated release restoration...
[INFO] Fetching dated tags...
[INFO] Found 17 dated tags
[INFO] Checking existing releases...
[INFO] Found 0 tags without releases
[SUCCESS] All dated releases already exist
```

## Full Restoration

### What It Does

Runs both semantic and dated release restoration in sequence.

### Usage

```bash
bash scripts/restore-releases.sh
```

### Process

1. **Phase 1** - Restore semantic releases
2. **Phase 2** - Restore dated releases
3. **Summary** - Report total restored releases

### Output

```
═══════════════════════════════════════════════════════════
              Release Restoration Summary
═══════════════════════════════════════════════════════════

Phase 1: Semantic Releases
  Restored: 5/5

Phase 2: Dated Releases
  Restored: 0/17 (all already exist)

Total Restored: 5 releases

✅ Release restoration completed successfully
═══════════════════════════════════════════════════════════
```

## Validation

### What It Does

Validates that all expected releases exist on GitHub.

### Usage

```bash
bash scripts/validate-releases.sh
```

### Checks

1. **Semantic Releases** - Verifies all 5 semantic versions exist
2. **Dated Releases** - Verifies all dated tags have releases
3. **Report** - Generates comprehensive integrity report

### Output

```
═══════════════════════════════════════════════════════════
              Release Integrity Report
═══════════════════════════════════════════════════════════

Release Statistics:
  Semantic releases: 5
  Dated releases: 17
  Total releases: 23

Validation Results:
  Semantic releases: ✅ PASS
  Dated releases: ✅ PASS

✅ All releases present - Integrity check PASSED
═══════════════════════════════════════════════════════════
```

## Prerequisites

### Required Tools

- **Git** - Version control
- **GitHub CLI (gh)** - For creating releases
  - Install: https://cli.github.com/
  - Authenticate: `gh auth login`

### Required Permissions

- Read access to repository
- Write access to create tags and releases
- GitHub token with `repo` and `workflow` scopes

### Verification

```bash
# Check git
git --version

# Check GitHub CLI
gh --version

# Check authentication
gh auth status
```

## Troubleshooting

### GitHub CLI Not Authenticated

**Error:**
```
[ERROR] GitHub CLI is not authenticated
```

**Solution:**
```bash
gh auth login
```

### Commit Not Found for Version

**Error:**
```
[ERROR] Could not find commit for v0.1.0
```

**Solution:**
The script tries multiple strategies. If all fail, you may need to manually specify the commit SHA by editing the script or providing it interactively.

### Rate Limit Exceeded

**Error:**
```
API rate limit exceeded
```

**Solution:**
Wait for the rate limit to reset (usually 1 hour) or use a GitHub token with higher limits.

### Tag Already Exists

**Warning:**
```
[WARNING] Tag v0.1.0 already exists, skipping tag creation
```

**Solution:**
This is normal. The script will skip tag creation and proceed to create the release.

## Advanced Usage

### Dry Run

To see what would be restored without making changes:

```bash
# Edit the script and add echo before gh commands
# Or review the logs carefully before running
```

### Restore Specific Version

To restore only a specific semantic version:

```bash
# Edit restore-semantic-releases.sh
# Comment out versions you don't want to restore
```

### Custom Changelog

To use a custom changelog for a release:

```bash
# Create the release manually with gh CLI
gh release create v0.1.0 \
  --title "v0.1.0 - Historical Release" \
  --notes "Custom changelog text here"
```

## Idempotency

All scripts are idempotent - they can be run multiple times safely:

- **Tags:** If a tag exists, it's skipped
- **Releases:** If a release exists, it's skipped
- **No Duplicates:** Running multiple times won't create duplicates

## Best Practices

1. **Backup First** - Create a backup before running restoration
2. **Validate After** - Always run validation after restoration
3. **Review Logs** - Check logs for any warnings or errors
4. **Test Locally** - Test on a fork before running on production
5. **Document Changes** - Keep a record of what was restored

## Integration with CI/CD

### Periodic Validation

Add to `.github/workflows/validate-releases.yml`:

```yaml
name: Validate Releases

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
  workflow_dispatch:

jobs:
  validate:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0
      
      - name: Validate releases
        run: bash scripts/validate-releases.sh
```

### Automatic Restoration

For automatic restoration on detection of missing releases:

```yaml
- name: Restore missing releases
  if: failure()  # Run if validation fails
  run: bash scripts/restore-releases.sh
```

## See Also

- [RELEASE_PROCESS.md](./RELEASE_PROCESS.md) - Main release process documentation
- [RELEASE_RESTORATION_REPORT.md](../../RELEASE_RESTORATION_REPORT.md) - Detailed restoration report
- [CHANGELOG.md](./CHANGELOG.md) - Project changelog

---

**Last Updated:** November 2025
