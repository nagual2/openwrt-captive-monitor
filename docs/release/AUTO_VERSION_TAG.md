# Automatic Date-Based Version Tagging

## Overview

This project uses **automatic date-based versioning** with the format `vYYYY.M.D.N`, where:

- `YYYY` = Year (4 digits)
- `M` = Month (1-12, no leading zeros)
- `D` = Day (1-31, no leading zeros)
- `N` = Sequential number for releases on the same day (starts at 1)

**Examples:**
- `v2025.1.15.1` - First release on January 15, 2025
- `v2025.1.15.2` - Second release on January 15, 2025
- `v2025.12.3.1` - First release on December 3, 2025

## How It Works

### Automatic Triggering

The auto-versioning workflow (`auto-version-tag.yml`) automatically triggers on **every push to the `main` branch**. This includes:

- Merges from pull requests
- Direct pushes (if permitted by branch protection)
- Merges from hotfix branches

### Version Calculation

When triggered, the workflow:

1. **Fetches all existing tags** from the repository
2. **Determines current date** (UTC timezone)
3. **Searches for existing tags** matching today's date pattern (e.g., `v2025.1.15.*`)
4. **Calculates next sequence number**:
   - If no tags exist for today → sequence = 1
   - If tags exist → sequence = (highest existing sequence) + 1
5. **Creates new tag** with the calculated version

### Release Creation

After creating the tag, the workflow:

1. **Generates release notes** from commit history
   - Lists all commits since the previous release
   - Uses simple format: `- commit message (hash)`
2. **Creates GitHub Release** with:
   - Title: The version tag (e.g., `v2025.1.15.1`)
   - Body: Generated release notes with commit history
   - Tag: The newly created version tag
3. **Triggers build workflow** (`tag-build-release.yml`) automatically via the new tag

## Workflow Sequence

```
┌────────────────────────────────────────────┐
│  Code merged to main branch                │
└──────────────────┬─────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────┐
    │  Auto Version Tag Workflow   │
    │  - Calculate next version    │
    │  - Generate release notes    │
    │  - Create tag                │
    │  - Create GitHub Release     │
    └──────────────┬───────────────┘
                   │
                   ▼ (Tag created → triggers build)
    ┌──────────────────────────────┐
    │  Build & Release Workflow    │
    │  - Build OpenWrt package     │
    │  - Sign artifacts            │
    │  - Upload to release         │
    └──────────────────────────────┘
```

## Version Examples

### First Release of the Day

```bash
# Before: No tags exist for 2025-01-15
# After merge to main:
# → Creates: v2025.1.15.1
```

### Multiple Releases Same Day

```bash
# Existing tags: v2025.1.15.1
# After another merge:
# → Creates: v2025.1.15.2

# Existing tags: v2025.1.15.1, v2025.1.15.2
# After third merge:
# → Creates: v2025.1.15.3
```

### Next Day Release

```bash
# Existing tags: v2025.1.15.1, v2025.1.15.2, v2025.1.15.3
# Next day (2025-01-16), after merge:
# → Creates: v2025.1.16.1  (sequence resets to 1)
```

## Release Notes Format

Release notes are automatically generated from commit history:

```markdown
## Release v2025.1.15.1

Generated on 2025-01-15 10:30:00 UTC

Changes since v2025.1.14.1:
- feat: add new feature X (a1b2c3d)
- fix: resolve issue with Y (e4f5g6h)
- docs: update README (i7j8k9l)
- chore: update dependencies (m0n1o2p)
```

### First Release

If no previous tags exist, the notes will show recent commits:

```markdown
## Release v2025.1.15.1

Generated on 2025-01-15 10:30:00 UTC

Changes since repository inception:
- Initial commit (a1b2c3d)
- Add core functionality (e4f5g6h)
- Configure CI/CD (i7j8k9l)
```

## Handling Edge Cases

### Tag Already Exists

If a tag already exists (e.g., manually created), the workflow:
- Detects the existing tag
- Skips tag creation
- Logs a message: "Tag already exists"
- Does not fail (graceful handling)

### No New Commits

If there are no commits since the last release, the workflow:
- Still creates a new tag and release
- Release notes will show "No new commits found"

### Same-Day Rapid Releases

The workflow handles multiple releases on the same day by incrementing the sequence number:
- First merge: `v2025.1.15.1`
- Second merge: `v2025.1.15.2`
- Third merge: `v2025.1.15.3`
- etc.

## Testing Version Calculation

A test script is provided to validate the version calculation logic locally:

```bash
./scripts/test-version-calculation.sh
```

This script tests:
- Version calculation with no existing tags
- Version calculation with one or more existing tags
- Handling of non-sequential tags
- Large sequence numbers
- Pattern matching for valid/invalid tag formats

## Comparison with Semantic Versioning

### Previous System (Release Please)

- **Format:** `vMAJOR.MINOR.PATCH` (e.g., `v1.2.3`)
- **Trigger:** Conventional commit messages (`feat:`, `fix:`, `BREAKING CHANGE:`)
- **Manual Control:** Developers controlled version bumps via commit types
- **Changelog:** Generated from conventional commits

### Current System (Date-Based)

- **Format:** `vYYYY.M.D.N` (e.g., `v2025.1.15.1`)
- **Trigger:** Every merge to main
- **Automatic:** No manual version control needed
- **Changelog:** Lists all commits since last release

### Key Differences

| Aspect | Semantic Versioning | Date-Based |
|--------|---------------------|------------|
| **Version meaning** | API compatibility | Release date |
| **Version control** | Manual (via commits) | Fully automatic |
| **Release cadence** | On-demand | Every merge |
| **Changelog** | Categorized by type | Chronological |
| **Best for** | Library/API versioning | Time-sensitive releases |

## Migration Notes

### From Release Please to Auto-Version

The repository now uses date-based auto-versioning. The previous Release Please workflow (`release-please.yml`) remains in place but can be disabled if desired.

**Key changes:**
1. Tags now use date format instead of semantic version
2. Releases are created on every merge to main
3. No need for conventional commit format (but still recommended for clarity)
4. Version numbers reset daily

### Existing Tags

Existing semantic version tags (e.g., `v1.0.0`) are preserved and not affected by the new workflow.

## Troubleshooting

### Tag Not Created

**Symptoms:** Workflow runs but no tag is created

**Possible causes:**
- Tag already exists for the calculated version
- Git permissions issue
- GitHub token doesn't have write permissions

**Resolution:**
1. Check workflow logs for error messages
2. Verify `contents: write` permission is set in workflow
3. Check if tag already exists: `git ls-remote --tags origin`

### Release Not Created

**Symptoms:** Tag is created but GitHub Release is missing

**Possible causes:**
- GitHub API rate limit
- Token permissions issue
- Release already exists for the tag

**Resolution:**
1. Check workflow logs for API errors
2. Verify GitHub token has release creation permissions
3. Check if release already exists in GitHub UI

### Wrong Version Number

**Symptoms:** Version number is not what you expected

**Possible causes:**
- Timezone difference (workflow uses UTC)
- Existing tags not fetched properly
- Local git tags differ from remote

**Resolution:**
1. Verify your timezone vs UTC
2. Run `git fetch --tags --force` to sync tags
3. Check existing tags: `git tag -l "v$(date -u +%Y.%-m.%-d).*"`

### Build Workflow Not Triggered

**Symptoms:** Tag and release created, but no build artifacts

**Possible causes:**
- `tag-build-release.yml` workflow not configured for new tag format
- Workflow trigger pattern doesn't match date-based tags

**Resolution:**
1. Verify `tag-build-release.yml` has trigger: `tags: ['v*']`
2. Check Actions tab for workflow run
3. Manually trigger build workflow if needed

## Manual Operations

### Manually Trigger Workflow

You can manually trigger the auto-version workflow:

```bash
gh workflow run auto-version-tag.yml --repo <owner>/<repo>
```

Or via GitHub UI:
1. Go to **Actions** → **Auto Version Tag and Release**
2. Click **Run workflow**
3. Select branch (should be `main`)
4. Click **Run workflow**

### Create Manual Release

If you need to create a version manually:

```bash
# Calculate today's next version
DATE_PREFIX="v$(date -u +%Y.%-m.%-d)"
LAST_SEQ=$(git tag -l "${DATE_PREFIX}.*" | sed -nE "s/^${DATE_PREFIX}\.([0-9]+)$/\1/p" | sort -n | tail -n1)
NEXT_SEQ=$((${LAST_SEQ:-0} + 1))
NEW_TAG="${DATE_PREFIX}.${NEXT_SEQ}"

# Create and push tag
git tag -a "$NEW_TAG" -m "Release $NEW_TAG"
git push origin "$NEW_TAG"

# Create release (optional - workflow will do this automatically)
gh release create "$NEW_TAG" --title "$NEW_TAG" --generate-notes
```

## Best Practices

1. **Merge to main regularly**: Each merge creates a new release
2. **Write clear commit messages**: They become part of release notes
3. **Test before merging**: Ensure CI passes before merge
4. **Monitor releases**: Check Actions tab after merging
5. **Keep main stable**: Only merge tested, reviewed code

## Advanced Configuration

### Modify Release Notes Format

Edit the workflow file `.github/workflows/auto-version-tag.yml`, step "Generate release notes":

```yaml
- name: Generate release notes
  id: notes
  run: |
    # Customize the format here
    echo "## Release $NEW_TAG" > "$NOTES_FILE"
    echo "" >> "$NOTES_FILE"
    echo "Custom message here" >> "$NOTES_FILE"
    # Add your custom logic
```

### Change Timezone

By default, the workflow uses UTC. To use a different timezone:

```yaml
- name: Determine next version
  id: version
  run: |
    # Change this line:
    YEAR=$(date -u +%Y)  # UTC
    # To use local time:
    YEAR=$(date +%Y)
    # Or specific timezone:
    YEAR=$(TZ=America/New_York date +%Y)
```

**Note:** Changing timezone may cause confusion if contributors are in different timezones.

### Skip Auto-Versioning

To prevent a merge from creating a release, you can:

1. **Temporarily disable workflow**: Rename the workflow file or set `if: false` condition
2. **Use a different branch**: Merge to a staging branch first, then to main when ready

## Workflow Configuration

### Permissions

The workflow requires these permissions:

```yaml
permissions:
  contents: write  # To create tags and push to repository
```

The workflow uses `secrets.GITHUB_TOKEN` which is automatically provided by GitHub Actions.

### Concurrency

The workflow uses concurrency settings to prevent race conditions:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: false
```

This ensures only one version tag is created at a time.

## Support

For issues or questions:

1. Check this documentation
2. Review workflow logs in Actions tab
3. Test version calculation locally: `./scripts/test-version-calculation.sh`
4. Open an issue with workflow logs

---

**Last Updated:** January 2025  
**Version Scheme:** Date-Based `vYYYY.M.D.N`  
**Workflow File:** `.github/workflows/auto-version-tag.yml`
