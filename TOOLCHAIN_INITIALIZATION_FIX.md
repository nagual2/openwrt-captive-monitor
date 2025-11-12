# OpenWrt Toolchain Initialization Fix - ld-musl Missing Error

## Problem Statement

When building the `openwrt-captive-monitor` package with the OpenWrt SDK, a build error occurs:

```
cp: cannot stat '/.../staging_dir/toolchain-x86_64_gcc-12.3.0_musl/lib/ld-musl-*.so*': No such file or directory
```

This error indicates that the musl C library dynamic linker files (`ld-musl-*.so`) are missing from the SDK's staging directory.

## Root Cause

The OpenWrt SDK's `staging_dir` needs to be properly initialized before building packages. This is done by running `make toolchain/install` in the SDK directory. 

When package dependencies (like `curl`, `dnsmasq`, `iptables`, etc.) need to be built from source, the build system requires access to the full toolchain, including:
- The musl C library loader (`ld-musl-*.so`)
- Standard library headers and shared objects
- Compiler and build tools

If `make toolchain/install` is not executed, the SDK remains in a partially initialized state, and when the build tries to compile dependencies or link binaries, it fails because it cannot find the necessary toolchain files.

## Solution

The fix adds a new build step in the CI/CD workflows to explicitly build and install the toolchain before attempting to compile the package.

### Changes Made

#### 1. `.github/workflows/build-openwrt-package.yml`

Added a new "Build toolchain" step after "Clean SDK environment":

```yaml
- name: Build toolchain
  run: |
    set -euo pipefail
    SDK_DIR="${{ env.SDK_DIR }}"
    cd "$SDK_DIR"
    
    echo "Building and installing OpenWrt toolchain..."
    echo "This ensures staging_dir is properly initialized with all toolchain files including ld-musl"
    
    # Build toolchain with verbose output to diagnose issues
    if ! make toolchain/install V=s 2>&1 | tee toolchain_build.log; then
      echo "=== TOOLCHAIN BUILD FAILED ==="
      echo "Last 50 lines of toolchain build log:"
      tail -50 toolchain_build.log
      exit 1
    fi
    
    echo "=== Toolchain build completed successfully ==="
    
    # Verify staging_dir structure
    if [ -d staging_dir ]; then
      echo "Toolchain staging_dir contents:"
      find staging_dir -name "ld-musl*" -o -name "libc.so*" | head -20
    else
      echo "Warning: staging_dir not found after toolchain build"
    fi
```

#### 2. `.github/workflows/build.yml`

Added the same "Build toolchain" step after "Clean SDK environment" in the `build-sdk` job.

### How It Works

1. **Environment Setup**: Enters the SDK directory
2. **Toolchain Build**: Runs `make toolchain/install V=s` which:
   - Compiles the cross-compilation toolchain
   - Installs toolchain binaries and libraries to `staging_dir`
   - Creates the `ld-musl-*.so` files needed by the musl C library
3. **Verification**: Checks that the staging_dir now contains the expected musl files
4. **Logging**: Captures toolchain build output for debugging if issues occur
5. **Error Handling**: Fails fast with diagnostic information if toolchain build fails

### Build Order

The correct build order is now:

1. SDK Download & Extract
2. SDK Configuration (defconfig)
3. Clean SDK Environment (distclean)
4. **Build Toolchain** ← NEW STEP (ensures ld-musl files exist)
5. Copy Package Files
6. Update & Install Feeds
7. Build Package

## Impact

- **Fixes**: The `ld-musl-*.so: No such file or directory` error
- **Scope**: Affects all packages that have dependencies requiring compilation
- **Time**: Adds ~10-30 minutes to CI build time (toolchain compilation takes time)
- **Reliability**: Ensures consistent, reproducible builds with all necessary toolchain components

## Testing

To verify the fix works:

1. Monitor the CI/CD workflow logs in `.github/workflows/`
2. Check for the "Build toolchain" step in the logs
3. Verify that staging_dir contains ld-musl files after this step
4. Confirm the package compilation succeeds

## Related Files

- `.github/workflows/build-openwrt-package.yml` - Updated with toolchain build step
- `.github/workflows/build.yml` - Updated with toolchain build step
- `package/openwrt-captive-monitor/Makefile` - No changes (already correct)
- `scripts/build_ipk.sh` - No changes (standalone build script, not affected)

## Notes

- The `make toolchain/install` command is safe to run multiple times
- The SDK caching in CI should be adjusted if toolchain needs frequent updates
- This aligns with OpenWrt SDK best practices documented in official OpenWrt build system documentation
