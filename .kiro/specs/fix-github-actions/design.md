# Design Document

## Overview

This design addresses two critical failures in the GitHub Actions CI pipeline:
1. Shell script formatting checks failing inside OpenWrt SDK Docker containers
2. IPK package verification script incompatibility with modern tar.gz-based IPK format

The solution involves modifying the CI workflow to skip format checks and updating the verification script to handle both legacy (ar) and modern (tar.gz) IPK formats.

## Architecture

The system consists of three main components:
1. **GitHub Actions Workflow** - orchestrates the build process
2. **OpenWrt SDK Action** - builds packages in Docker containers
3. **Package Verification Script** - validates built IPK packages

```
┌─────────────────────────────────────────┐
│     GitHub Actions Workflow (ci.yml)    │
│  - Prepares feed directory              │
│  - Sets environment variables           │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   OpenWrt SDK Action (Docker)           │
│  - Builds package in container          │
│  - Runs format checks (problematic)     │
│  - Produces IPK files                   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Package Verification (verify_package.sh)│
│  - Detects IPK format (ar vs tar.gz)    │
│  - Extracts and validates contents      │
└─────────────────────────────────────────┘
```

## Components and Interfaces

### 1. GitHub Actions Workflow (ci.yml)

**Purpose:** Orchestrate the build and verification process

**Key Changes:**
- Add `IGNORE_ERRORS: 1` environment variable to SDK action
- Maintain existing `NO_CHECK_FORMAT: 1` variable
- Keep git initialization in feed directory (for local context)

**Interface:**
```yaml
env:
  ARCH: <sdk-slug>-<version>
  PACKAGES: openwrt-captive-monitor
  FEEDNAME: local
  ARTIFACTS_DIR: <path>
  FEED_DIR: <path>
  NO_CHECK_FORMAT: 1
  IGNORE_ERRORS: 1
```

### 2. Package Verification Script (verify_package.sh)

**Purpose:** Validate IPK package structure and contents

**Key Functions:**

```bash
# Detect and extract IPK package
extract_ipk() {
  # Try tar.gz extraction first (modern format)
  if tar -xzf "$package_path" -C "$work_dir" 2>/dev/null; then
    return 0
  fi
  # Fall back to ar extraction (legacy format)
  ar x "$package_path"
}

# Validate package contents
validate_ipk_contents() {
  # Check for data.tar.gz and control.tar.gz
  # Verify file permissions
  # Display metadata
}
```

**Input:** Path to IPK file
**Output:** Validation report or error message
**Exit Codes:**
- 0: Success
- 1: Validation failure

## Data Models

### IPK Package Structure (Modern tar.gz format)

```
package.ipk (tar.gz archive)
├── data.tar.gz       # Package files
│   ├── ./usr/sbin/openwrt_captive_monitor
│   ├── ./etc/init.d/captive-monitor
│   └── ...
├── control.tar.gz    # Package metadata
│   ├── ./control     # Package info
│   ├── ./postinst    # Post-install script
│   ├── ./prerm       # Pre-remove script
│   └── ./postrm      # Post-remove script
└── debian-binary     # Format version
```

### IPK Package Structure (Legacy ar format)

```
package.ipk (ar archive)
├── debian-binary
├── data.tar.gz
└── control.tar.gz
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Build completion with format check bypass

*For any* package build with IGNORE_ERRORS=1 set, the build SHALL complete successfully regardless of format check results
**Validates: Requirements 1.1, 1.2, 1.4**

### Property 2: IPK format detection

*For any* valid IPK file, the verification script SHALL correctly identify whether it uses tar.gz or ar format
**Validates: Requirements 2.1**

### Property 3: Extraction method selection

*For any* IPK file identified as tar.gz format, extraction SHALL use tar command; for ar format, extraction SHALL use ar command
**Validates: Requirements 2.2, 2.3**

### Property 4: Validation completeness

*For any* successfully extracted IPK, the verification SHALL check for both data.tar.gz and control.tar.gz archives
**Validates: Requirements 2.4**

### Property 5: Error message clarity

*For any* failed validation, the error message SHALL include the specific validation step that failed
**Validates: Requirements 3.1, 3.2, 3.3**

## Error Handling

### Build Errors

1. **Format Check Failure**
   - **Detection:** Exit code 128 from git command inside SDK container
   - **Handling:** IGNORE_ERRORS=1 allows build to continue
   - **Logging:** Warning logged but build proceeds

2. **Package Build Failure**
   - **Detection:** Non-zero exit from make command
   - **Handling:** Workflow fails with error
   - **Logging:** Full build log preserved in artifacts

### Verification Errors

1. **Unknown IPK Format**
   - **Detection:** Both tar and ar extraction fail
   - **Handling:** Script exits with code 1
   - **Message:** "error: unable to extract IPK package"

2. **Missing Required Archives**
   - **Detection:** data.tar.gz or control.tar.gz not found
   - **Handling:** Script exits with code 1
   - **Message:** "error: expected <archive> inside package"

3. **Corrupted Archive**
   - **Detection:** tar/ar command fails
   - **Handling:** Script exits with code 1
   - **Message:** "error: unable to list <archive> contents"

## Testing Strategy

### Unit Testing

Unit tests will cover:
- IPK format detection logic
- Extraction method selection
- Error message generation
- File type identification

### Property-Based Testing

Property-based tests will use **shellspec** or **bats** framework with random input generation:

1. **Format Detection Property**
   - Generate random IPK files (both formats)
   - Verify correct format detection
   - Minimum 100 iterations

2. **Extraction Consistency Property**
   - Generate random valid IPK packages
   - Verify extraction produces expected files
   - Minimum 100 iterations

3. **Error Handling Property**
   - Generate random invalid/corrupted IPK files
   - Verify appropriate error messages
   - Minimum 100 iterations

### Integration Testing

- Test full CI workflow with sample packages
- Verify build artifacts are created
- Validate package contents match expectations

### Test Execution

Tests will run:
- On every pull request
- On push to main branch
- Before releases

Test results will be uploaded as GitHub Actions artifacts for debugging.
