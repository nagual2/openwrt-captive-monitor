# GitHub Actions Workflow Changes - Duplicate Test Removal

## Issues Fixed

### 1. ✅ Duplicate Test Execution

**Problem**: Both `ci.yml` and `openwrt-build.yml` were running the same test harness

- `ci.yml`: `busybox ash tests/run.sh`
- `openwrt-build.yml`: `busybox sh tests/run.sh`

**Solution**: Removed duplicate test execution from `openwrt-build.yml`

### 2. ✅ Trigger Overlap

**Problem**: Both workflows triggered on the same events, causing simultaneous runs

**Solution**: Modified `openwrt-build.yml` triggers:

  - **Before**: All branch pushes + pull_request + tags + manual
  - **After**: Main branch pushes + tags + manual

### 3. ✅ Missing Concurrency Control

**Problem**: `ci.yml` didn't have concurrency control

**Solution**: Added concurrency control to prevent queue buildup:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

## Current Workflow Behavior

### `ci.yml` - Main CI/CD Pipeline

  - **Triggers**: All branch pushes + pull_requests + manual
  - **Jobs**: Lint → Test
  - **Concurrency**: Enabled
  - **Artifacts**: Uploads test results

### `openwrt-build.yml` - Package Builds

  - **Triggers**: Main branch pushes + tags + manual
  - **Jobs**: Build (matrix) → Release (on tags)
  - **Concurrency**: Enabled
  - **Dependencies**: Downloads test results from CI

### `release-please.yml` - Automated Releases

  - **Triggers**: Main branch pushes + manual
  - **Purpose**: Create releases when needed

## Expected Results

✅ **Tests run only once per commit/PR** (in ci.yml only)
✅ **No duplicate test executions** 
✅ **Proper sequencing**: Tests complete before builds start
✅ **Concurrency control** prevents queue buildup
✅ **All test coverage maintained**
✅ **Optimized triggers** avoid unnecessary overlap

## Files Modified

1. `.github/workflows/ci.yml` - Added concurrency control
2. `.github/workflows/openwrt-build.yml` - Removed duplicate test, simplified triggers
3. `.github/workflows/release-please.yml` - No changes needed (reverted attempted change)

The duplicate test workflow issue has been resolved!
