# Migration to Date-Based Auto-Versioning

## Summary

The project has migrated from **semantic versioning (v1.2.3)** to **date-based auto-versioning (vYYYY.M.D.N)**.

## Key Changes

### Version Format

**Before (Semantic Versioning):**
```
v1.0.0, v1.1.0, v1.2.3
```

**After (Date-Based):**
```
v2025.1.15.1, v2025.1.15.2, v2025.12.3.1
```

### Version Format Details

- `YYYY` - Year (4 digits)
- `M` - Month (1-12, no leading zeros)
- `D` - Day (1-31, no leading zeros)
- `N` - Sequential number (starts at 1 each day)

## What Changed

### 1. New Workflow

**File:** `.github/workflows/auto-version-tag.yml`

This workflow automatically:
- Triggers on every push to `main` branch
- Calculates the next version based on current date
- Creates a git tag
- Creates a GitHub Release with commit history
- Triggers the build workflow

### 2. Updated Documentation

**New Documentation:**
- [`docs/release/AUTO_VERSION_TAG.md`](./release/AUTO_VERSION_TAG.md) - Complete guide to the new system

**Updated Documentation:**
- [`docs/release/RELEASE_PROCESS.md`](./release/RELEASE_PROCESS.md) - Marked as legacy
- [`docs/release/README.md`](./release/README.md) - Updated to reference new system

### 3. Test Script

**File:** `scripts/test-version-calculation.sh`

Script to test version calculation logic locally.

## How It Works

### Automatic Release on Merge

```
Developer merges PR to main
          ↓
Auto-version workflow triggers
          ↓
Calculate next version (e.g., v2025.1.15.1)
          ↓
Create and push git tag
          ↓
Create GitHub Release with commit history
          ↓
Build workflow triggers (tag-build-release.yml)
          ↓
Artifacts built and attached to release
```

### Multiple Releases Same Day

The system handles multiple releases on the same day:

```
First merge today  → v2025.1.15.1
Second merge today → v2025.1.15.2
Third merge today  → v2025.1.15.3
```

Next day:
```
First merge tomorrow → v2025.1.16.1  (resets to .1)
```

## Benefits

### Advantages of Date-Based Versioning

1. **Simplicity** - No need to decide on version bump size
2. **Automatic** - Every merge creates a release automatically
3. **Traceable** - Version includes the release date
4. **Predictable** - Same format every time
5. **No Conflicts** - No merge conflicts on version files

### Use Cases

Date-based versioning is ideal for:
- Applications (not libraries)
- Time-sensitive releases
- Continuous deployment
- Projects where release date matters more than API compatibility

## Migration Guide

### For Developers

**No changes needed!** Just merge to main as usual:

```bash
# Before (with Release Please)
git commit -m "feat: add new feature"  # Requires conventional commits
git push

# After (with Auto-Version)
git commit -m "add new feature"  # Any commit message works
git push
# → Automatically creates v2025.1.15.1
```

**Best Practices:**
- Write clear commit messages (they appear in release notes)
- Ensure CI passes before merging
- Monitor the Actions tab after merge

### For Users

**Existing releases are preserved.** Old semantic versions (v1.0.0, etc.) remain available.

**Finding releases:**
- Latest release: Always the newest date-based tag
- Specific date: Search for `v2025.1.15.*`
- All releases: Visit the [Releases page](https://github.com/nagual2/openwrt-captive-monitor/releases)

### For CI/CD

**Build workflow unchanged.** The `tag-build-release.yml` workflow still triggers on any `v*` tag, so it works with both formats.

**Status checks unchanged.** Branch protection rules remain the same.

## Backward Compatibility

### Existing Tags

All existing semantic version tags are preserved:
- `v1.0.0`
- `v1.1.0`
- `v1.2.3`
- etc.

These remain accessible and functional.

### Co-existence

The new date-based tags co-exist with old semantic tags:

```
Existing tags:     v1.0.0, v1.1.0, v1.2.3
New tags:          v2025.1.15.1, v2025.1.15.2
```

Both formats work with the build workflow.

## Testing

### Test Version Calculation

Run the test script to validate the logic:

```bash
./scripts/test-version-calculation.sh
```

This tests:
- Version calculation with various tag scenarios
- Pattern matching for valid/invalid tags
- Edge cases (large sequence numbers, non-sequential tags)

### Verify Workflow

Check the workflow is valid:

```bash
./actionlint .github/workflows/auto-version-tag.yml
```

## Troubleshooting

### "Tag already exists" Error

**Cause:** A tag was already created for today's date and sequence.

**Solution:** This is normal if the workflow ran multiple times. The workflow will skip tag creation gracefully.

### No Release Created

**Cause:** Possible GitHub API rate limit or permissions issue.

**Solution:**
1. Check workflow logs in Actions tab
2. Verify `contents: write` permission
3. Manually create release if needed: `gh release create v2025.1.15.1`

### Build Not Triggered

**Cause:** Build workflow not watching for the new tag.

**Solution:** Verify `tag-build-release.yml` has `tags: ['v*']` trigger pattern.

## Rollback Plan

If needed, you can revert to Release Please:

1. Disable auto-version workflow:
   ```bash
   mv .github/workflows/auto-version-tag.yml .github/workflows/auto-version-tag.yml.disabled
   ```

2. Re-enable Release Please (it's still present in `release-please.yml`)

3. Continue using conventional commits for version control

## Questions & Support

### Where to Get Help

- **Documentation:** [`docs/release/AUTO_VERSION_TAG.md`](./release/AUTO_VERSION_TAG.md)
- **Test Script:** `./scripts/test-version-calculation.sh`
- **Issues:** Open an issue on GitHub
- **Workflow Logs:** Check the Actions tab

### Common Questions

**Q: Can I use semantic versioning again?**  
A: Yes, just disable the auto-version workflow and use Release Please.

**Q: What happens to VERSION file?**  
A: It's no longer automatically updated. Manual updates may be needed for package builds.

**Q: Can I create tags manually?**  
A: Yes, but use the date format: `v2025.1.15.1`

**Q: How do I know what changed in a release?**  
A: Check the release notes in GitHub Releases - they list all commits.

**Q: Can I skip a release?**  
A: Disable the workflow temporarily before merging, or merge to a different branch first.

## Timeline

- **Previous System:** Release Please (semantic versioning)
- **Migration Date:** January 2025
- **New System:** Date-based auto-versioning

## Related Documentation

- [Auto Version Tag Guide](./release/AUTO_VERSION_TAG.md) - Complete user guide
- [Release Process (Legacy)](./release/RELEASE_PROCESS.md) - Historical documentation
- [Release Documentation](./release/README.md) - Release documentation index

---

**Last Updated:** January 2025  
**Migration Status:** ✅ Complete
