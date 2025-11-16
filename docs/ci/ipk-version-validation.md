# IPK Version Validation

## Overview

The CI pipeline includes automated validation of `.ipk` package version metadata to ensure correct version suffix handling based on the build context (main branch vs. pull requests).

## Validation Rules

### Main Branch Builds

Packages built from the `main` branch **must** include a `-dev` suffix in their Version field:

- **Pattern**: `^[0-9][0-9\.]*-dev(-[0-9]{8}([0-9]{2})?)?$`
- **Examples**:
  - `1.0.8-dev`
  - `1.0.8-dev-20240101`
  - `1.0.8-dev-2024010112`

### Pull Request Builds

Packages built from pull requests **must NOT** include a `-dev` suffix:

- **Pattern**: `^[0-9][0-9\.]*(-[0-9]{8}([0-9]{2})?)?$`
- **Examples**:
  - `1.0.8`
  - `1.0.8-20240101`
  - `1.0.8-2024010112`

### PKG_RELEASE Validation

The validation also checks for date-based release suffixes:

- **Format**: `YYYYMMDD` or `YYYYMMDDHHMM`
- **Example**: `20240101` or `202401011530`

## Implementation

### Script Location

The validation is implemented in `scripts/validate-ipk-version.sh`.

### How It Works

1. Extracts the `.ipk` archive (which is an `ar` archive)
2. Extracts the `control.tar.gz` from the package
3. Reads the `control` file metadata
4. Validates the `Version` field against branch-specific regex patterns
5. Optionally validates the PKG_RELEASE date format
6. Exits with code 0 on success, 1 on failure

### CI Integration

The validation runs in two CI jobs:

1. **build-dev-package** (main branch only):
   - Validates packages include `-dev` suffix
   - Step: "Validate IPK version metadata"

2. **build-pr-package** (pull requests only):
   - Validates packages do NOT include `-dev` suffix
   - Step: "Validate IPK version metadata"

## Usage

### Manual Validation

You can manually validate an `.ipk` file:

```bash
# For main branch packages (should have -dev)
./scripts/validate-ipk-version.sh package.ipk main

# For PR packages (should NOT have -dev)
./scripts/validate-ipk-version.sh package.ipk pr
```

### CI Validation

The validation runs automatically in CI after building packages. It checks all `.ipk` files in the artifacts directory.

## Troubleshooting

### Validation Failures

If validation fails, check:

1. **Main branch**: Ensure `DEV_SUFFIX=1` is set during the SDK build
2. **Pull requests**: Ensure `DEV_SUFFIX=0` or unset during the SDK build
3. **Makefile**: Verify the package Makefile properly appends `-dev` when `DEV_SUFFIX=1`

### Expected Error Messages

**Main branch without -dev**:

```
✗ Validation FAILED: Version does not match main branch pattern
  Expected: version with '-dev' suffix (e.g., 1.0.8-dev or 1.0.8-dev-20240101)
  Got: 1.0.8-20240101
```

**PR with -dev**:

```
✗ Validation FAILED: Version incorrectly includes '-dev' suffix for PR/non-main branch
  Expected: version without '-dev' suffix (e.g., 1.0.8 or 1.0.8-20240101)
  Got: 1.0.8-dev-20240101
```

## Related Files

- `scripts/validate-ipk-version.sh` - Validation script
- `.github/workflows/ci.yml` - CI workflow with validation steps
- `package/openwrt-captive-monitor/Makefile` - Package Makefile with DEV_SUFFIX logic
- `scripts/lib/colors.sh` - Color output library

## Design Rationale

The `-dev` suffix serves to distinguish development builds from stable releases:

- **Development builds** (main branch) are continuous and may contain breaking changes
- **PR builds** represent candidate changes that could potentially be merged
- **Release builds** (tags) are stable and versioned releases

This validation ensures that packages are correctly labeled based on their build context, preventing confusion between development and stable versions.
