# Release Please Troubleshooting

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---


## Common Issues and Solutions

### GitHub Actions Permission Error

**Error**: `release-please failed: GitHub Actions is not permitted to create or approve pull requests.`

**Symptoms**:
- Release branch is created successfully (e.g., `release-please--branches--main`)
- Commit is made to the branch
- PR creation fails with permissions error

**Solutions**:

#### Option 1: Enable GitHub Actions PR Creation (Recommended)

1. **Repository Settings**: Go to Settings → Actions → General
2. **Workflow permissions**: Select "Read and write permissions"
3. **Allow GitHub Actions to create and approve pull requests**: ✅ Enable

This is the preferred solution as it doesn't require additional tokens.

#### Option 2: Use Personal Access Token (PAT)

If repository settings cannot be changed, use a PAT token:

1. **Create PAT Token**:
   - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate new token with `repo` scope
   - Name it something like "Release Please Bot"

2. **Add to Repository Secrets**:
   - Go to repository Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `RELEASE_PLEASE_TOKEN`
   - Value: [paste your PAT token]

3. **Update Workflow**:
   ```yaml
   # In .github/workflows/release-please.yml, uncomment the PAT line:
   token: ${{ secrets.RELEASE_PLEASE_TOKEN }}
   # And comment out:
   # token: ${{ secrets.GITHUB_TOKEN }}
   ```

#### Option 3: Organization-Level Settings

If this is an organization repository, check:
- Organization Settings → Actions → General
- Ensure "Allow GitHub Actions to create and approve pull requests" is enabled
- Or use PAT token approach above

### Branch Protection Conflicts

**Issue**: Branch protection rules prevent PR creation

**Solutions**:
1. **Exclude release-please branches** from protection rules:
   - Add pattern `!release-please--branches--*` to branch protection settings
   - Or specifically allow GitHub Actions to bypass protection

2. **Use PAT token** with higher privileges (see Option 2 above)

### Workflow Permissions

The workflow already includes these permissions:
```yaml
permissions:
  contents: write      # Required for creating release branches
  pull-requests: write # Required for creating PRs
  actions: read        # Required for reading workflow info
  checks: write        # Required for status checks
```

If issues persist, ensure these permissions are not overridden at the organization level.

## Verification

After implementing fixes:

1. **Manual trigger**: Run workflow manually via "workflow_dispatch"
2. **Check logs**: Ensure no permission errors
3. **Verify PR**: Confirm release PR is created successfully
4. **Test merge**: Ensure PR can be merged without issues

## Current Status

- ✅ Workflow permissions configured
- ✅ Branch creation working (confirmed by existing release-please branches)
- ❌ PR creation failing (permissions error)
- 🔄 Fix in progress: Enhanced permissions + PAT fallback
