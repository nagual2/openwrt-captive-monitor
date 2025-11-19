# CI SDK Validation Implementation

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---

This document describes the implementation of SDK validation in the CI/CD pipelines to fail fast when SDK images or URLs are invalid, reducing wasted CI minutes.

## Overview

The repository now includes comprehensive SDK validation for both Docker-based SDK builds and SDK tarball downloads. This validation ensures that:

1. **Docker SDK images** exist in the registry before attempting to use them
2. **SDK tarball URLs** are accessible before attempting downloads
3. **Version formats** are correct and follow expected patterns
4. **Target/architecture combinations** are valid

## Implementation Details

### 1. Docker SDK Image Validation

**Script**: `scripts/validate-sdk-image.sh`

**Usage**:
```bash
./scripts/validate-sdk-image.sh <container_image> <sdk_target> <openwrt_version> <sdk_slug>
```

**Example**:
```bash
./scripts/validate-sdk-image.sh ghcr.io/openwrt/sdk:x86_64-23.05.3 x86/64 23.05.3 x86_64
```

**Validations performed**:
- OpenWrt version format (X.Y or X.Y.Z)
- SDK target format (target/subtarget)
- SDK slug format (alphanumeric, hyphens, underscores)
- Container image tag format matching
- Docker image availability in registry with 3 retry attempts

**CI Integration**: Used in `.github/workflows/ci.yml` before the SDK build step

### 2. SDK Tarball URL Validation

**Script**: `scripts/validate-sdk-url.sh`

**Usage**:
```bash
./scripts/validate-sdk-url.sh <sdk_version> [target] [arch]
```

**Example**:
```bash
./scripts/validate-sdk-url.sh 23.05.2 x86/64 x86-64
```

**Validations performed**:
- OpenWrt version format (X.Y or X.Y.Z)
- Target format (target/subtarget)
- Architecture format (alphanumeric and hyphens)
- URL accessibility across multiple mirrors with timeout

**Mirrors checked**:
1. GitHub repository mirror (for faster CI access)
2. Official OpenWrt downloads
3. Alternative OpenWrt mirrors

**CI Integration**: Used in `.github/workflows/tag-build-release.yml` and `.github/workflows/upload-sdk-to-release.yml`

## Workflow Changes

### CI Workflow (`.github/workflows/ci.yml`)

**Before**:
- Used incorrect container tag format: `ghcr.io/openwrt/sdk:openwrt-23.05.3-x86-64`
- No validation of SDK image availability

**After**:
- Fixed container tag format: `ghcr.io/openwrt/sdk:x86_64-23.05.3`
- Added early validation step: "Validate SDK image and target"
- Fails fast with clear error messages if SDK image doesn't exist

### Tag Build Release Workflow (`.github/workflows/tag-build-release.yml`)

**Before**:
- No validation of SDK URLs before download
- Placeholder checksum value
- Could waste time downloading non-existent SDKs

**After**:
- Added "Validate SDK download URLs" step before download
- Updated to real checksum for OpenWrt 23.05.2
- Validates URL accessibility across multiple mirrors

### Upload SDK Workflow (`.github/workflows/upload-sdk-to-release.yml`)

**Before**:
- No validation of user-provided SDK version
- Could attempt to upload non-existent SDK versions

**After**:
- Added SDK version format validation
- Added URL accessibility check before download
- Clear error messages for invalid versions

## Error Handling

All validation scripts provide clear, actionable error messages:

### Docker Image Validation Errors
```
Error: Docker image not found in registry: ghcr.io/openwrt/sdk:x86_64-99.99.99

This usually means:
1. The OpenWrt version (99.99.99) doesn't exist
2. The target/subtarget combination (x86/64 / x86_64) is not supported
3. Network connectivity issue (even after 3 attempts)

Please verify:
- The OpenWrt version is correct
- The target/subtarget combination is valid
- Network connectivity is working
```

### SDK URL Validation Errors
```
Error: No accessible SDK mirrors found for version 99.99.99

This usually means:
1. The OpenWrt version (99.99.99) doesn't exist
2. The target/architecture combination (x86/64 / x86-64) is not supported
3. Network connectivity issues

Please verify:
- The OpenWrt version is correct
- The target/architecture combination is valid
- Network connectivity is working
```

## Benefits

1. **Reduced CI Waste**: Fail fast instead of wasting minutes on invalid configurations
2. **Clear Error Messages**: Developers get immediate feedback on what's wrong
3. **Improved Reliability**: Validation ensures SDK resources exist before use
4. **Better Developer Experience**: Clear guidance on how to fix configuration issues
5. **Network Resilience**: Multiple mirrors and retry attempts handle transient issues

## Testing

The validation scripts have been tested with:

- **Valid configurations**: Should pass validation
- **Invalid versions**: Should fail with clear error messages
- **Invalid formats**: Should fail with format-specific error messages
- **Network issues**: Should retry appropriate number of times

## Future Enhancements

Potential improvements for the future:

1. **Automatic version discovery**: Could query available versions from OpenWrt APIs
2. **Architecture validation**: Could validate supported architectures per version
3. **Performance optimization**: Cache validation results where appropriate
4. **Integration tests**: Add automated tests for validation scripts

## Maintenance

When updating OpenWrt versions or targets:

1. Test the new version with validation scripts first
2. Update any hardcoded checksums if using SDK tarballs
3. Verify that the new version follows the expected tag format
4. Update documentation if tag formats change

The validation scripts are designed to be maintainable and provide clear feedback when configurations need to be updated.