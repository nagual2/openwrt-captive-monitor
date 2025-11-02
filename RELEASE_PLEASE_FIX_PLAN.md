# Fix Plan for Release Please Version Issues

## Problem Analysis
After PR #73 merge, the Release Please workflow created a release PR (version 1.0.0) but failed to properly synchronize all version files. This creates inconsistent versioning across the project.

## Current Version State (as of main branch)
- `VERSION` file: **1.0.1**
- `.release-please-manifest.json`: **0.1.2** (on main)
- `package/openwrt-captive-monitor/Makefile` PKG_VERSION: **0.1.2**
- Release branch manifest: **1.0.0**

## Root Cause
The Release Please workflow's `update-version` job may have:
1. Failed to run due to permissions
2. Not properly updated all version files
3. Run on the wrong branch/context

## Immediate Fix Commands

### Step 1: Align all versions to 1.0.0 on main
```bash
# Update VERSION file
echo "1.0.0" > VERSION

# Update Makefile PKG_VERSION
sed -i 's/^PKG_VERSION:=.*/PKG_VERSION:=1.0.0/' package/openwrt-captive-monitor/Makefile

# Update release manifest to match
sed -i 's/"\.".*$/".": "1.0.0"/' .release-please-manifest.json

# Commit and push
git add VERSION package/openwrt-captive-monitor/Makefile .release-please-manifest.json
git commit -m "fix: synchronize all version files to 1.0.0 for release"
git push
```

### Step 2: Verify Release PR
```bash
# Check the release PR changes
git diff main..origin/release-please--branches--main

# The release PR should now be ready to merge
```

### Step 3: Merge Release PR
```bash
# After verification, merge the release PR via GitHub web interface
# This will create the v1.0.0 tag and release
```

## Workflow Investigation

### Check Release Please Configuration
The workflow expects to update the Makefile version, but there might be a path issue:
```yaml
# Current workflow line 72:
sed -i "s/^PKG_VERSION:=.*/PKG_VERSION:=$VERSION/" package/openwrt-captive-monitor/Makefile
```

This should work, but we need to verify:
1. The workflow has write permissions
2. The file paths are correct
3. The regex matches the Makefile format

### Potential Workflow Fixes
If the issue persists, consider these improvements:

1. **Add version consistency check**:
```yaml
- name: Verify version consistency
  run: |
    MANIFEST_VERSION=$(jq -r '."' .release-please-manifest.json)
    MAKEFILE_VERSION=$(grep '^PKG_VERSION:=' package/openwrt-captive-monitor/Makefile | cut -d'=' -f2)
    VERSION_FILE=$(cat VERSION)
    
    if [ "$MANIFEST_VERSION" != "$MAKEFILE_VERSION" ] || [ "$MANIFEST_VERSION" != "$VERSION_FILE" ]; then
      echo "Version mismatch detected!"
      echo "Manifest: $MANIFEST_VERSION"
      echo "Makefile: $MAKEFILE_VERSION" 
      echo "VERSION file: $VERSION_FILE"
      exit 1
    fi
```

2. **Update all version files explicitly**:
```yaml
- name: Update all version files
  run: |
    VERSION="${{ needs.release-please.outputs.tag_name }}"
    VERSION="${VERSION#v}"
    
    # Update Makefile
    sed -i "s/^PKG_VERSION:=.*/PKG_VERSION:=$VERSION/" package/openwrt-captive-monitor/Makefile
    
    # Update VERSION file
    echo "$VERSION" > VERSION
    
    # Update release manifest (should already be done by release-please)
    # But verify it's correct
    jq '."' = "$VERSION"' .release-please-manifest.json > tmp.json && mv tmp.json .release-please-manifest.json
```

## Verification Steps

After applying fixes:

1. **Check version consistency**:
```bash
echo "VERSION file: $(cat VERSION)"
echo "Manifest: $(jq -r '."' .release-please-manifest.json)"
echo "Makefile: $(grep '^PKG_VERSION:=' package/openwrt-captive-monitor/Makefile | cut -d'=' -f2)"
```

2. **Verify release PR**:
```bash
git log origin/release-please--branches--main --oneline -3
git diff main..origin/release-please--branches--main --name-only
```

3. **Test Release Please workflow**:
   - Trigger the workflow manually or push a small change
   - Verify all version files are updated consistently
   - Check if the release PR is created properly

## Prevention Measures

1. **Add pre-commit hook** for version consistency
2. **Add CI check** to verify version file synchronization
3. **Document version update process** clearly
4. **Consider using a single source of truth** for version information

## Timeline

- **Immediate**: Apply version fix commands
- **Short-term**: Merge release PR and verify 1.0.0 release
- **Medium-term**: Improve workflow with consistency checks
- **Long-term**: Implement better version management system