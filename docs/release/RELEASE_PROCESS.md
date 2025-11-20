# Release Process Documentation

> **2025 Update (Canonical):** The active release process now uses **date-based versioning** (`vYYYY.M.D.N`) and an automatic metadata sync workflow. This section describes the **current, canonical** process. The later sections remain as **archival documentation** of the previous Release Please + semantic versioning setup.

## Overview (2025+ Date-Based Workflow)

The project now uses a **date-based auto-versioning workflow** to manage releases:

- Each push to `main` triggers the `Auto Version Tag and Release` workflow.
- The workflow computes the next date-based version `vYYYY.M.D.N`.
- A helper script updates version metadata so that:
  - The root `VERSION` file is set to `YYYY.M.D.N`.
  - `PKG_VERSION` in `package/openwrt-captive-monitor/Makefile` is set to `YYYY.M.D.N`.
  - `PKG_RELEASE` is set to `1` for each new `PKG_VERSION`.
- The workflow then creates an annotated tag and GitHub Release for `vYYYY.M.D.N`.

Release builds are performed by the **tag-based build workflow** (`tag-build-release.yml`), which validates that:

- The Git tag name (without the leading `v`) matches the `VERSION` file.
- The `VERSION` file matches `PKG_VERSION` in the package `Makefile`.
- `PKG_RELEASE` in the package `Makefile` is a small numeric integer (`^[0-9]+$`) and does **not** look like a date stamp.

If any of these invariants are violated, the tagged build fails, preventing a broken release from being published.

---

## Canonical Date-Based Release Steps

1. Ensure all required CI checks pass for your pull request.
2. Merge the PR into `main` (squash merge is recommended).
3. Wait for the **Auto Version Tag and Release** workflow to run:
   - It determines the next `vYYYY.M.D.N` tag.
   - It updates `VERSION`, `PKG_VERSION`, and `PKG_RELEASE` (`1`).
   - It creates or updates the corresponding GitHub Release with notes.
4. The **tag-build-release** workflow runs on that tag and:
   - Validates the version metadata invariants described above.
   - Builds and signs the IPK packages.
   - Uploads IPK files and `SHA256SUMS` to the GitHub Release.

### Verifying a Release Before Publishing

Before you announce or depend on a release, verify:

1. The tag name matches the contents of the `VERSION` file (e.g., tag `v2025.11.20.2` → `VERSION` file contains exactly `2025.11.20.2`).
2. The package `Makefile` contains values consistent with the tag:
   - `PKG_VERSION:=2025.11.20.2`
   - `PKG_RELEASE:=1` (or another small integer such as `2`, `3` if packaging-only fixes were made)
3. The release assets on GitHub contain IPK files whose internal `Version` control field reflects `PKG_VERSION-PKG_RELEASE` (e.g., `2025.11.20.2-1`).

For detailed CI wiring, see:
- [`AUTO_VERSION_TAG.md`](./AUTO_VERSION_TAG.md) – auto-tag workflow
- [`AUTO_VERSION_MIGRATION.md`](../AUTO_VERSION_MIGRATION.md) – migration notes
- [`CI_STATUS_REPORT.md`](../ci/CI_STATUS_REPORT.md) – overview of workflows

---

## Archival: Previous Semantic Versioning / Release Please Workflow

> **Note:** The content below describes the historical **Release Please + semantic versioning** process and is kept only as a reference for older tags and reports.

## Overview (Legacy Semantic Versioning)

This project historically used **automated semantic versioning** with GitHub Actions to manage releases. The process was completely automated when code was merged to the `main` branch, following the [Semantic Versioning 2.0.0](https://semver.org/) specification.

## Branch Protection and Security Requirements

Before any code can be merged to `main` and trigger the automated release process, it **must pass all branch protection checks**. This ensures that only high-quality, secure code reaches production releases.

### Merge Prerequisites

To merge a pull request to `main`, you must satisfy these requirements:

1. **Code Review**: Obtain at least one approval from a repository maintainer
2. **All Status Checks Pass**: Every status check must pass before merging:
   - **CI/Linting**: `Lint (shfmt)`, `Lint (shellcheck)`, `Lint (markdownlint)`, `Lint (actionlint)`, `Test`
   - **Security Scans**: `ShellCheck Security Analysis`, `Dependency Review`, `Trivy Security Scan`
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

## Semantic Versioning (Legacy)

The project previously used semantic versioning in the format: `MAJOR.MINOR.PATCH`.

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

## Automated Release Workflow (Legacy)

The historical semantic-versioning-based release process was fully automated and consisted of three main workflows:

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
- Release metadata summary (`release-metadata.json`)

All artifacts are staged under `release-artifacts/<tag>/` within the workflow before signing and publication, providing clear traceability for each release iteration.

### 3. CI Workflow (Continuous Integration)

**Triggers:**
- On push to main
- On pull requests targeting main
- Manual trigger via workflow_dispatch

**Steps:**
1. **Linting** - Validates shell scripts, Markdown, and GitHub Actions workflows
2. **Testing** - Runs unit tests using BusyBox ash shell
3. **Dev Package Build** - On pull requests and pushes to main, builds development packages using the OpenWrt SDK (via `openwrt/gh-action-sdk@v6`) and uploads them as CI artifacts

Channel behavior and naming:
- Main branch builds set environment flags:
  - BUILD_CHANNEL=dev
  - BUILD_NAME=dev-main
- Packages are built inside the OpenWrt SDK using `./scripts/feeds update -a && ./scripts/feeds install <pkg>` followed by `make package/<pkg>/compile V=s`.
- Dev artifacts are staged under `artifacts/dev-main/` from SDK outputs in `bin/packages/<target>/**`.
- To avoid mutating upstream PKG_VERSION, the "dev" identifier is applied at the artifact level. The uploaded artifact name includes the short SHA (e.g., `openwrt-dev-package-dev+<short-sha>-<target>`), while the `.ipk` filenames remain in the standard `<PKG_VERSION>-<PKG_RELEASE>` format produced by the SDK.

Release packaging remains tag-driven:
- The Build and Release workflow runs on tags (vX.Y.Z) and sets:
  - BUILD_CHANNEL=release
  - BUILD_NAME=release
- Release artifacts are staged under `artifacts/release/` and attached to the GitHub Release, with clean filenames (no "dev" suffix), e.g.:
  `openwrt-captive-monitor_<VERSION>_<arch>.ipk`

## SDK-Based CI Build and Versioning

This project uses the **OpenWrt SDK** (similar to official OpenWrt packages like Luci) to build development and release packages. This section clarifies how versioning and artifacts are handled across different CI build contexts.

### OpenWrt SDK Integration

The CI pipeline leverages the OpenWrt SDK for consistent, reproducible package builds:

- **SDK Container**: Builds use the official OpenWrt SDK Docker image via `openwrt/gh-action-sdk@v6`
- **Local Feed**: The package is provided as a local feed (FEEDNAME=local) mounted to the SDK environment
- **Build Command**: Packages are compiled using standard OpenWrt build commands: `./scripts/feeds update -a && ./scripts/feeds install <pkg>` followed by `make package/<pkg>/compile V=s`
- **Multiple Targets**: CI validates builds across multiple target architectures (x86_64, ath79, ramips, mediatek, ipq40xx, ipq806x, bcm27xx, rockchip)

### Development Build Versioning (Main Branch)

When code is pushed to the `main` branch, the CI workflow performs development builds with the following versioning behavior:

**Version Field (PKG_VERSION):**
- The package `Makefile` contains the base version (e.g., `1.0.8`)
- When `DEV_SUFFIX=1` is set by CI, the build appends `-dev` to `PKG_VERSION`
- Final version string in the `.ipk` control metadata: `1.0.8-dev` or `1.0.8-dev-<date>` format

**Release Field (PKG_RELEASE):**
- Remains date-based and untouched: formats like `20240101` (YYYYMMDD) or `202401011530` (YYYYMMDDHHMM)
- No modification by the CI build process

**Artifact Naming:**
- Uploaded CI artifacts include a dev identifier and short commit SHA: `captive-monitor-<target>-dev+<shortsha>`
- Individual `.ipk` filenames within the artifact follow standard format: `openwrt-captive-monitor_1.0.8-dev_*.ipk`
- Artifacts are staged under `artifacts/dev-main/` and available as GitHub Actions artifacts for 7 days

### Pull Request Build Versioning (PR Builds)

Pull request builds validate changes without modifying version metadata:

**Version Field (PKG_VERSION):**
- No `-dev` suffix is appended (DEV_SUFFIX=0)
- Version remains as specified in the package `Makefile` (e.g., `1.0.8`)

**Release Field (PKG_RELEASE):**
- Date-based, consistent with main branch builds

**Artifact Naming:**
- Uploaded CI artifacts use the pattern: `captive-monitor-<target>-pr+<shortsha>`
- Artifacts are staged under `artifacts/pr-build/` for validation

### Version Validation

The CI pipeline includes automated validation (`scripts/validate-ipk-version.sh`) that enforces versioning rules:

- **Main branch** (default): Package `.ipk` files must include `-dev` in their Version field
- **Pull requests**: Package `.ipk` files must NOT include `-dev`
- **Validation failure** halts the build and reports the mismatch

This prevents accidental release of development versions and ensures correct labeling.

### Release Workflow (Unchanged)

The release process for tagged versions (vX.Y.Z) remains unchanged:

- **Tag builds** trigger the `tag-build-release` workflow
- **Release artifacts** have clean filenames without `-dev` suffix
- **PKG_VERSION and PKG_RELEASE** are exactly as specified in the package `Makefile`
- **Release channel**: Set to `BUILD_CHANNEL=release` and `BUILD_NAME=release`
- All release artifacts are signed and published to the GitHub Release

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
