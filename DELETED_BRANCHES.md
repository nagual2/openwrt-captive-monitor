# Deleted Branches

## Merged and removed

### PR #65 - fix-release-please-permissions
- **Branch**: `fix-release-please-permissions`
- **Status**: ✅ Merged into main on 2025-10-30
- **Description**: Fix GitHub Actions permissions error for automated PRs
- **Deleted**: ✅ Yes

### PR #64 - ci(deps): bump actions/checkout from 4 to 5
- **Branch**: Part of main branch (no separate branch to delete)
- **Status**: ✅ Merged into main
- **Description**: Bump actions/checkout from 4 to 5 in the github-actions group
- **Deleted**: N/A (merged directly)

### PR #63 - cleanup/remove-non-openwrt-deps-ci-scripts
- **Branch**: `cleanup/remove-non-openwrt-deps-ci-scripts`
- **Status**: ✅ Merged into main
- **Description**: Remove non-OpenWrt dependencies and simplify CI/scripts
- **Deleted**: ✅ Yes

### PR #61 - fix-github-actions-tests-add-semver-changelog
- **Branch**: `fix-github-actions-tests-add-semver-changelog`
- **Status**: ✅ Merged into main
- **Description**: Fix GitHub CI tests, enforce shell script lint, and align versioning
- **Deleted**: ✅ Yes

## Kept (still needed)

### fix-ci-failing-tests
- **Branch**: `fix-ci-failing-tests`
- **Status**: ⚠️ Not merged (PR #62 - status unknown)
- **Reason**: Contains commits not in main, no evidence of merge
- **Action**: 🔄 Keep for now - needs review

### chore-audit-merge-active-branches
- **Branch**: `chore-audit-merge-active-branches`
- **Status**: 🔄 Active development
- **Reason**: Newer than main, contains merge resolution work
- **Action**: 🔄 Keep - active work in progress

### release-please--branches--main
- **Branch**: `release-please--branches--main`
- **Status**: 🔄 Release branch
- **Reason**: Automated release management branch
- **Action**: 🔄 Keep - required for release automation

### main
- **Branch**: `main`
- **Status**: ✅ Protected branch
- **Reason**: Main development branch
- **Action**: 🔄 Never delete

## Summary

**Total branches deleted**: 3
**Total branches kept**: 4
**Total branches analyzed**: 7

## Cleanup Commands Used

```bash
# Deleted merged branches
git push origin --delete fix-release-please-permissions
git push origin --delete cleanup/remove-non-openwrt-deps-ci-scripts
git push origin --delete fix-github-actions-tests-add-semver-changelog

# Cleaned up local references
git fetch --all --prune
git remote prune origin
```

## Safety Rules Followed

✅ Did NOT delete: main, develop, master  
✅ Did NOT delete: branches with open PRs (none found)  
✅ Did NOT delete: release-please branches (kept release-please--branches--main)  
✅ Did NOT delete: branches with unmerged unique commits (kept fix-ci-failing-tests)  
✅ Verified all deleted branches had their PRs merged into main