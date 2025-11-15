# Windows-Incompatible Artifact Cleanup

This directory contains scripts and workflows for identifying and deleting GitHub artifacts with Windows-incompatible names.

## Problem

Windows has strict filename restrictions and the following characters are invalid or problematic in Windows filenames:

- **Punctuation:** `: * ? " < > | ; , . ! @ # $ % ^ & + = ~ ` ' \`
- **Brackets:** `( ) [ ] { }`

When GitHub artifacts contain these characters in their names, they can cause issues when:
- Downloading artifacts on Windows systems
- Automated scripts process artifact names
- Cross-platform compatibility is required

## Solution

### 1. Automated GitHub Workflow

**File:** `.github/workflows/delete-windows-incompatible-artifacts.yml`

A GitHub Actions workflow that can be manually triggered to clean up Windows-incompatible artifacts.

**Features:**
- **Dry-run mode by default** - Safe operation that shows what would be deleted
- **Manual confirmation required** - Must type "DELETE" to actually delete artifacts
- **Detailed logging** - Shows exactly which artifacts contain problematic characters
- **Character identification** - Highlights specific problematic characters in each artifact name

**Usage:**
1. Go to GitHub Actions → "Delete Windows-Incompatible Artifacts" → "Run workflow"
2. **Dry Run:** Leave `dry_run` as `true` to see what would be deleted
3. **Execute:** Set `dry_run` to `false` AND type `DELETE` in the confirmation field

### 2. Command Line Script

**File:** `scripts/delete-windows-incompatible-artifacts.sh`

A standalone script that can be run locally or in CI environments.

**Features:**
- Lists all artifacts in the repository
- Identifies artifacts with Windows-incompatible characters
- Shows problematic characters in each artifact name
- Supports dry-run mode for safety
- Provides detailed logging and summary

**Usage:**
```bash
# Dry run (safe)
./scripts/delete-windows-incompatible-artifacts.sh

# Execute with confirmation
DRY_RUN=false ./scripts/delete-windows-incompatible-artifacts.sh

# With custom repository
GITHUB_REPOSITORY=owner/repo ./scripts/delete-windows-incompatible-artifacts.sh
```

**Requirements:**
- GitHub CLI (`gh`) installed
- `GITHUB_TOKEN` environment variable with `repo` scope

### 3. Test Script

**File:** `scripts/test-windows-incompatible-detection.sh`

A comprehensive test suite that validates the character detection logic.

**Usage:**
```bash
./scripts/test-windows-incompatible-detection.sh
```

## Character Detection Logic

The solution uses a character-by-character analysis approach:

```bash
# Windows-incompatible characters
incompatible=':"*?<>|;,.!@#$%^&+=~`'"'"'\()[]{}'

# Check each character in the artifact name
for (( i=0; i<${#name}; i++ )); do
    local char="${name:$i:1}"
    if [[ "$incompatible" == *"$char"* ]]; then
        return 0  # Found incompatible character
    fi
done
```

This approach is:
- **Reliable:** Doesn't depend on complex regex patterns
- **Comprehensive:** Covers all Windows-incompatible characters
- **Clear:** Easy to understand and maintain

## Safety Features

1. **Dry-run Mode:** Default behavior shows what would be deleted without actually deleting
2. **Manual Confirmation:** Requires explicit confirmation for actual deletion
3. **Detailed Logging:** Shows exactly which artifacts and characters are problematic
4. **Error Handling:** Graceful handling of API errors and edge cases
5. **Comprehensive Testing:** Full test suite validates detection logic

## Current Artifact Naming Patterns

Based on repository workflow analysis:

| Workflow | Artifact Name | Windows Compatible |
|----------|---------------|-------------------|
| `ci.yml` | `test-results` | ❌ Contains `.` |
| `tag-build-release.yml` | `openwrt-package-build-*` | ✅ (sanitized) |
| `build-simple.yml` | `ipk-package` | ✅ |
| `security-scanning.yml` | No artifacts (uses SARIF upload) | N/A |

**Note:** The `test-results` artifact from `ci.yml` will be flagged as incompatible due to the dot (`.`) character, as specified in the requirements.

## Integration with Existing Cleanup

This solution complements the existing `.github/workflows/cleanup.yml` workflow:

- **Existing cleanup:** Removes old artifacts based on age (retention policy)
- **New cleanup:** Removes artifacts based on naming compatibility (Windows compatibility)

Both can be used together for comprehensive artifact management.

## Examples

### Artifact Names That Will Be Deleted:
- `artifact:name` (contains `:`)
- `test-results` (contains `.`)
- `build(v1.2.3)` (contains `(` and `)`)
- `package@latest` (contains `@`)
- `release#1` (contains `#`)

### Artifact Names That Will Be Kept:
- `test-results` (if `.` is excluded from incompatible list)
- `build-v1-2-3`
- `package_latest`
- `release-1`
- `openwrt-package-build-v1.2.3` (if `.` is excluded)

## Troubleshooting

### Common Issues:

1. **"gh: command not found"**
   - Install GitHub CLI: `curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null && sudo apt-get update && sudo apt-get install gh`

2. **"GITHUB_TOKEN not set"**
   - Set environment variable: `export GITHUB_TOKEN=your_token`
   - Token needs `repo` scope for artifact management

3. **Permission errors**
   - Ensure token has `repo` scope
   - For workflow, ensure `actions: write` permission is set

### Testing Locally:

```bash
# Test character detection
./scripts/test-windows-incompatible-detection.sh

# Test with dry run
./scripts/delete-windows-incompatible-artifacts.sh --dry-run
```

## Future Enhancements

- **Configurable character lists:** Allow customization of incompatible characters
- **Artifact name sanitization:** Automatically rename incompatible artifacts instead of deleting
- **Integration with artifact creation:** Prevent creation of incompatible artifacts
- **Reporting:** Generate reports of incompatible artifacts for analysis

## Support

For issues or questions:
1. Check the workflow run logs in GitHub Actions
2. Run the test script to validate detection logic
3. Verify GitHub CLI installation and token permissions
4. Review this documentation for common troubleshooting steps