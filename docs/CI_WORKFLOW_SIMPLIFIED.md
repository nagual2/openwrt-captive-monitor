# Simplified CI Workflow

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---


This document explains the simplified CI/CD workflow implemented for openwrt-captive-monitor.

## Overview

The CI workflow has been streamlined to follow the documented OpenWrt SDK workflow pattern. The previous approach using `make distclean` and `make toolchain/install` has been replaced with a simpler, more direct SDK usage pattern.

## Pipeline Structure

```
┌─────────┐     ┌──────────┐     ┌────────────┐     ┌───────────┐
│  Lint   │ --> │   Test   │ --> │  SDK Build │ --> │  Artifact │
│         │     │          │     │            │     │   Upload  │
└─────────┘     └──────────┘     └────────────┘     └───────────┘
```

## Workflow Steps

### 1. Lint (Parallel)

Runs multiple linters in parallel to ensure code quality:

- **shfmt**: Shell script formatting
- **shellcheck**: Shell script static analysis
- **markdownlint**: Documentation linting
- **actionlint**: GitHub Actions workflow linting

### 2. Test

Runs the BusyBox-based test harness:

```bash
busybox ash tests/run.sh
```

Tests include:
- Mock-based unit tests
- Package validation
- Configuration parsing
- Script logic verification

### 3. SDK Build

Builds the package using the OpenWrt SDK following the documented workflow:

**Steps:**
1. Download and extract OpenWrt SDK (with caching)
2. Copy package files to SDK
3. Update feeds: `./scripts/feeds update -a`
4. Install feeds: `./scripts/feeds install -a`
5. Configure SDK: `make defconfig`
6. Build package: `make package/openwrt-captive-monitor/compile V=s`
7. Validate built `.ipk`
8. Upload artifacts

**Key Points:**
- Uses prebuilt toolchain from SDK (no `make toolchain/install`)
- No `make distclean` before build
- Relies on SDK's built-in configuration
- Simple, straightforward workflow

### 4. Artifact Upload

Uploads build artifacts to GitHub Actions:

- `.ipk` package file
- `Packages` index file
- `Packages.gz` compressed index
- `build.log` verbose build output

## Simplified Approach

### What Changed

**Before:**
```bash
make defconfig
make distclean        # Clean everything
make defconfig        # Reconfigure
make toolchain/install V=s  # Build toolchain (10-30 minutes)
# Copy package
# Update feeds
make package/.../compile
```

**After:**
```bash
# Download SDK
# Copy package
./scripts/feeds update -a
./scripts/feeds install -a
make defconfig
make package/.../compile
```

### Benefits

1. **Faster builds**: No toolchain compilation (saves 10-30 minutes)
2. **Simpler workflow**: Fewer steps, clearer intent
3. **Standard approach**: Follows documented OpenWrt SDK usage
4. **Prebuilt toolchain**: Relies on SDK's included toolchain
5. **More reliable**: Fewer moving parts, less room for error

### Why This Works

The OpenWrt SDK comes with a prebuilt cross-compilation toolchain that includes:
- GCC compiler
- Musl C library and loader (`ld-musl-*.so`)
- Build system tools
- Package dependencies

By using the SDK as intended, we avoid the complexity of rebuilding the toolchain and can focus on package compilation.

## SDK Caching

The workflow uses GitHub Actions cache to speed up subsequent builds:

```yaml
Cache Key: ${{ runner.os }}-openwrt-sdk-${{ version }}-${{ arch }}-v3
```

**First build:**
- Downloads SDK (~500MB-1GB)
- Extracts SDK
- Cache saved

**Subsequent builds:**
- Restores SDK from cache (< 1 minute)
- Skips download and extraction

## Error Handling

The workflow includes robust error handling:

- **SDK download failures**: Retries with exponential backoff, falls back to official mirror
- **Feed update failures**: 10 retry attempts with jitter
- **Build failures**: Captures last 100 lines of build log
- **Validation failures**: Runs `validate_ipk.sh` script

## Artifact Management

Build artifacts are:
- Uploaded to GitHub Actions (30-day retention)
- Available for download from workflow runs
- Automatically attached to releases on tag pushes

## Release Integration

The workflow integrates with the release process:

1. **Release Please** creates release PR and tag
2. **CI workflow** triggered by tag push
3. **SDK build job** compiles package
4. **Artifacts** automatically uploaded to GitHub release

## Documentation References

- [SDK Build Workflow Guide](guides/sdk-build-workflow.md)
- [Release Checklist](RELEASE_CHECKLIST.md)
- [Packaging Guide](packaging.md)

## Troubleshooting

### Build Failures

Check the build log in artifacts:
```bash
# Download and extract artifacts from workflow run
cat build.log
```

### Package Not Found

Verify package was copied to SDK:
```bash
ls -la "$SDK_DIR/package/openwrt-captive-monitor/"
```

### Feed Issues

Check feed update logs for network errors or repository issues.

## Further Reading

- [OpenWrt SDK Documentation](https://openwrt.org/docs/guide-developer/toolchain/using_the_sdk)
- [OpenWrt Build System](https://openwrt.org/docs/guide-developer/toolchain/buildsystem_essentials)
- [Package Build Guide](https://openwrt.org/docs/guide-developer/packages)
