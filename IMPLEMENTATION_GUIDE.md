# Implementation Guide for Post-Release CI Fixes

## Quick Start

This document provides step-by-step instructions to implement the fixes for the post-release CI failures.

## Files to Apply

### 1. OpenWrt Build Architecture Fix
**File**: `FIXES/openwrt-build-architecture-fix.yml`
**Target**: `.github/workflows/openwrt-build.yml`
**Action**: Replace the "Collect package metadata" step (lines 102-129)

### 2. Shellcheck Installation Fix  
**File**: `FIXES/ci-shellcheck-fix.yml`
**Target**: `.github/workflows/ci.yml`
**Action**: Replace the "Install dependencies" step (lines 60-74)

### 3. Release-Please Fix
**File**: `FIXES/release-please-fix.yml`
**Target**: `.github/workflows/release-please.yml`
**Action**: Replace the entire file

## Implementation Steps

### Step 1: Apply OpenWrt Build Fix

```bash
# Backup original file
cp .github/workflows/openwrt-build.yml .github/workflows/openwrt-build.yml.backup

# Apply the fix (manual edit required)
# Open .github/workflows/openwrt-build.yml
# Replace lines 102-129 with content from FIXES/openwrt-build-architecture-fix.yml
```

### Step 2: Apply Shellcheck Fix

```bash
# Backup original file
cp .github/workflows/ci.yml .github/workflows/ci.yml.backup

# Apply the fix (manual edit required)
# Open .github/workflows/ci.yml
# Replace lines 60-74 with content from FIXES/ci-shellcheck-fix.yml
```

### Step 3: Apply Release-Please Fix

```bash
# Backup original file
cp .github/workflows/release-please.yml .github/workflows/release-please.yml.backup

# Replace entire file
cp FIXES/release-please-fix.yml .github/workflows/release-please.yml
```

## Testing After Fixes

### Test 1: Local Build Verification

```bash
# Test that the architecture fix logic works
./scripts/build_ipk.sh --arch generic
ls -la dist/opkg/all/  # Should show openwrt-captive-monitor_1.0.4-1_all.ipk

# Verify the expected path matches workflow logic
echo "Expected: dist/opkg/all/openwrt-captive-monitor_1.0.4-1_all.ipk"
echo "Actual: $(find dist/opkg -name '*.ipk')"
```

### Test 2: Shellcheck Installation

```bash
# Test shellcheck installation method
docker run -i ubuntu:22.04 << 'EOF'
apt-get update
wget -qO- https://github.com/koalaman/shellcheck/releases/download/v0.9.0/shellcheck-v0.9.0.linux.x86_64.tar.xz | tar -xJv
./shellcheck-v0.9.0/shellcheck --version
EOF
```

### Test 3: Release-Please Configuration

```bash
# Verify release-please config is valid
cat .release-please-manifest.json
cat release-please-config.json

# Test locally (if release-please is installed)
# release-please manifest --config release-please-config.json --manifest-file .release-please-manifest.json
```

## Validation Workflow

After applying fixes, the expected workflow should be:

1. **Push to main** → Triggers all workflows
2. **CI workflow** → Linting passes (shellcheck works)
3. **OpenWrt build** → All architectures build successfully
4. **Release-please** → Version management works

## Rollback Procedures

If any fix causes issues:

### Rollback OpenWrt Build Fix
```bash
cp .github/workflows/openwrt-build.yml.backup .github/workflows/openwrt-build.yml
```

### Rollback Shellcheck Fix
```bash
cp .github/workflows/ci.yml.backup .github/workflows/ci.yml
```

### Rollback Release-Please Fix
```bash
cp .github/workflows/release-please.yml.backup .github/workflows/release-please.yml
```

## Monitoring Checklist

After deployment, monitor:

- [ ] CI workflow runs successfully
- [ ] All OpenWrt architectures build (generic, x86-64, armvirt-64, mips_24kc)
- [ ] Artifacts are uploaded correctly
- [ ] Release-please creates releases properly
- [ ] Version files are updated correctly

## Troubleshooting

### If OpenWrt Build Still Fails
1. Check the exact filename created vs expected
2. Verify the feed directory structure
3. Check PKG_ARCH vs build_arch values in workflow logs

### If Shellcheck Still Fails
1. Verify wget can access GitHub releases
2. Check if the shellcheck binary is executable
3. Verify PATH includes /usr/bin

### If Release-Please Still Fails
1. Check workflow permissions
2. Verify token has write access
3. Check if main branch is protected

## Contact Information

- **DevOps Team**: infrastructure@company.com
- **On-call Engineer**: oncall@company.com
- **Emergency Contact**: emergency@company.com

---

**Implementation Date**: 2024-XX-XX
**Review Date**: 2024-XX-XX
**Next Review**: After first successful release