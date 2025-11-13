# Branch Protection Setup Instructions

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---


## GitHub Repository Settings Configuration

To complete the trunk protection setup, configure these settings in your GitHub repository:

### 1. Branch Protection Rule for `main`

**Settings → Branches → Add rule**

1. **Branch name pattern**: `main`
2. **Protect matching branches**: ✅ Enable
3. **Branch protection options**:
   - ✅ Require a pull request before merging
   - ✅ Require approvals: 1
   - ✅ Dismiss stale pull request approvals when new commits are pushed
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Require linear history
   - ✅ Restrict pushes that create matching branches (limit to maintainers)
   - ✅ Disallow force pushes

4. **Required status checks** (add these exact names):
   - `Lint / Shell lint`
   - `Build OpenWrt packages / Build (ath79-generic)`
   - `Build OpenWrt packages / Build (ramips-mt7621)`

5. **Save the rule**

### 2. General Settings

**Settings → General → Pull Requests**

1. **Default merge method**: Allow squash merging
2. **Disabled merge methods**: ✅ Disable merge commits, ✅ Disable rebase and merge
3. **Automatically delete head branches**: ✅ Enable

### 3. Repository Rules (Optional Enhancement)

**Settings → Rules → New rule set**

Create a rule set for feature branches:
- **Target**: Branch names matching `feature/*`, `fix/*`, `chore/*`, `docs/*`, `hotfix/*`
- **Required status checks**: Same as main branch
- **Restrict pushes**: ✅ Enable (require PRs for these branches too)

## Verification Steps

After setup, verify:

1. **Branch status**: `git branch -r` shows only `origin/main`
2. **Local branches**: `git branch` shows only `main`
3. **CI workflows**: Both workflows run and pass on pushes to main
4. **PR workflow**: New PRs require approval and pass all status checks before merge

## Current Repository State

✅ **Completed**:
- Trunk identified: `main`
- Feature merge order: opkg package → captive portal functionality
- PRs processed and merged: All changes integrated into main
- Branch cleanup: All redundant branches deleted
- Documentation: BRANCHES_AND_MERGE_POLICY.md, CODEOWNERS, PR templates configured
- CI enforcement: Shell linting and OpenWrt package builds required
- Release automation: release-please workflow configured with proper permissions

🔄 **Pending** (GitHub UI configuration):
- Branch protection rules setup
- Auto-delete branches enabled
- Status checks enforcement
- **GitHub Actions permissions**: Enable "Allow GitHub Actions to create and approve pull requests" in Settings → Actions → General (required for release-please automation)

The repository is now ready for protected, systematic development with enforced CI and merge policies.

## Release Automation Notes

The `release-please` workflow requires special permissions to create release PRs automatically. If GitHub Actions cannot create PRs:

1. **Enable Actions permissions** in repository settings (recommended)
2. **Use PAT token** as documented in `RELEASE_PLEASE_TROUBLESHOOTING.md`
3. **Exclude release branches** from protection if needed: `!release-please--branches--*`
