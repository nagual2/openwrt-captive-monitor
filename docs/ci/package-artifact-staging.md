# Package Artifact Staging for CI

## Overview

In non-release CI workflows (main branch and pull requests), built `.ipk` package files are staged into a workspace `package/` directory and uploaded as GitHub Actions artifacts. This provides a consistent location and standardized artifact layout across all builds.

## Feature

### What Happens

1. OpenWrt SDK builds produce `.ipk` files in `artifacts/{BUILD_NAME}/` directory
2. The staging script copies `.ipk` files to a clean `package/` directory
3. SHA256SUMS checksum file is generated
4. The `package/` directory is uploaded as a CI artifact with proper naming

### Naming Convention

Artifacts are named with channel and short SHA identifiers:

- **Dev builds (main branch)**: `captive-monitor-{sdk_target}-dev+{short_sha}`
  - Example: `captive-monitor-x86-64-dev+a1b2c3d4`
  - Includes `-dev` suffix in .ipk control Version field

- **PR builds**: `captive-monitor-{sdk_target}-pr+{short_sha}`
  - Example: `captive-monitor-x86-64-pr+a1b2c3d4`
  - Does NOT include `-dev` suffix in .ipk control Version field

### Artifact Contents

Each uploaded artifact contains:

```
package/
├── openwrt-captive-monitor_*.ipk    # Built package(s)
└── SHA256SUMS                        # Checksums for verification
```

## Implementation

### Staging Script

The `scripts/stage-package-artifacts.sh` script handles the staging:

```bash
./scripts/stage-package-artifacts.sh <artifacts_dir>
```

**Functionality:**
- Creates clean `package/` directory (removes any existing files)
- Copies all `.ipk` files from artifacts directory
- Generates SHA256SUMS checksum file
- Uses color output for clear logging
- Validates that at least one `.ipk` file was found

**Environment Variables:**
- `WORKSPACE_PACKAGE_DIR`: Override default package directory (default: `package/`)

### CI Integration

Both build jobs integrate the staging step:

**build-dev-package job (main branch):**
```yaml
- name: Stage package artifacts with SHA256SUMS
  run: |
    ./scripts/stage-package-artifacts.sh "artifacts/${BUILD_NAME}"

- name: Upload dev artifacts
  uses: actions/upload-artifact@v5
  with:
    name: captive-monitor-${{ matrix.sdk_target }}-dev+${{ env.SHORT_SHA }}
    path: package
    retention-days: 7
```

**build-pr-package job (pull requests):**
```yaml
- name: Stage package artifacts with SHA256SUMS
  run: |
    ./scripts/stage-package-artifacts.sh "artifacts/${BUILD_NAME}"

- name: Upload PR artifacts
  uses: actions/upload-artifact@v5
  with:
    name: captive-monitor-${{ matrix.sdk_target }}-pr+${{ env.SHORT_SHA }}
    path: package
```

## Version Validation

The `.ipk` Version field is validated separately via `scripts/validate-ipk-version.sh`:

- **Main branch**: Must include `-dev` suffix
  - Pattern: `^[0-9][0-9\.]*-dev(-[0-9]{8}([0-9]{2})?)?$`
  - Example: `1.0.0-dev` or `1.0.0-dev-20240101`

- **PR builds**: Must NOT include `-dev` suffix
  - Pattern: `^[0-9][0-9\.]*(-[0-9]{8}([0-9]{2})?)?$`
  - Example: `1.0.0` or `1.0.0-20240101`

This separation ensures:
- Main branch builds are clearly marked as development versions
- PR builds can be directly released without additional changes
- Version validation occurs before staging

## Git Ignore

The `.ipk` files are already git-ignored globally:

```gitignore
*.ipk
*.ipk.gz
```

This ensures:
- Built packages are never committed to the repository
- Staging happens only in CI workspace (temporary)
- No repository size bloat from build artifacts

## Artifact Retention

- **Retention**: 7 days (default GitHub Actions retention)
- **Location**: GitHub Actions Artifacts section of workflow run
- **Download**: Available through GitHub UI or API

## Usage

### Accessing Artifacts Locally

```bash
# List available artifacts for a workflow run
gh run view {run_id} --json artifacts

# Download specific artifact
gh run download {run_id} --name "captive-monitor-x86-64-dev+abc12345"

# Extract and verify
unzip -d ~/Downloads/artifacts
sha256sum -c ~/Downloads/artifacts/SHA256SUMS
```

### Integration in Workflows

Users can:
1. Download artifacts from workflow runs
2. Verify checksums with provided SHA256SUMS
3. Deploy or test on target systems
4. No need to rebuild for each test iteration

## Troubleshooting

### No .ipk files staged

**Symptom**: Upload fails with "no files found"

**Causes:**
- SDK build failed (check previous steps)
- Wrong artifacts directory path
- File permission issues

**Solution:**
1. Check "List and validate produced artifacts" step output
2. Verify SDK build succeeded
3. Check build logs for compilation errors

### Missing SHA256SUMS

**Symptom**: Artifact missing SHA256SUMS file

**Causes:**
- Staging script failed
- sha256sum command not available

**Solution:**
1. Check staging script output
2. Verify sha256sum is available (Ubuntu 24.04 includes it)
3. Check filesystem space

### Incorrect artifact name

**Symptom**: Artifact has wrong name or missing short SHA

**Causes:**
- Environment variable not set
- Git commit history not available

**Solution:**
1. Verify SHORT_SHA environment variable is set
2. Ensure `fetch-depth: 0` in checkout step
3. Check "Set dev channel environment" or "Set PR build environment" step output

## See Also

- [IPK Version Validation](ipk-version-validation.md)
- [SDK Build Workflow Guide](../guides/sdk-build-workflow.md)
- [Simplified CI Workflow](../CI_WORKFLOW_SIMPLIFIED.md)
