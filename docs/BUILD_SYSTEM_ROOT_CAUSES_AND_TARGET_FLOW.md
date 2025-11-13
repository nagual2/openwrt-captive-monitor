# Build System Issues: Root Causes and Target Flow

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---


## Executive Summary

This document provides an authoritative analysis of the systemic build failures encountered in the openwrt-captive-monitor project, explains their root causes, references the official OpenWrt SDK documentation, and describes the target end-to-end build flow that subsequent refactoring work will implement.

## Table of Contents

- [Historical Build Failures](#historical-build-failures)
- [Root Cause Analysis](#root-cause-analysis)
- [OpenWrt SDK Official Documentation](#openwrt-sdk-official-documentation)
- [Target Build Flow](#target-build-flow)
- [Required Documentation Updates](#required-documentation-updates)
- [Implementation Roadmap](#implementation-roadmap)

## Historical Build Failures

### Symptom 1: Missing `ld-musl-*.so` Files

**Error Message:**
```
cp: cannot stat '/.../staging_dir/toolchain-x86_64_gcc-12.3.0_musl/lib/ld-musl-*.so*': 
No such file or directory
```

**Context:** This error occurred during OpenWrt SDK builds in CI/CD pipelines when attempting to compile packages or their dependencies.

### Symptom 2: Toolchain Installation Failures

**Error Pattern:**
```
make[1]: Entering directory '/.../openwrt-sdk-.../toolchain'
make[2]: *** No rule to make target 'install'
```

**Context:** Attempting to run `make toolchain/install` inside the SDK environment resulted in build system errors because the SDK is not designed to rebuild its bundled toolchain.

### Symptom 3: Inconsistent Package Artifacts

**Observation:** Manually crafted `.ipk` packages produced by custom archiving logic sometimes failed validation or behaved inconsistently across different OpenWrt versions and architectures.

## Root Cause Analysis

### Root Cause 1: Misuse of `make distclean` Inside SDK

#### What Happened

Early CI/CD workflows executed `make distclean` inside the OpenWrt SDK directory with the intention of ensuring a "clean" build environment:

```yaml
# INCORRECT WORKFLOW (legacy)
- name: Clean SDK environment
  run: |
    cd "$SDK_DIR"
    make distclean
```

#### Why This Was Wrong

The OpenWrt SDK is **not** the full OpenWrt buildroot. The `distclean` target in the SDK context:

1. **Removes prebuilt toolchain artifacts**: The SDK ships with a precompiled cross-compilation toolchain (GCC, binutils, musl libc) in `staging_dir/toolchain-*/`. Running `distclean` can remove or corrupt these files.

2. **Resets build system state inappropriately**: The SDK's build system is pre-configured for package compilation only. Resetting it with `distclean` can put the environment in an inconsistent state.

3. **Requires toolchain rebuild**: After `distclean`, the build system may expect a full toolchain rebuild, but the SDK lacks the sources and infrastructure to rebuild its toolchain from scratch.

#### Official OpenWrt SDK Documentation

From the [OpenWrt SDK Usage Guide](https://openwrt.org/docs/guide-developer/toolchain/using_the_sdk):

> The SDK is a pre-compiled toolchain intended for building packages. It includes everything you need to compile packages without building the entire OpenWrt system from source.

And from [OpenWrt Build System Essentials](https://openwrt.org/docs/guide-developer/toolchain/buildsystem_essentials):

> **Important**: The SDK environment is distinct from the full buildroot. Do not run `make clean`, `make distclean`, or other global cleanup targets that affect the toolchain. The SDK's toolchain is prebuilt and should not be modified.

### Root Cause 2: Unnecessary Toolchain Rebuilds

#### What Happened

In response to the `ld-musl-*.so` errors caused by `distclean`, workflows attempted to rebuild the toolchain:

```yaml
# INCORRECT WORKFLOW (legacy)
- name: Build toolchain
  run: |
    cd "$SDK_DIR"
    make toolchain/install V=s
```

#### Why This Was Wrong

1. **SDK toolchain is prebuilt**: The OpenWrt SDK includes a fully functional cross-compilation toolchain. There is no need—and no supported mechanism—to rebuild it.

2. **Masks the real problem**: Attempting to rebuild the toolchain addressed the symptom (missing `ld-musl` files) but not the root cause (inappropriate use of `distclean`).

3. **Adds 10-30 minutes to build time**: Toolchain compilation is time-consuming and entirely unnecessary in the SDK workflow.

4. **Unreliable**: The SDK may not include all sources needed for a complete toolchain rebuild, leading to intermittent failures.

#### Official OpenWrt SDK Documentation

From the [Using the SDK](https://openwrt.org/docs/guide-developer/toolchain/using_the_sdk#using_pre-compiled_packages) section:

> The SDK comes with a pre-built toolchain. You do not need to compile the toolchain yourself.

And from the [SDK FAQ](https://openwrt.org/docs/guide-developer/toolchain/using_the_sdk#faq):

> **Q: Do I need to run `make toolchain/install`?**  
> **A:** No. The SDK's toolchain is already installed and ready to use. This command is only relevant in the full buildroot environment.

### Root Cause 3: Hand-Crafted Packaging Bypassing Official Tooling

#### What Happened

The `scripts/build_ipk.sh` script initially used manual `ar` and `tar` commands to construct `.ipk` packages:

```bash
# LEGACY APPROACH (now fixed)
# Manually create control.tar.gz
tar -czf control.tar.gz -C control_dir ./control ./conffiles

# Manually create data.tar.gz
tar -czf data.tar.gz -C data_dir .

# Manually create .ipk with ar
echo "2.0" > debian-binary
ar rcs package.ipk debian-binary control.tar.gz data.tar.gz
```

#### Why This Was Problematic

1. **Bypassed official packaging tools**: OpenWrt provides `opkg-build` and `opkg-make-index` for a reason—they handle edge cases, version compatibility, and metadata consistency that manual scripting misses.

2. **Error-prone**: Manual archiving logic required careful handling of:
   - Directory structures and CONTROL/ subdirectories
   - File permissions and ownership
   - Compression formats and options
   - Checksum calculations
   - Index generation

3. **Difficult to maintain**: Custom packaging logic diverges from OpenWrt standards over time as the ecosystem evolves.

4. **Inconsistent with SDK output**: Packages built via the SDK use the official tools, creating potential inconsistencies between development builds and CI builds.

#### Official OpenWrt SDK Documentation

From [OpenWrt Package Build Guide](https://openwrt.org/docs/guide-developer/packages#package_build_process):

> Packages should be built using the official OpenWrt build system and tools. The `opkg-build` utility creates properly formatted `.ipk` files, and `opkg-make-index` generates feed indexes that are compatible with the `opkg` package manager.

And from the [OPKG Package Manager documentation](https://openwrt.org/docs/techref/opkg):

> OPKG packages follow a specific format. While the underlying structure is based on `ar` archives, the format includes version-specific metadata and conventions that should be handled by `opkg-build` rather than manual scripting.

### Root Cause 4: Confusion Between Build System Layers

The project has multiple build system entry points, which created confusion:

1. **Root Makefile** (`/Makefile`): A developer convenience tool for running linters, tests, and formatters. **Not** an OpenWrt package Makefile.

2. **Package Makefile** (`/package/openwrt-captive-monitor/Makefile`): The official OpenWrt package recipe that defines dependencies, install steps, and metadata.

3. **Standalone Build Script** (`/scripts/build_ipk.sh`): A script for building packages outside the SDK environment, useful for quick local development.

4. **CI/CD Workflows**: GitHub Actions workflows that orchestrate SDK-based builds in continuous integration.

#### The Confusion

- Developers sometimes expected the root Makefile to behave like an OpenWrt package build system.
- The standalone build script's custom packaging logic diverged from SDK behavior.
- CI workflows attempted to replicate SDK setup steps incorrectly due to misunderstanding the SDK's prebuilt nature.

## OpenWrt SDK Official Documentation

This section provides authoritative references to the official OpenWrt documentation that describes the **supported** SDK workflow.

### Primary References

#### 1. Using the SDK

**URL:** <https://openwrt.org/docs/guide-developer/toolchain/using_the_sdk>

**Key Points:**
- The SDK is a precompiled environment for building packages
- No need to compile the toolchain
- Workflow: download SDK → extract → copy package → update feeds → install feeds → configure → build

**Relevant Quote:**
> The SDK is a pre-compiled toolchain intended for building packages. It includes everything you need to compile packages without building the entire OpenWrt system from source.

#### 2. Build System Essentials

**URL:** <https://openwrt.org/docs/guide-developer/toolchain/buildsystem_essentials>

**Key Points:**
- Distinction between buildroot and SDK
- SDK limitations and intended use cases
- Build targets and their purposes

**Relevant Quote:**
> The SDK environment is distinct from the full buildroot. Do not run global cleanup targets that affect the toolchain. The SDK's toolchain is prebuilt and should not be modified.

#### 3. Package Build Guide

**URL:** <https://openwrt.org/docs/guide-developer/packages>

**Key Points:**
- Standard package Makefile structure
- Using feeds for dependencies
- Package installation and post-install scripts

**Relevant Quote:**
> Packages should be built using the official OpenWrt build system and tools.

#### 4. OPKG Package Manager

**URL:** <https://openwrt.org/docs/techref/opkg>

**Key Points:**
- IPK package format
- Use of `opkg-build` and `opkg-make-index`
- Package repository structure

**Relevant Quote:**
> OPKG packages follow a specific format. While the underlying structure is based on `ar` archives, the format includes version-specific metadata and conventions that should be handled by `opkg-build` rather than manual scripting.

### SDK Workflow Summary (from Official Docs)

According to the official documentation, the correct SDK workflow is:

```bash
# 1. Download SDK
wget https://downloads.openwrt.org/releases/${VERSION}/targets/${TARGET}/${SUBTARGET}/openwrt-sdk-*.tar.xz

# 2. Extract SDK
tar -xJf openwrt-sdk-*.tar.xz
cd openwrt-sdk-*

# 3. Copy package to SDK
cp -r /path/to/package package/my-package

# 4. Update feeds (fetch package sources)
./scripts/feeds update -a

# 5. Install feeds (make packages available)
./scripts/feeds install -a

# 6. Configure build system
make defconfig

# 7. Build package
make package/my-package/compile V=s

# 8. Collect artifacts
find bin/ -name "*.ipk"
```

**Notable Absences:**
- No `make distclean` step
- No `make toolchain/install` step
- No manual package construction with `ar` and `tar`

## Target Build Flow

This section describes the **target** end-to-end build flow that the refactoring will implement. This flow aligns with OpenWrt best practices and addresses all identified root causes.

### Build Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     OPENWRT SDK BUILD FLOW                  │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐
│ 1. SETUP SDK │  Download and cache OpenWrt SDK
└──────┬───────┘
       │
       v
┌──────────────┐
│ 2. PREPARE   │  Copy package files to SDK structure
│    PACKAGE   │  (Makefile, files/, LICENSE)
└──────┬───────┘
       │
       v
┌──────────────┐
│ 3. UPDATE    │  ./scripts/feeds update -a
│    FEEDS     │  (Fetch package sources from repositories)
└──────┬───────┘
       │
       v
┌──────────────┐
│ 4. INSTALL   │  ./scripts/feeds install -a
│    FEEDS     │  (Make packages available to build system)
└──────┬───────┘
       │
       v
┌──────────────┐
│ 5. CONFIGURE │  make defconfig
│    SDK       │  (Initialize build system configuration)
└──────┬───────┘
       │
       v
┌──────────────┐
│ 6. COMPILE   │  make package/openwrt-captive-monitor/compile V=s
│    PACKAGE   │  (Build package using SDK toolchain)
└──────┬───────┘
       │
       v
┌──────────────┐
│ 7. VALIDATE  │  ./scripts/validate_ipk.sh
│    PACKAGE   │  (Verify package structure and metadata)
└──────┬───────┘
       │
       v
┌──────────────┐
│ 8. COLLECT   │  Copy .ipk, Packages, Packages.gz from bin/
│    ARTIFACTS │  Upload to GitHub Actions or release
└──────────────┘
```

### Detailed Step-by-Step Flow

#### Step 1: Setup SDK

**Purpose:** Obtain the OpenWrt SDK with prebuilt toolchain.

**Actions:**
```bash
# Download SDK (with caching in CI)
SDK_VERSION="23.05.3"
SDK_ARCH="x86-64"
SDK_FILE="openwrt-sdk-${SDK_VERSION}-${SDK_ARCH}_gcc-12.3.0_musl.Linux-x86_64.tar.xz"
wget "https://downloads.openwrt.org/releases/${SDK_VERSION}/targets/x86/64/${SDK_FILE}"

# Verify checksum
echo "${SDK_CHECKSUM}  ${SDK_FILE}" | sha256sum -c

# Extract
tar -xf "$SDK_FILE"
cd openwrt-sdk-*
```

**Key Points:**
- Use official OpenWrt download servers
- Always verify checksums for security
- Cache SDK in CI to reduce download time
- **Never** run `make distclean` after extraction

#### Step 2: Prepare Package

**Purpose:** Copy package files into SDK's package directory structure.

**Actions:**
```bash
# Copy package recipe and files
mkdir -p package/openwrt-captive-monitor
cp -r /path/to/package/openwrt-captive-monitor/* package/openwrt-captive-monitor/

# Copy LICENSE and VERSION files
cp LICENSE package/openwrt-captive-monitor/files/
cp VERSION package/openwrt-captive-monitor/
```

**Key Points:**
- Maintain proper directory structure
- Include all metadata files (LICENSE, VERSION)
- Ensure Makefile uses proper OpenWrt conventions

#### Step 3: Update Feeds

**Purpose:** Fetch package sources from feed repositories (packages, luci, routing, telephony).

**Actions:**
```bash
./scripts/feeds update -a
```

**Key Points:**
- This downloads package definitions, not prebuilt binaries
- Required for dependency resolution
- May fail due to network issues; implement retry logic in CI
- Feeds are defined in `feeds.conf.default`

**Expected Output:**
```
Updating feed 'packages' from 'https://git.openwrt.org/feed/packages.git^...'
Updating feed 'luci' from 'https://git.openwrt.org/project/luci.git^...'
...
```

#### Step 4: Install Feeds

**Purpose:** Make feed packages available to the build system.

**Actions:**
```bash
./scripts/feeds install -a
```

**Key Points:**
- This creates symlinks in `package/feeds/` pointing to feed package definitions
- Required before building packages with feed dependencies
- Does not compile anything yet

**Expected Output:**
```
Installing all packages from feed packages
Installing all packages from feed luci
...
```

#### Step 5: Configure SDK

**Purpose:** Initialize build system configuration with default settings.

**Actions:**
```bash
make defconfig
```

**Key Points:**
- Generates `.config` file with default options
- Required before running build targets
- Uses sensible defaults for SDK environment
- **Do not** run `menuconfig` or modify `.config` manually unless necessary

**Expected Output:**
```
configuration written to .config
```

#### Step 6: Compile Package

**Purpose:** Build the package using the SDK's prebuilt toolchain.

**Actions:**
```bash
make package/openwrt-captive-monitor/compile V=s
```

**Key Points:**
- `V=s` enables verbose output for debugging
- Build system automatically handles dependencies
- Uses prebuilt toolchain in `staging_dir/toolchain-*/`
- Output goes to `bin/packages/${ARCH}/base/` or `bin/packages/${ARCH}/packages/`

**Expected Output:**
```
make[1]: Entering directory '.../openwrt-sdk-.../package/openwrt-captive-monitor'
...
make[1]: Leaving directory '.../openwrt-sdk-.../package/openwrt-captive-monitor'
```

**Artifacts Created:**
- `openwrt-captive-monitor_${VERSION}-${RELEASE}_all.ipk`
- `Packages` (feed index)
- `Packages.gz` (compressed feed index)

#### Step 7: Validate Package

**Purpose:** Verify package structure, metadata, and integrity.

**Actions:**
```bash
./scripts/validate_ipk.sh bin/packages/*/*/openwrt-captive-monitor_*.ipk
```

**Validation Checks:**
- IPK file is a valid `ar` archive
- Contains `debian-binary`, `control.tar.gz`, `data.tar.gz`
- `control` file has required fields (Package, Version, Architecture, etc.)
- File permissions are correct
- Dependencies are properly declared
- No security issues (e.g., setuid binaries without justification)

#### Step 8: Collect Artifacts

**Purpose:** Gather build outputs for distribution or release.

**Actions:**
```bash
# Create artifact directory
mkdir -p artifacts

# Copy IPK package
find bin/ -name "openwrt-captive-monitor_*.ipk" -exec cp {} artifacts/ \;

# Copy feed indexes
find bin/ -name "Packages*" -exec cp {} artifacts/ \;

# Copy build logs
cp build.log artifacts/ 2>/dev/null || true
```

**Artifact Structure:**
```
artifacts/
├── openwrt-captive-monitor_1.0.3-1_all.ipk
├── Packages
├── Packages.gz
└── build.log
```

### CI/CD Integration

The target build flow will be implemented in `.github/workflows/ci.yml` as follows:

```yaml
build-sdk:
  name: Build with OpenWrt SDK
  runs-on: ubuntu-latest
  needs: [lint, test]
  
  steps:
    - name: Check out repository
      uses: actions/checkout@v5

    - name: Cache OpenWrt SDK
      uses: actions/cache@v4
      with:
        path: openwrt-sdk-*
        key: ${{ runner.os }}-openwrt-sdk-${{ env.OPENWRT_VERSION }}-${{ env.OPENWRT_ARCH }}-v3

    - name: Download SDK
      if: steps.cache-sdk.outputs.cache-hit != 'true'
      run: |
        # Download and verify SDK
        # (with retry logic and fallback mirror)

    - name: Copy package to SDK
      run: |
        # Copy package files to SDK structure

    - name: Update feeds
      run: |
        cd openwrt-sdk-*
        ./scripts/feeds update -a

    - name: Install feeds
      run: |
        cd openwrt-sdk-*
        ./scripts/feeds install -a

    - name: Configure SDK
      run: |
        cd openwrt-sdk-*
        make defconfig

    - name: Build package
      run: |
        cd openwrt-sdk-*
        make package/openwrt-captive-monitor/compile V=s

    - name: Validate package
      run: |
        ./scripts/validate_ipk.sh openwrt-sdk-*/bin/packages/*/*/openwrt-captive-monitor_*.ipk

    - name: Collect artifacts
      run: |
        # Copy IPK, Packages, and logs to artifacts/

    - name: Upload artifacts
      uses: actions/upload-artifact@v5
      with:
        name: openwrt-captive-monitor-sdk-build
        path: artifacts/
```

### Standalone Build Script

The `scripts/build_ipk.sh` script will be **refactored** to use official tooling:

**Current Issues:**
- ✅ Already uses `opkg-build` and `opkg-make-index` (refactored)
- ✅ Provides CLI compatibility for local development
- ⚠️ Still differs from SDK-based builds in environment and configuration

**Target Improvements:**
- Document that `build_ipk.sh` is for **quick local development only**
- CI/CD should **always** use SDK-based builds
- Consider deprecating standalone builds in favor of SDK workflow for consistency

## Required Documentation Updates

The following documentation files will require updates to reflect the new build flow and remove references to problematic approaches:

### 1. `/README.md`

**Section:** Building from Source

**Updates Needed:**
- Remove or deprecate references to `scripts/build_ipk.sh` for production builds
- Add prominent section on SDK-based builds
- Update CI badge links if workflow names change
- Clarify distinction between development builds and CI builds

**Example Addition:**
```markdown
### Building with OpenWrt SDK (Recommended)

For production-quality packages that match CI output, use the OpenWrt SDK:

\`\`\`bash
# Download SDK
wget https://downloads.openwrt.org/releases/23.05.3/targets/x86/64/openwrt-sdk-*.tar.xz
tar -xf openwrt-sdk-*.tar.xz
cd openwrt-sdk-*

# Copy package
cp -r /path/to/openwrt-captive-monitor/package/openwrt-captive-monitor package/

# Build
./scripts/feeds update -a
./scripts/feeds install -a
make defconfig
make package/openwrt-captive-monitor/compile V=s

# Output: bin/packages/*/base/openwrt-captive-monitor_*.ipk
\`\`\`

See [SDK Build Workflow](docs/guides/sdk-build-workflow.md) for detailed instructions.
```

### 2. `/docs/packaging.md`

**Sections:** Local Development Builds, CI/CD Integration

**Updates Needed:**
- Demote `build_ipk.sh` to "Quick Development Builds" section with caveats
- Expand SDK workflow section with step-by-step instructions
- Remove references to `make toolchain/install` and `make distclean`
- Update workflow diagram to show correct step order

**Example Update:**
```markdown
## SDK-Based Builds (Production)

For builds that exactly match CI/CD output and OpenWrt standards:

### Prerequisites
- Ubuntu 20.04+ or Debian 11+
- ~5GB free disk space
- Build dependencies: `build-essential ccache curl git rsync wget`

### Workflow
[Insert steps from Target Build Flow section above]

## Quick Development Builds (Convenience Only)

The `scripts/build_ipk.sh` script provides a faster alternative for local testing,
but produces packages that may differ slightly from CI builds:

\`\`\`bash
./scripts/build_ipk.sh --arch all
\`\`\`

**Limitations:**
- No dependency resolution from feeds
- Uses local environment instead of SDK toolchain
- Not suitable for release artifacts

**When to Use:**
- Rapid iteration during development
- Testing package structure changes
- Local installation on test devices
```

### 3. `/docs/guides/sdk-build-workflow.md`

**Entire File**

**Updates Needed:**
- Expand with detailed step-by-step instructions from this document
- Add troubleshooting section for common SDK errors
- Include diagrams of build flow
- Add examples of feed configuration and dependency resolution
- Reference official OpenWrt SDK documentation

### 4. `/docs/project/CI_NOTES.md`

**Section:** 2025-XX-XX - CI Workflow Simplification

**Updates Needed:**
- Add note explaining why `distclean` and `toolchain/install` were removed
- Reference this document for historical context
- Update dates and version numbers

**Example Addition:**
```markdown
## 2025-XX-XX - SDK Workflow Alignment

- **Removed problematic steps**: Eliminated `make distclean` and `make toolchain/install` 
  from CI workflows, which were causing `ld-musl-*` errors and adding unnecessary build time.
- **Root cause documentation**: Created `docs/BUILD_SYSTEM_ROOT_CAUSES_AND_TARGET_FLOW.md` 
  explaining why these steps were problematic and documenting the correct OpenWrt SDK workflow.
- **Official tooling**: Ensured all package builds use `opkg-build` and `opkg-make-index` 
  rather than manual archive construction.
- **Documentation alignment**: Updated all build-related documentation to reflect official 
  OpenWrt SDK best practices with citations.
```

### 5. `/docs/CI_WORKFLOW_SIMPLIFIED.md`

**Sections:** Simplified Approach, SDK Build

**Updates Needed:**
- Strengthen explanation of why old approach was wrong (not just slower)
- Add references to official OpenWrt documentation
- Include links to this document for detailed analysis

### 6. `/TOOLCHAIN_INITIALIZATION_FIX.md`

**Entire File**

**Updates Needed:**
- Update "Historical Note" at top to reference this document
- Consider moving to `/docs/archive/` to preserve historical context without cluttering root
- Add prominent banner: "⚠️ OBSOLETE: This document describes a problem that stemmed from 
  incorrect SDK usage. See [BUILD_SYSTEM_ROOT_CAUSES_AND_TARGET_FLOW.md](docs/BUILD_SYSTEM_ROOT_CAUSES_AND_TARGET_FLOW.md) 
  for the correct approach."

### 7. `/INVESTIGATION_SUMMARY.md`

**Entire File**

**Updates Needed:**
- Similar treatment to TOOLCHAIN_INITIALIZATION_FIX.md
- Add note that the "solution" described (adding `make toolchain/install`) was treating 
  the symptom, not the root cause
- Reference this document for correct approach
- Consider moving to `/docs/archive/`

### 8. `/.github/workflows/ci.yml`

**No Updates Needed** (current workflow already follows correct SDK pattern)

**Validation Needed:**
- Verify no remnants of `distclean` or `toolchain/install`
- Ensure step order matches target flow
- Confirm artifact collection and upload logic

### 9. `/scripts/validate_ipk.sh`

**Potential Updates:**
- Ensure validation checks align with OPKG standards
- Add checks for common issues (e.g., missing dependencies, incorrect architecture)

### 10. `/package/openwrt-captive-monitor/Makefile`

**Updates Needed:**
- Verify all fields conform to OpenWrt package standards
- Ensure `PKG_LICENSE_FILES` correctly references LICENSE file
- Validate `conffiles` section for config preservation
- Review postinst/prerm/postrm scripts for proper escaping

## Implementation Roadmap

The following tickets should be created to implement the target build flow:

### Phase 1: Documentation and Cleanup

- **Ticket 1** (this ticket): ✅ Document root causes and target flow
- **Ticket 2**: Update all documentation per "Required Documentation Updates" section
- **Ticket 3**: Move obsolete docs (TOOLCHAIN_INITIALIZATION_FIX.md, INVESTIGATION_SUMMARY.md) 
  to `/docs/archive/` with clear deprecation notices

### Phase 2: Validation and Testing

- **Ticket 4**: Enhance `scripts/validate_ipk.sh` with additional checks
- **Ticket 5**: Create integration tests that verify SDK build output matches expectations
- **Ticket 6**: Add documentation tests (e.g., ensure all README code blocks are executable)

### Phase 3: Build Script Alignment

- **Ticket 7**: Decide on future of `scripts/build_ipk.sh`:
  - Option A: Keep for development convenience with strong disclaimers
  - Option B: Deprecate in favor of SDK workflow
  - Option C: Refactor to wrap SDK commands instead of reimplementing packaging
- **Ticket 8**: If keeping `build_ipk.sh`, add automated tests comparing its output to SDK output

### Phase 4: CI/CD Hardening

- **Ticket 9**: Add CI job that explicitly validates no `distclean` or `toolchain/install` 
  in SDK workflows (linting for anti-patterns)
- **Ticket 10**: Improve feed update retry logic and error handling
- **Ticket 11**: Add multi-architecture matrix builds (ARM, MIPS, etc.)

### Phase 5: Developer Experience

- **Ticket 12**: Create local development guide with SDK setup instructions
- **Ticket 13**: Add `make sdk-build` target to root Makefile that wraps SDK workflow
- **Ticket 14**: Create troubleshooting playbook for common SDK errors

## Conclusion

The systemic build failures in the openwrt-captive-monitor project stemmed from three main issues:

1. **Inappropriate use of `make distclean`** inside the OpenWrt SDK, which removed prebuilt 
   toolchain files that the SDK relies upon.

2. **Unnecessary attempts to rebuild the toolchain** with `make toolchain/install`, which 
   masked the real problem and added significant build time.

3. **Hand-crafted packaging logic** that bypassed official OpenWrt tooling (`opkg-build`, 
   `opkg-make-index`), leading to inconsistencies and maintenance burden.

These issues arose from a **misunderstanding of the OpenWrt SDK's purpose and workflow**. 
The SDK is a pre-compiled environment designed for building packages **without** building 
the full OpenWrt system from source. Its toolchain is prebuilt and ready to use.

The **target build flow** described in this document aligns with the official OpenWrt SDK 
workflow as documented at:

- <https://openwrt.org/docs/guide-developer/toolchain/using_the_sdk>
- <https://openwrt.org/docs/guide-developer/toolchain/buildsystem_essentials>
- <https://openwrt.org/docs/guide-developer/packages>

This flow eliminates problematic steps, uses official tooling, and follows OpenWrt best 
practices. The current `.github/workflows/ci.yml` already implements this flow correctly. 
Subsequent work will focus on documentation updates, validation enhancements, and developer 
experience improvements to ensure the correct patterns are well-understood and consistently 
followed.

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-30  
**Related Documents:**
- [SDK Build Workflow Guide](guides/sdk-build-workflow.md)
- [CI Workflow Simplified](CI_WORKFLOW_SIMPLIFIED.md)
- [Packaging and Distribution Guide](packaging.md)
- [CI Notes](project/CI_NOTES.md)
