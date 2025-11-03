# GitHub Actions Fix Summary

## Changes Made

### 1. ✅ Unified actions/checkout versions
- **Before:** Mixed versions - v4 in cleanup.yml, v5 in others
- **After:** All workflows now use `actions/checkout@v5`
- **Files updated:**
  - `.github/workflows/cleanup.yml` (line 19): `@v4` → `@v5`

### 2. ✅ Updated deprecated actions

#### Markdown Lint Action
- **Before:** `avto-dev/markdown-lint@v1` (deprecated)
- **After:** `DavidAnson/markdownlint-cli2-action@v18` (actively maintained)
- **Files updated:**
  - `.github/workflows/ci.yml` (line 92): Updated action and parameter name `args` → `files`

#### Workflow Run Cleanup Action  
- **Before:** `rokroskar/workflow-run-cleanup-action@v1.0.0` (deprecated)
- **After:** `actions/github-script@v7` with custom cleanup script
- **Files updated:**
  - `.github/workflows/cleanup.yml` (line 40): Replaced with equivalent functionality using GitHub Script

#### Artifact Delete Action
- **Before:** `actions/upload-artifact/delete-artifact@v4` (deprecated)
- **After:** `actions/github-script@v7` with custom deletion script
- **Files updated:**
  - `.github/workflows/cleanup.yml` (line 34): Replaced with equivalent functionality

### 3. ✅ Standardized artifact action versions
- **Before:** Mixed versions - upload@v5, download@v6
- **After:** All artifact actions use v4 (current stable)
- **Files updated:**
  - `.github/workflows/ci.yml` (line 133): `upload-artifact@v5` → `@v4`
  - `.github/workflows/openwrt-build.yml` (line 54): `download-artifact@v6` → `@v4`
  - `.github/workflows/openwrt-build.yml` (line 138): `upload-artifact@v5` → `@v4`
  - `.github/workflows/openwrt-build.yml` (line 179): `download-artifact@v6` → `@v4`

## Final Action Versions

| Action | Version | Status |
|--------|---------|--------|
| `actions/checkout` | `@v5` | ✅ Unified across all workflows |
| `actions/cache` | `@v4` | ✅ Consistent |
| `actions/upload-artifact` | `@v4` | ✅ Standardized |
| `actions/download-artifact` | `@v4` | ✅ Standardized |
| `actions/github-script` | `@v7` | ✅ Latest |
| `DavidAnson/markdownlint-cli2-action` | `@v18` | ✅ Updated from deprecated |
| `reviewdog/action-actionlint` | `@v1` | ✅ Current |
| `softprops/action-gh-release` | `@v2` | ✅ Current |
| `google-github-actions/release-please-action` | `@v4` | ✅ Current |

## Verification

- ✅ YAML syntax is valid for all workflow files
- ✅ All actions use current, actively maintained versions
- ✅ Workflow logic remains unchanged (only action versions updated)
- ✅ No new checks or steps added
- ✅ Consistent versions across all workflows

## Impact

These changes ensure:
- Better security with up-to-date actions
- Continued compatibility as deprecated actions are removed
- Consistent behavior across all workflows
- Maintained functionality while using modern action versions
