# Build System Issues: Root Causes and Target Flow

## 🌐 Language / Язык

**English** | [Русский](README.ru.md)

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

### 5. `/docs/ci/CI_WORKFLOW_SIMPLIFIED.md`

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
- [CI Workflow Simplified](ci/CI_WORKFLOW_SIMPLIFIED.md)
- [Packaging and Distribution Guide](packaging.md)
- [CI Notes](project/CI_NOTES.md)

---

# Проблемы системы сборки: коренные причины и целевой поток

## 🌐 Language / Язык

[English](#english) | **Русский**

---

## Резюме

Этот документ предоставляет авторитетный анализ системных ошибок сборки, возникших в проекте openwrt-captive-monitor, объясняет их коренные причины, ссылается на официальную документацию OpenWrt SDK и описывает целевой комплексный поток сборки, который будет реализован в последующих работах по рефакторингу.

## Оглавление

- [Исторические ошибки сборки](#исторические-ошибки-сборки)
- [Анализ коренных причин](#анализ-коренных-причин)
- [Официальная документация OpenWrt SDK](#официальная-документация-openwrt-sdk)
- [Целевой поток сборки](#целевой-поток-сборки)
- [Требуемые обновления документации](#требуемые-обновления-документации)
- [Дорожная карта реализации](#дорожная-карта-реализации)

## Исторические ошибки сборки

### Симптом 1: Отсутствующие файлы `ld-musl-*.so`

**Сообщение об ошибке:**
```
cp: cannot stat '/.../staging_dir/toolchain-x86_64_gcc-12.3.0_musl/lib/ld-musl-*.so*': 
No such file or directory
```

**Контекст:** Эта ошибка возникала во время сборок OpenWrt SDK в конвейерах CI/CD при попытке компиляции пакетов или их зависимостей.

### Симптом 2: Ошибки установки toolchain

**Шаблон ошибки:**
```
make[1]: Entering directory '/.../openwrt-sdk-.../toolchain'
make[2]: *** No rule to make target 'install'
```

**Контекст:** Попытка запуска `make toolchain/install` внутри окружения SDK привела к ошибкам системы сборки, потому что SDK не предназначен для перестроения своего встроенного toolchain.

### Симптом 3: Несогласованные артефакты пакетов

**Наблюдение:** Вручную созданные пакеты `.ipk`, созданные пользовательской логикой архивирования, иногда не проходили валидацию или вели себя несогласованно на различных версиях OpenWrt и архитектурах.

## Анализ коренных причин

### Коренная причина 1: Неправильное использование `make distclean` внутри SDK

#### Что произошло

Ранние конвейеры CI/CD выполняли `make distclean` внутри каталога OpenWrt SDK с целью обеспечения "чистого" окружения сборки:

```yaml
# НЕПРАВИЛЬНЫЙ РАБОЧИЙ ПОТОК (устаревший)
- name: Clean SDK environment
  run: |
    cd "$SDK_DIR"
    make distclean
```

#### Почему это было неправильно

OpenWrt SDK **не является** полным buildroot OpenWrt. Целевой `distclean` в контексте SDK:

1. **Удаляет артефакты предкомпилированного toolchain**: SDK поставляется с предкомпилированным инструментом кросс-компиляции (GCC, binutils, musl libc) в `staging_dir/toolchain-*/`. Запуск `distclean` может удалить или повредить эти файлы.

2. **Неправильно сбрасывает состояние системы сборки**: Система сборки SDK предварительно настроена только для компиляции пакетов. Сброс её с помощью `distclean` может привести окружение в несогласованное состояние.

3. **Требует перестроения toolchain**: После `distclean` система сборки может ожидать полного перестроения toolchain, но SDK не имеет источников и инфраструктуры для перестроения своего toolchain с нуля.

#### Официальная документация OpenWrt SDK

Из [OpenWrt SDK Usage Guide](https://openwrt.org/docs/guide-developer/toolchain/using_the_sdk):

> The SDK is a pre-compiled toolchain intended for building packages. It includes everything you need to compile packages without building the entire OpenWrt system from source.

(SDK — это предкомпилированный toolchain, предназначенный для сборки пакетов. Он включает всё необходимое для компиляции пакетов без необходимости собирать всю систему OpenWrt с исходных кодов.)

А из [OpenWrt Build System Essentials](https://openwrt.org/docs/guide-developer/toolchain/buildsystem_essentials):

> **Important**: The SDK environment is distinct from the full buildroot. Do not run `make clean`, `make distclean`, or other global cleanup targets that affect the toolchain. The SDK's toolchain is prebuilt and should not be modified.

(Окружение SDK отличается от полного buildroot. Не запускайте `make clean`, `make distclean` или другие целевые объекты глобальной очистки, влияющие на toolchain. Toolchain SDK предварительно построен и не должен быть изменён.)

### Коренная причина 2: Ненужные перестроения toolchain

#### Что произошло

В ответ на ошибки `ld-musl-*.so`, вызванные `distclean`, рабочие потоки попытались перестроить toolchain:

```yaml
# НЕПРАВИЛЬНЫЙ РАБОЧИЙ ПОТОК (устаревший)
- name: Build toolchain
  run: |
    cd "$SDK_DIR"
    make toolchain/install V=s
```

#### Почему это было неправильно

1. **Toolchain SDK предкомпилирован**: OpenWrt SDK включает полностью функциональный инструмент кросс-компиляции. Нет необходимости — и нет поддерживаемого механизма — перестраивать его.

2. **Скрывает реальную проблему**: Попытка перестроения toolchain устраняла симптом (отсутствующие файлы `ld-musl`), но не коренную причину (неправильное использование `distclean`).

3. **Добавляет 10-30 минут к времени сборки**: Компиляция toolchain требует много времени и полностью ненужна в рабочем потоке SDK.

4. **Ненадёжно**: SDK может не включать все источники, необходимые для полного перестроения toolchain, что приводит к нерегулярным сбоям.

#### Официальная документация OpenWrt SDK

Из раздела [Using the SDK](https://openwrt.org/docs/guide-developer/toolchain/using_the_sdk#using_pre-compiled_packages):

> The SDK comes with a pre-built toolchain. You do not need to compile the toolchain yourself.

(SDK поставляется с предварительно построенным toolchain. Вам не нужно компилировать toolchain самостоятельно.)

А из [SDK FAQ](https://openwrt.org/docs/guide-developer/toolchain/using_the_sdk#faq):

> **Q: Do I need to run `make toolchain/install`?**  
> **A:** No. The SDK's toolchain is already installed and ready to use. This command is only relevant in the full buildroot environment.

(Нужно ли мне запускать `make toolchain/install`? Нет. Toolchain SDK уже установлен и готов к использованию. Эта команда актуальна только в полном окружении buildroot.)

### Коренная причина 3: Вручную созданное упаковывание, обходящее официальные инструменты

#### Что произошло

Скрипт `scripts/build_ipk.sh` первоначально использовал команды `ar` и `tar` для конструирования пакетов `.ipk`:

```bash
# УСТАРЕВШИЙ ПОДХОД (теперь исправлено)
# Вручную создать control.tar.gz
tar -czf control.tar.gz -C control_dir ./control ./conffiles

# Вручную создать data.tar.gz
tar -czf data.tar.gz -C data_dir .

# Вручную создать .ipk с ar
echo "2.0" > debian-binary
ar rcs package.ipk debian-binary control.tar.gz data.tar.gz
```

#### Почему это было проблематично

1. **Обошёл официальные инструменты упаковывания**: OpenWrt предоставляет `opkg-build` и `opkg-make-index` не просто так — они обрабатывают граничные случаи, совместимость версий и согласованность метаданных, которые пропускает пользовательский скрипт.

2. **Подвержено ошибкам**: Пользовательская логика архивирования требовала тщательной обработки:
   - Структур каталогов и подкаталогов CONTROL/
   - Разрешений и прав собственности на файлы
   - Форматов и параметров сжатия
   - Расчётов контрольных сумм
   - Генерации индексов

3. **Сложно поддерживать**: Пользовательская логика упаковывания расходится со стандартами OpenWrt по мере развития экосистемы.

4. **Несогласованно с выводом SDK**: Пакеты, созданные через SDK, используют официальные инструменты, создавая потенциальные несоответствия между разработками и CI сборками.

#### Официальная документация OpenWrt SDK

Из [OpenWrt Package Build Guide](https://openwrt.org/docs/guide-developer/packages#package_build_process):

> Packages should be built using the official OpenWrt build system and tools. The `opkg-build` utility creates properly formatted `.ipk` files, and `opkg-make-index` generates feed indexes that are compatible with the `opkg` package manager.

(Пакеты должны быть построены с использованием официальной системы сборки OpenWrt и инструментов. Утилита `opkg-build` создаёт правильно отформатированные файлы `.ipk`, а `opkg-make-index` генерирует индексы feeds, совместимые с менеджером пакетов `opkg`.)

А из документации [OPKG Package Manager](https://openwrt.org/docs/techref/opkg):

> OPKG packages follow a specific format. While the underlying structure is based on `ar` archives, the format includes version-specific metadata and conventions that should be handled by `opkg-build` rather than manual scripting.

(Пакеты OPKG следуют определённому формату. Хотя основная структура основана на `ar` архивах, формат включает специфичные для версии метаданные и соглашения, которые должны обрабатываться `opkg-build`, а не пользовательским скриптом.)

### Коренная причина 4: Путаница между слоями системы сборки

Проект имеет несколько точек входа системы сборки, которые создали путаницу:

1. **Root Makefile** (`/Makefile`): Инструмент удобства разработчика для запуска linters, тестов и форматтеров. **Не** OpenWrt package Makefile.

2. **Package Makefile** (`/package/openwrt-captive-monitor/Makefile`): Официальный рецепт пакета OpenWrt, который определяет зависимости, шаги установки и метаданные.

3. **Standalone Build Script** (`/scripts/build_ipk.sh`): Скрипт для сборки пакетов вне окружения SDK, полезен для быстрой локальной разработки.

4. **CI/CD Workflows**: Рабочие потоки GitHub Actions, которые организуют SDK сборки в непрерывной интеграции.

#### Путаница

- Разработчики иногда ожидали, что root Makefile будет работать как система сборки пакетов OpenWrt.
- Пользовательская логика упаковывания автономного скрипта сборки расходилась с поведением SDK.
- Рабочие потоки CI попытались неправильно повторить шаги установки SDK из-за неправильного понимания предкомпилированной природы SDK.

## Официальная документация OpenWrt SDK

Этот раздел предоставляет авторитетные ссылки на официальную документацию OpenWrt, которая описывает **поддерживаемый** рабочий поток SDK.

### Основные ссылки

#### 1. Использование SDK

**URL:** <https://openwrt.org/docs/guide-developer/toolchain/using_the_sdk>

**Ключевые моменты:**
- SDK — это предкомпилированное окружение для сборки пакетов
- Нет необходимости компилировать toolchain
- Рабочий поток: загрузить SDK → распаковать → скопировать пакет → обновить feeds → установить feeds → сконфигурировать → собрать

**Релевантная цитата:**
> The SDK is a pre-compiled toolchain intended for building packages. It includes everything you need to compile packages without building the entire OpenWrt system from source.

(SDK — это предкомпилированный toolchain для сборки пакетов. Он включает всё необходимое для компиляции пакетов без необходимости собирать всю систему OpenWrt с исходных кодов.)

#### 2. Build System Essentials

**URL:** <https://openwrt.org/docs/guide-developer/toolchain/buildsystem_essentials>

**Ключевые моменты:**
- Различие между buildroot и SDK
- Ограничения SDK и предусмотренные случаи использования
- Целевые объекты сборки и их назначение

**Релевантная цитата:**
> The SDK environment is distinct from the full buildroot. Do not run global cleanup targets that affect the toolchain. The SDK's toolchain is prebuilt and should not be modified.

(Окружение SDK отличается от полного buildroot. Не запускайте целевые объекты глобальной очистки, влияющие на toolchain. Toolchain SDK предварительно построен и не должен быть изменён.)

#### 3. Package Build Guide

**URL:** <https://openwrt.org/docs/guide-developer/packages>

**Ключевые моменты:**
- Стандартная структура package Makefile
- Использование feeds для зависимостей
- Установка пакетов и сценарии постинсталляции

**Релевантная цитата:**
> Packages should be built using the official OpenWrt build system and tools.

(Пакеты должны быть построены с использованием официальной системы сборки OpenWrt и инструментов.)

#### 4. OPKG Package Manager

**URL:** <https://openwrt.org/docs/techref/opkg>

**Ключевые моменты:**
- Формат пакета IPK
- Использование `opkg-build` и `opkg-make-index`
- Структура хранилища пакетов

**Релевантная цитата:**
> OPKG packages follow a specific format. While the underlying structure is based on `ar` archives, the format includes version-specific metadata and conventions that should be handled by `opkg-build` rather than manual scripting.

(Пакеты OPKG следуют определённому формату. Хотя основная структура основана на `ar` архивах, формат включает специфичные для версии метаданные и соглашения, которые должны обрабатываться `opkg-build`, а не пользовательским скриптом.)

### Краткое описание рабочего потока SDK (из официальной документации)

Согласно официальной документации, правильный рабочий поток SDK таков:

```bash
# 1. Загрузить SDK
wget https://downloads.openwrt.org/releases/${VERSION}/targets/${TARGET}/${SUBTARGET}/openwrt-sdk-*.tar.xz

# 2. Распаковать SDK
tar -xJf openwrt-sdk-*.tar.xz
cd openwrt-sdk-*

# 3. Скопировать пакет в SDK
cp -r /path/to/package package/my-package

# 4. Обновить feeds (загрузить источники пакетов)
./scripts/feeds update -a

# 5. Установить feeds (сделать пакеты доступными)
./scripts/feeds install -a

# 6. Сконфигурировать систему сборки
make defconfig

# 7. Собрать пакет
make package/my-package/compile V=s

# 8. Собрать артефакты
find bin/ -name "*.ipk"
```

**Примечательные отсутствия:**
- Нет шага `make distclean`
- Нет шага `make toolchain/install`
- Нет ручной конструкции пакета с `ar` и `tar`

## Целевой поток сборки

Этот раздел описывает **целевой** комплексный поток сборки, который будет реализован рефакторингом. Этот поток соответствует лучшим практикам OpenWrt и устраняет все выявленные коренные причины.

### Архитектура потока сборки

```
┌─────────────────────────────────────────────────────────────┐
│                   ПОТОК СБОРКИ OPENWRT SDK                  │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐
│ 1. НАСТРОИТЬ │  Загрузить и кэшировать OpenWrt SDK
│     SDK      │
└──────┬───────┘
       │
       v
┌──────────────┐
│ 2. ПОДГОТОВ. │  Скопировать файлы пакета в структуру SDK
│    ПАКЕТ     │  (Makefile, files/, LICENSE)
└──────┬───────┘
       │
       v
┌──────────────┐
│ 3. ОБНОВИТЬ  │  ./scripts/feeds update -a
│    FEEDS     │  (Загрузить источники пакетов из репозиториев)
└──────┬───────┘
       │
       v
┌──────────────┐
│ 4. УСТАНОВ.  │  ./scripts/feeds install -a
│    FEEDS     │  (Сделать пакеты доступными для системы сборки)
└──────┬───────┘
       │
       v
┌──────────────┐
│ 5. СКОНФИГУР │  make defconfig
│     SDK      │  (Инициализировать конфигурацию системы сборки)
└──────┬───────┘
       │
       v
┌──────────────┐
│ 6. СКОМПИЛ.  │  make package/openwrt-captive-monitor/compile V=s
│    ПАКЕТ     │  (Собрать пакет используя SDK toolchain)
└──────┬───────┘
       │
       v
┌──────────────┐
│ 7. ВАЛИДИРОВ │  ./scripts/validate_ipk.sh
│    ПАКЕТ     │  (Проверить структуру пакета и метаданные)
└──────┬───────┘
       │
       v
┌──────────────┐
│ 8. СОБРАТЬ   │  Скопировать .ipk, Packages, Packages.gz из bin/
│  АРТЕФАКТЫ   │  Загрузить на GitHub Actions или в релиз
└──────────────┘
```

### Подробный пошаговый поток

#### Шаг 1: Настроить SDK

**Назначение:** Получить OpenWrt SDK с предкомпилированным toolchain.

**Действия:**
```bash
# Загрузить SDK (с кэшированием в CI)
SDK_VERSION="23.05.3"
SDK_ARCH="x86-64"
SDK_FILE="openwrt-sdk-${SDK_VERSION}-${SDK_ARCH}_gcc-12.3.0_musl.Linux-x86_64.tar.xz"
wget "https://downloads.openwrt.org/releases/${SDK_VERSION}/targets/x86/64/${SDK_FILE}"

# Проверить контрольную сумму
echo "${SDK_CHECKSUM}  ${SDK_FILE}" | sha256sum -c

# Распаковать
tar -xf "$SDK_FILE"
cd openwrt-sdk-*
```

**Ключевые моменты:**
- Используйте официальные серверы загрузки OpenWrt
- Всегда проверяйте контрольные суммы в целях безопасности
- Кэшируйте SDK в CI для сокращения времени загрузки
- **Никогда** не запускайте `make distclean` после распаковки

#### Шаг 2: Подготовить пакет

**Назначение:** Скопировать файлы пакета в структуру каталога пакетов SDK.

**Действия:**
```bash
# Скопировать рецепт пакета и файлы
mkdir -p package/openwrt-captive-monitor
cp -r /path/to/package/openwrt-captive-monitor/* package/openwrt-captive-monitor/

# Скопировать файлы LICENSE и VERSION
cp LICENSE package/openwrt-captive-monitor/files/
cp VERSION package/openwrt-captive-monitor/
```

**Ключевые моменты:**
- Поддерживайте правильную структуру каталогов
- Включите все файлы метаданных (LICENSE, VERSION)
- Убедитесь, что Makefile использует правильные соглашения OpenWrt

#### Шаг 3: Обновить Feeds

**Назначение:** Загрузить источники пакетов из хранилищ feeds (packages, luci, routing, telephony).

**Действия:**
```bash
./scripts/feeds update -a
```

**Ключевые моменты:**
- Это загружает определения пакетов, не предкомпилированные бинарные файлы
- Требуется для разрешения зависимостей
- Может не сработать из-за сетевых проблем; реализуйте логику повтора в CI
- Feeds определены в `feeds.conf.default`

**Ожидаемый вывод:**
```
Updating feed 'packages' from 'https://git.openwrt.org/feed/packages.git^...'
Updating feed 'luci' from 'https://git.openwrt.org/project/luci.git^...'
...
```

#### Шаг 4: Установить Feeds

**Назначение:** Сделать пакеты feeds доступными для системы сборки.

**Действия:**
```bash
./scripts/feeds install -a
```

**Ключевые моменты:**
- Это создаёт символические ссылки в `package/feeds/`, указывающие на определения пакетов feeds
- Требуется перед сборкой пакетов с зависимостями feeds
- Ничего не компилирует на этом этапе

**Ожидаемый вывод:**
```
Installing all packages from feed packages
Installing all packages from feed luci
...
```

#### Шаг 5: Сконфигурировать SDK

**Назначение:** Инициализировать конфигурацию системы сборки с параметрами по умолчанию.

**Действия:**
```bash
make defconfig
```

**Ключевые моменты:**
- Генерирует файл `.config` с параметрами по умолчанию
- Требуется перед запуском целевых объектов сборки
- Использует разумные параметры по умолчанию для окружения SDK
- **Не** запускайте `menuconfig` и не изменяйте `.config` вручную, если не требуется

**Ожидаемый вывод:**
```
configuration written to .config
```

#### Шаг 6: Скомпилировать пакет

**Назначение:** Собрать пакет, используя предкомпилированный toolchain SDK.

**Действия:**
```bash
make package/openwrt-captive-monitor/compile V=s
```

**Ключевые моменты:**
- `V=s` включает подробный вывод для отладки
- Система сборки автоматически обрабатывает зависимости
- Использует предкомпилированный toolchain в `staging_dir/toolchain-*/`
- Вывод идёт в `bin/packages/${ARCH}/base/` или `bin/packages/${ARCH}/packages/`

**Ожидаемый вывод:**
```
make[1]: Entering directory '.../openwrt-sdk-.../package/openwrt-captive-monitor'
...
make[1]: Leaving directory '.../openwrt-sdk-.../package/openwrt-captive-monitor'
```

**Созданные артефакты:**
- `openwrt-captive-monitor_${VERSION}-${RELEASE}_all.ipk`
- `Packages` (индекс feed)
- `Packages.gz` (сжатый индекс feed)

#### Шаг 7: Валидировать пакет

**Назначение:** Проверить структуру пакета, метаданные и целостность.

**Действия:**
```bash
./scripts/validate_ipk.sh bin/packages/*/*/openwrt-captive-monitor_*.ipk
```

**Проверки валидации:**
- IPK файл является действительным `ar` архивом
- Содержит `debian-binary`, `control.tar.gz`, `data.tar.gz`
- Файл `control` содержит требуемые поля (Package, Version, Architecture, и т.д.)
- Разрешения на файлы правильные
- Зависимости правильно объявлены
- Нет проблем безопасности (например, setuid бинарные файлы без обоснования)

#### Шаг 8: Собрать артефакты

**Назначение:** Собрать выходные данные сборки для распределения или релиза.

**Действия:**
```bash
# Создать каталог артефактов
mkdir -p artifacts

# Скопировать IPK пакет
find bin/ -name "openwrt-captive-monitor_*.ipk" -exec cp {} artifacts/ \;

# Скопировать индексы feeds
find bin/ -name "Packages*" -exec cp {} artifacts/ \;

# Скопировать журналы сборки
cp build.log artifacts/ 2>/dev/null || true
```

**Структура артефактов:**
```
artifacts/
├── openwrt-captive-monitor_1.0.3-1_all.ipk
├── Packages
├── Packages.gz
└── build.log
```

### Интеграция CI/CD

Целевой поток сборки будет реализован в `.github/workflows/ci.yml` следующим образом:

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
        # Загрузить и проверить SDK
        # (с логикой повтора и резервным зеркалом)

    - name: Copy package to SDK
      run: |
        # Скопировать файлы пакета в структуру SDK

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
        # Скопировать IPK, Packages и журналы в artifacts/

    - name: Upload artifacts
      uses: actions/upload-artifact@v5
      with:
        name: openwrt-captive-monitor-sdk-build
        path: artifacts/
```

### Автономный скрипт сборки

Скрипт `scripts/build_ipk.sh` будет **рефакторирован** для использования официальных инструментов:

**Текущие проблемы:**
- ✅ Уже использует `opkg-build` и `opkg-make-index` (рефакторирован)
- ✅ Обеспечивает совместимость CLI для локальной разработки
- ⚠️ Всё ещё отличается от SDK сборок в окружении и конфигурации

**Целевые улучшения:**
- Задокументируйте, что `build_ipk.sh` предназначен **только для быстрой локальной разработки**
- CI/CD должен **всегда** использовать SDK сборки
- Рассмотрите возможность амортизации автономных сборок в пользу рабочего потока SDK для согласованности

## Требуемые обновления документации

Следующие файлы документации потребуют обновления для отражения нового потока сборки и удаления ссылок на проблемные подходы:

### 1. `/README.md`

**Раздел:** Building from Source

**Требуемые обновления:**
- Удалите или амортизируйте ссылки на `scripts/build_ipk.sh` для производственных сборок
- Добавьте видный раздел о SDK сборках
- Обновите ссылки значков CI, если названия рабочих потоков изменятся
- Уточните различие между разработками и CI сборками

**Примерное добавление:**
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

**Разделы:** Local Development Builds, CI/CD Integration

**Требуемые обновления:**
- Понизьте `build_ipk.sh` в раздел "Quick Development Builds" с оговорками
- Расширьте раздел рабочего потока SDK пошаговыми инструкциями
- Удалите ссылки на `make toolchain/install` и `make distclean`
- Обновите диаграмму рабочего потока, чтобы показать правильный порядок шагов

**Примерное обновление:**
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

**Весь файл**

**Требуемые обновления:**
- Расширьте детальными пошаговыми инструкциями из раздела Target Build Flow выше
- Добавьте раздел устранения неполадок для распространённых ошибок SDK
- Включите диаграммы потока сборки
- Добавьте примеры конфигурации feeds и разрешения зависимостей
- Ссылка на официальную документацию OpenWrt SDK

### 4. `/docs/project/CI_NOTES.md`

**Раздел:** 2025-XX-XX - CI Workflow Simplification

**Требуемые обновления:**
- Добавьте примечание, объясняющее, почему `distclean` и `toolchain/install` были удалены
- Ссылка на этот документ для исторического контекста
- Обновите даты и номера версий

**Примерное добавление:**
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

### 5. `/docs/ci/CI_WORKFLOW_SIMPLIFIED.md`

**Разделы:** Simplified Approach, SDK Build

**Требуемые обновления:**
- Укрепите объяснение того, почему старый подход был неправильным (не только медленнее)
- Добавьте ссылки на официальную документацию OpenWrt
- Включите ссылки на этот документ для подробного анализа

### 6. `/TOOLCHAIN_INITIALIZATION_FIX.md`

**Весь файл**

**Требуемые обновления:**
- Обновите "Historical Note" вверху для ссылки на этот документ
- Рассмотрите перемещение в `/docs/archive/` для сохранения исторического контекста без загромождения корня
- Добавьте видный баннер: "⚠️ OBSOLETE: This document describes a problem that stemmed from 
  incorrect SDK usage. See [BUILD_SYSTEM_ROOT_CAUSES_AND_TARGET_FLOW.md](docs/BUILD_SYSTEM_ROOT_CAUSES_AND_TARGET_FLOW.md) 
  for the correct approach."

### 7. `/INVESTIGATION_SUMMARY.md`

**Весь файл**

**Требуемые обновления:**
- Подобное лечение как для TOOLCHAIN_INITIALIZATION_FIX.md
- Добавьте примечание о том, что "решение", описанное (добавление `make toolchain/install`), лечило симптом, а не коренную причину
- Ссылка на этот документ для правильного подхода
- Рассмотрите перемещение в `/docs/archive/`

### 8. `/.github/workflows/ci.yml`

**Обновления не требуются** (текущий рабочий поток уже следует правильному паттерну SDK)

**Требуется валидация:**
- Проверьте отсутствие остатков `distclean` или `toolchain/install`
- Убедитесь, что порядок шагов соответствует целевому потоку
- Подтвердите логику сбора артефактов и загрузки

### 9. `/scripts/validate_ipk.sh`

**Потенциальные обновления:**
- Убедитесь, что проверки валидации соответствуют стандартам OPKG
- Добавьте проверки распространённых проблем (например, отсутствующие зависимости, неправильная архитектура)

### 10. `/package/openwrt-captive-monitor/Makefile`

**Требуемые обновления:**
- Проверьте, что все поля соответствуют стандартам пакетов OpenWrt
- Убедитесь, что `PKG_LICENSE_FILES` правильно ссылается на файл LICENSE
- Валидируйте раздел `conffiles` для сохранения конфига
- Проверьте сценарии postinst/prerm/postrm для правильного экранирования

## Дорожная карта реализации

Следующие задачи должны быть созданы для реализации целевого потока сборки:

### Фаза 1: Документация и очистка

- **Задача 1** (эта задача): ✅ Задокументировать коренные причины и целевой поток
- **Задача 2**: Обновить всю документацию согласно разделу "Требуемые обновления документации"
- **Задача 3**: Переместить устаревшие документы (TOOLCHAIN_INITIALIZATION_FIX.md, INVESTIGATION_SUMMARY.md) 
  в `/docs/archive/` с чёткими уведомлениями об амортизации

### Фаза 2: Валидация и тестирование

- **Задача 4**: Улучшить `scripts/validate_ipk.sh` с дополнительными проверками
- **Задача 5**: Создать интеграционные тесты, которые проверяют, что вывод SDK сборки соответствует ожиданиям
- **Задача 6**: Добавить тесты документации (например, убедитесь, что все блоки кода README исполняемы)

### Фаза 3: Выравнивание скрипта сборки

- **Задача 7**: Решить о будущем `scripts/build_ipk.sh`:
  - Вариант A: Сохранить для удобства разработки с сильными оговорками
  - Вариант B: Амортизировать в пользу рабочего потока SDK
  - Вариант C: Рефакторировать для обёртывания команд SDK вместо переимплементации упаковывания
- **Задача 8**: Если сохранять `build_ipk.sh`, добавить автоматические тесты, сравнивающие его вывод с выводом SDK

### Фаза 4: Укрепление CI/CD

- **Задача 9**: Добавить работу CI, которая явно валидирует отсутствие `distclean` или `toolchain/install` 
  в рабочих потоках SDK (linting для антипаттернов)
- **Задача 10**: Улучшить логику повтора обновления feeds и обработку ошибок
- **Задача 11**: Добавить матричные сборки для нескольких архитектур (ARM, MIPS, и т.д.)

### Фаза 5: Опыт разработчика

- **Задача 12**: Создать локальный руководство разработки с инструкциями по настройке SDK
- **Задача 13**: Добавить целевой объект `make sdk-build` в root Makefile, обёртывающий рабочий поток SDK
- **Задача 14**: Создать сборник устранения неполадок для распространённых ошибок SDK

## Заключение

Системные ошибки сборки в проекте openwrt-captive-monitor вытекали из трёх основных проблем:

1. **Неправильное использование `make distclean`** внутри OpenWrt SDK, которое удалило предкомпилированные 
   файлы toolchain, на которые полагается SDK.

2. **Ненужные попытки перестроить toolchain** с помощью `make toolchain/install`, которые 
   скрывали реальную проблему и добавляли значительное время сборки.

3. **Пользовательская логика упаковывания**, которая обошла официальные инструменты OpenWrt (`opkg-build`, 
   `opkg-make-index`), приводя к несоответствиям и бремени обслуживания.

Эти проблемы возникли из **неправильного понимания назначения и рабочего потока OpenWrt SDK**. 
SDK — это предкомпилированное окружение, предназначенное для сборки пакетов **без** необходимости собирать 
полную систему OpenWrt с исходных кодов. Его toolchain предкомпилирован и готов к использованию.

**Целевой поток сборки**, описанный в этом документе, соответствует официальному рабочему потоку OpenWrt SDK 
согласно документации:

- <https://openwrt.org/docs/guide-developer/toolchain/using_the_sdk>
- <https://openwrt.org/docs/guide-developer/toolchain/buildsystem_essentials>
- <https://openwrt.org/docs/guide-developer/packages>

Этот поток исключает проблемные шаги, использует официальные инструменты и следует лучшим практикам OpenWrt. 
Текущий файл `.github/workflows/ci.yml` уже правильно реализует этот поток. Последующая работа будет сосредоточена 
на обновлениях документации, улучшениях валидации и совершенствовании опыта разработчика для обеспечения того, 
чтобы правильные паттерны были хорошо поняты и последовательно соблюдались.

---

**Версия документа:** 1.0  
**Последнее обновление:** 2025-01-30  
**Связанные документы:**
- [Руководство рабочего потока сборки SDK](guides/sdk-build-workflow.md)
- [Упрощённый рабочий поток CI](ci/CI_WORKFLOW_SIMPLIFIED.md)
- [Руководство по упаковыванию и распределению](packaging.md)
- [Примечания CI](project/CI_NOTES.md)
