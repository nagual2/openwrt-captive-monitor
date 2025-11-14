# Release Process Documentation

## Overview

This project uses **automated semantic versioning** with GitHub Actions to manage releases. The process is completely automated when code is merged to the `main` branch, following the [Semantic Versioning 2.0.0](https://semver.org/) specification.

## Branch Protection and Security Requirements

Before any code can be merged to `main` and trigger the automated release process, it **must pass all branch protection checks**. This ensures that only high-quality, secure code reaches production releases.

### Merge Prerequisites

To merge a pull request to `main`, you must satisfy these requirements:

1. **Code Review**: Obtain at least one approval from a repository maintainer
2. **All Status Checks Pass**: Every status check must pass before merging:
   - **CI/Linting**: `Lint (shfmt)`, `Lint (shellcheck)`, `Lint (markdownlint)`, `Lint (actionlint)`, `Test`
   - **Security Scans**: `CodeQL Analysis (python)`, `ShellCheck Security Analysis`, `Dependency Review`, `Trivy Security Scan`, `Bandit Python Security Scan`
3. **Branch Up-to-Date**: Your branch must be rebased on the latest `main`
4. **Conversations Resolved**: All review conversations must be closed
5. **Squash Merge Only**: Use squash merge strategy (merge commits are not allowed)

### Impact on Release Timing

These requirements ensure that:
- No vulnerable code reaches the main branch
- Only fully tested, reviewed code triggers automatic releases
- Release artifacts are built from verified, secure commits
- The release chain of custody is maintained from commit through signed artifact

For detailed information about branch protection rules, see [`.github/settings.yml`](./.github/settings.yml).

## Semantic Versioning

The project uses semantic versioning in the format: `MAJOR.MINOR.PATCH`

- **MAJOR** version: Incompatible API changes
- **MINOR** version: New functionality in a backward-compatible manner
- **PATCH** version: Bug fixes and backwards-compatible changes

### Version Determination

Versions are automatically determined based on conventional commit messages:

- **feat:** triggers a MINOR version bump
- **fix:** triggers a PATCH version bump  
- **feat!:** or **fix!:** triggers a MAJOR version bump (breaking change)
- Other types (docs, ci, refactor, etc.) do not trigger version bumps

### Example Conventional Commits

```bash
# Patch release (1.0.0 -> 1.0.1)
git commit -m "fix: resolve captive portal detection issue"

# Minor release (1.0.0 -> 1.1.0)
git commit -m "feat: add IPv6 support for portal detection"

# Major release (1.0.0 -> 2.0.0)
git commit -m "feat!: rewrite core detection engine

BREAKING CHANGE: Configuration format has changed"
```

## Automated Release Workflow

The release process is fully automated and consists of three main workflows:

### 1. Release Please Workflow

**Triggers:** On push to `main` branch or manual trigger via workflow dispatch

**Steps:**
1. **Code Quality Checks** - Runs linting and test suites
2. **Release Detection** - Analyzes commits since last release using Release Please
3. **Changelog Generation** - Creates comprehensive changelog based on commit history
4. **Tag and Release Creation** - Creates GitHub tag and release with generated changelog
5. **Version Update** - Automatically updates `VERSION` file and package metadata

**Outputs:**
- Semantic version tag (e.g., `v1.1.0`)
- GitHub Release with changelog
- Updated `VERSION` file
- Updated `package/openwrt-captive-monitor/Makefile`

### 2. Build and Release Package Workflow

**Triggers:** On push of version tag (`v*`) - automatically triggered after Release Please

**Steps:**
1. **SDK Cache** - Downloads and caches OpenWrt SDK (reused across builds)
2. **Package Build** - Compiles the OpenWrt package
3. **Validation** - Verifies the built IPK package
4. **OIDC Federation** - Requests a GitHub-issued OIDC token and (optionally) assumes a cloud provider role for external storage
5. **Sigstore Signing & Provenance** - Produces checksums, provenance manifest, and Cosign signatures/certificates for every artifact
6. **GitHub Release Upload** - Attaches packages, logs, provenance, checksums, and signatures to the release

**Outputs:**
- Signed IPK package
- Build logs
- Checksums (SHA256SUMS)
- Signatures, certificates, and Sigstore bundles (`.sig`, `.pem`, `.sigstore`)
- Provenance manifest (`.provenance.json`)

### 3. CI Workflow (Continuous Integration)

**Triggers:** On push to feature branches, pull requests, or manual trigger

**Steps:**
1. **Linting** - Validates shell scripts, Markdown, and GitHub Actions workflows
2. **Testing** - Runs unit tests using BusyBox ash shell

**Note:** This workflow does NOT build the package. Package building only occurs on version tags.

## Release Pipeline Sequence

```
┌─────────────────────────────────────────────────────────┐
│ Developer pushes commits to main branch                 │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────┐
        │  Release Please Workflow │
        │  - Run CI checks         │
        │  - Detect version bump   │
        │  - Create tag + release  │
        │  - Update VERSION file   │
        └──────────────┬───────────┘
                       │
                       ▼ (Tag pushed automatically)
        ┌──────────────────────────┐
        │ Build & Release Workflow │
        │  - Build OpenWrt package │
        │  - Sign artifacts        │
        │  - Upload to release     │
        │  - Create checksums      │
        └──────────────┬───────────┘
                       │
                       ▼
        ┌──────────────────────────┐
        │   Release Published      │
        │   Ready for distribution │
        └──────────────────────────┘
```

### Verifying Signed Releases

Downstream consumers can verify every release artifact without relying on long-lived maintainer keys.
Sigstore certificates embed the repository, workflow, and tag that produced the build.

1. Install [Cosign](https://docs.sigstore.dev/cosign/installation/) locally.
2. Download the desired assets from the GitHub release, e.g. `openwrt-captive-monitor_1.2.3_all.ipk`, the matching `.sig`/`.pem` files, `SHA256SUMS`, and `openwrt-captive-monitor_1.2.3_all.ipk.provenance.json`.
3. Verify the detached signature for the package:

   ```bash
   cosign verify-blob \
     --certificate openwrt-captive-monitor_1.2.3_all.ipk.pem \
     --signature openwrt-captive-monitor_1.2.3_all.ipk.sig \
     --certificate-identity-regexp "https://github.com/nagual2/openwrt-captive-monitor/.github/workflows/tag-build-release.yml@.*" \
     --certificate-oidc-issuer https://token.actions.githubusercontent.com \
     openwrt-captive-monitor_1.2.3_all.ipk
   ```

4. Verify the provenance manifest with the same identity constraint:

   ```bash
   cosign verify-blob \
     --certificate openwrt-captive-monitor_1.2.3_all.ipk.provenance.json.pem \
     --signature openwrt-captive-monitor_1.2.3_all.ipk.provenance.json.sig \
     --certificate-identity-regexp "https://github.com/nagual2/openwrt-captive-monitor/.github/workflows/tag-build-release.yml@.*" \
     --certificate-oidc-issuer https://token.actions.githubusercontent.com \
     openwrt-captive-monitor_1.2.3_all.ipk.provenance.json
   ```

5. Cross-check integrity with the published checksums:

   ```bash
   sha256sum --check SHA256SUMS
   ```

Successful verification confirms the binary, checksums, and provenance were produced on GitHub Actions
by the `tag-build-release.yml` workflow for the referenced tag.

## Manual Release Triggers

### Triggering a Release Manually

You can manually trigger the Release Please workflow if needed:

```bash
gh workflow run release-please.yml --repo nagual2/openwrt-captive-monitor
```

Or through the GitHub UI:
1. Go to **Actions** → **Release Please**
2. Click **Run workflow** button
3. Select branch and options
4. Click **Run workflow**

### Building for a Specific Tag

To manually trigger a build for an existing tag:

```bash
gh workflow run tag-build-release.yml -f tag=v1.0.0 --repo nagual2/openwrt-captive-monitor
```

Or through the UI:
1. Go to **Actions** → **Build and Release Package**
2. Click **Run workflow**
3. Enter the tag name (e.g., `v1.0.0`)
4. Click **Run workflow**

## Hotfix Releases

For emergency hotfixes to the current release, follow this process:

### 1. Create a Hotfix Branch

```bash
git checkout main
git pull origin main
git checkout -b hotfix/issue-description
```

### 2. Make and Commit Your Fix

```bash
# Make your fix
git add .
git commit -m "fix: critical issue with X

This hotfix addresses a critical production issue."
```

### 3. Create a Pull Request

```bash
git push origin hotfix/issue-description
# Open PR on GitHub
```

### 4. Merge to Main

After PR approval and CI passes:
```bash
# PR is merged to main via GitHub UI
# This automatically triggers the release workflow
```

### 5. Monitor the Releases

Check the **Actions** tab to verify:
- Release Please creates the hotfix tag
- Build workflow completes successfully
- Artifacts are published to the release

## Version Metadata

The following files are automatically updated with version information:

### VERSION File
- Path: `/VERSION`
- Format: `MAJOR.MINOR.PATCH` (e.g., `1.2.3`)
- Updated by: Release Please workflow

### Package Makefile
- Path: `/package/openwrt-captive-monitor/Makefile`
- Fields updated:
  - `PKG_VERSION`: Set to the semantic version
  - `PKG_RELEASE`: Reset to `1` for new versions
- Updated by: Release Please workflow

## Release Configuration

The release process is configured via:

### `.release-please-config.json`
Main configuration for Release Please action:
- Changelog sections and formatting
- Pre-release settings
- Version bumping rules

### `.release-please-manifest.json`
Tracks the latest version for each package/component:
- Used as source of truth for version detection
- Automatically updated by Release Please

## OIDC Federation & Cloud Integrations

The release workflows authenticate with GitHub's OIDC provider to mint short-lived tokens for Cosign
and (optionally) assume cloud roles for external artifact storage.

### Provider trust policy (AWS example)

1. Create or update an AWS IAM role dedicated to release publishing.
2. Attach a trust policy that allows GitHub Actions from this repository to assume the role via OIDC.
3. Restrict the policy to the environments you expect (e.g., only tags) to prevent privilege escalation.

Example trust policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:nagual2/openwrt-captive-monitor:ref:refs/tags/*"
        }
      }
    }
  ]
}
```

Adjust the AWS account ID, `aud` claim, and `sub` pattern to match your release strategy. You can
further scope access by requiring a GitHub environment (e.g. `environment:production`).

### Repository secrets and variables

| Name | Type | Purpose |
| --- | --- | --- |
| `RELEASE_OIDC_ROLE_ARN` | Actions secret | ARN of the OIDC-enabled cloud role to assume (optional). |
| `RELEASE_OIDC_AUDIENCE` | Actions secret | Overrides the OIDC audience when assuming a role (defaults to `sts.amazonaws.com`). |
| `RELEASE_AWS_REGION` | Actions secret | Sets `AWS_DEFAULT_REGION` for downstream tooling (optional). |
| `RELEASE_CLOUD_PROVIDER` | Actions secret | Switches the provider used by `.github/actions/oidc-assume-role` (defaults to `aws`). |
| `RELEASE_OIDC_SESSION_DURATION` | Actions variable | Overrides the temporary credential lifetime (seconds). |

To enable external publishing, define the secrets above and the `sign-and-publish` job will execute
`./.github/actions/oidc-assume-role` before signing. When unused, the step is skipped automatically.

### Credential rotation guidance

Because keyless signing relies on ephemeral certificates, there are no signing keys to rotate.
If you previously stored static cloud credentials, delete them from repository secrets once OIDC
federation is configured. When you need to rotate access, update the cloud-side trust policy or
replace the target role ARN—no workflow changes are required.

OIDC step logs include the issuer, subject, and audience that were minted, providing an auditable
trail each time the workflow runs.

## Troubleshooting

### Release Please Workflow Fails

**Symptoms:** Release Please workflow fails in the Actions tab

**Common Causes:**
- CI checks failed (lint/test)
- Invalid commit history format
- Permission issues with token

**Resolution:**
1. Check workflow logs for specific error
2. Fix issues (e.g., failing tests)
3. Push fixes to main
4. Manually trigger workflow again

### Build Workflow Fails

**Symptoms:** Tag is created but build workflow fails

**Common Causes:**
- SDK download timeout
- Build environment issues
- Missing dependencies

**Resolution:**
1. Check build logs in Actions tab
2. Review SDK download errors
3. Retry the build workflow manually
4. If persistent, open an issue with logs

### Missing IPK in Release

**Symptoms:** Release created but no IPK package attached

**Common Causes:**
- Build step failed but didn't stop workflow
- Artifact upload permissions issue
- Signing step failed

**Resolution:**
1. Check build logs for errors
2. Verify GitHub token permissions
3. Re-run the build workflow

### Emergency Override

If the automated release process fails critically and you need to publish immediately:

```bash
# 1. Create tag manually
git tag -a v1.2.3 -m "Release version 1.2.3"
git push origin v1.2.3

# 2. Let the build workflow trigger and complete
# OR manually trigger it via Actions tab

# 3. Upload artifacts manually if needed
gh release upload v1.2.3 ./path/to/artifacts/*
```

## Branch Protection Integration

The repository enforces branch protection rules that coordinate with the release workflows:

- **Require CI checks to pass:** Lint and Test jobs must pass before merge
- **Require branches to be up to date:** Branches must be up-to-date with main
- **Require pull request reviews:** At least one approval required
- **Dismiss stale reviews:** Pull request reviews are reset when commits are pushed
- **Require status checks to pass before merging:** All required checks must pass

These rules ensure code quality before version bumps and release creation.

## Best Practices

1. **Use Conventional Commits:** Always use the conventional commit format to enable automatic version detection
2. **Keep Commits Atomic:** Each commit should represent one logical change
3. **Write Descriptive Messages:** Clear commit messages help generate better changelogs
4. **Review Release Notes:** Check the generated changelog for accuracy before merging
5. **Test Before Merge:** Ensure all CI checks pass before merging to main
6. **Monitor Releases:** Watch the Actions tab to verify release completion

## Advanced Configuration

To modify release behavior, edit `.release-please-config.json`:

```json
{
  "changelog-sections": [
    {"type": "feat", "section": "Features", "hidden": false},
    {"type": "fix", "section": "Bug Fixes", "hidden": false}
  ],
  "bump-minor-pre-major": true,
  "always-link-issues": true,
  "draft": false,
  "prerelease": false
}
```

## Support

For issues or questions about the release process:

1. Check this documentation
2. Review recent release logs in Actions tab
3. Open an issue with workflow logs and error messages
4. Contact the maintainers

---

**Last Updated:** November 2024
**Release Process Version:** 2.0 (Semantic Versioning + Automated)
