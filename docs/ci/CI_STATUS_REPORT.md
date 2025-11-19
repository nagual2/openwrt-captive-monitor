# GitHub Actions CI Status Report

Repository: `openwrt-captive-monitor`  
Scope date: static analysis of workflows and scripts in this branch (no GitHub UI data)

---

## 1. Summary

The repository has a mature GitHub Actions setup with:

- A primary **CI workflow (`ci.yml`)** that runs linting, tests, and OpenWrt SDK-based package builds for both `main` and pull requests.
- A dedicated **security scanning workflow (`security-scanning.yml`)** that provides ShellCheck-based security analysis, Trivy vulnerability scanning, and GitHub Dependency Review integration.
- A **release automation chain** built around:
  - `release-please.yml` (automated release PRs and tags),
  - `auto-version-tag.yml` (date-based tag and release generation), and
  - `tag-build-release.yml` (SDK-based tagged builds, signing, and release asset publishing).
- Additional **support workflows**:
  - `upload-sdk-to-release.yml` to mirror OpenWrt SDK tarballs into GitHub Releases,
  - `build-simple.yml` for host-side `opkg`-based builds, and
  - `cleanup.yml` for scheduled cleanup of artifacts and workflow runs.

Branch protection required checks are all backed by explicit workflow jobs:

- `Lint (shfmt)`, `Lint (shellcheck)`, `Lint (markdownlint)`, `Lint (actionlint)`, and `Test` come from `ci.yml`.
- `ShellCheck Security Analysis`, `Dependency Review`, and `Trivy Security Scan` come from `security-scanning.yml`.

Non-release CI builds use the **OpenWrt SDK Docker images** via `openwrt/gh-action-sdk@v9`, with fail-fast validation using `scripts/validate-sdk-image.sh`. Release builds for tags use an **SDK tarball** validated by `scripts/validate-sdk-image.sh` and `scripts/validate-sdk-url.sh`. IPK version metadata for dev and PR builds is enforced by `scripts/validate-ipk-version.sh`, and all non-release IPKs are staged via `scripts/stage-package-artifacts.sh` into a standard `package/` directory with `SHA256SUMS`.

Key static risks are primarily around **hard-coded SDK versions and filenames**, **assumptions about Ubuntu 24.04 package availability**, and **tight coupling between branch type and IPK version suffix rules**. These are reasonable trade-offs but should be revisited when upgrading OpenWrt versions or runners.

---

## 2. Workflow Inventory

### 2.1 Inventory Table

| Workflow file | Workflow name | Events / filters | Main jobs | Primary purpose |
|---------------|--------------|------------------|-----------|-----------------|
| `.github/workflows/ci.yml` | **CI** | `push` (branches: `main`), `pull_request` (branches: `main`), `workflow_dispatch` | `lint`, `test`, `build-dev-package`, `build-pr-package` | Core CI: linting, testing, and multi-target OpenWrt SDK package builds for dev and PR channels. |
| `.github/workflows/security-scanning.yml` | **Security Scanning** | `push` (branches: `main`), `pull_request` (branches: `main`), `schedule` (weekly Tue 00:00 UTC), `workflow_dispatch` | `dependency-review`, `trivy-scan`, `shellcheck-security`, `security-summary` | Security-focused checks (dependency review, Trivy scan, ShellCheck SARIF) with summary. |
| `.github/workflows/tag-build-release.yml` | **Build and Release Package** | `push` (tags: `v*`), `workflow_dispatch` (manual `tag` input) | `pre-check`, `build-package`, `sign-and-publish` | Tagged release build: build with SDK tarball, validate IPKs, sign artifacts (cosign), and publish to GitHub Release. |
| `.github/workflows/release-please.yml` | **Release Please** | `push` (branches: `main`), `workflow_dispatch` (`prerelease` input) | `lint`, `test`, `release-please`, `update-version`, `publish-release` | Automates release PRs/tags via release-please, updates version metadata, and triggers the tag-based build pipeline. |
| `.github/workflows/auto-version-tag.yml` | **Auto Version Tag and Release** | `push` (branches: `main`) | `tag-and-release` | Generates date-based semantic tags (`vYYYY.M.D.N`), creates corresponding GitHub releases with notes. |
| `.github/workflows/build-simple.yml` | **Simple Build** | `push` (tags: `v*`), `workflow_dispatch` (manual `tag` input) | `build` | Host-side `opkg` packaging using `scripts/build_ipk.sh` and `scripts/setup-opkg-utils.sh` (no SDK). Primarily a simplified/manual build path. |
| `.github/workflows/upload-sdk-to-release.yml` | **Upload SDK to GitHub Release** | `workflow_dispatch` (`sdk_version`, `force_update` inputs) | `upload-sdk` | Downloads an official OpenWrt SDK tarball, validates its availability, and mirrors it into a GitHub Release for faster CI reuse. |
| `.github/workflows/cleanup.yml` | **Cleanup Artifacts and Runs** | `schedule` (daily at 03:00 UTC), `workflow_dispatch` (`force` input) | `cleanup` | Deletes old Actions artifacts and workflow runs according to retention thresholds; supports a manual “force delete all artifacts” mode. |

> **Paths:** None of the workflows currently use `paths`/`paths-ignore` filters; triggers apply to all file changes for the configured branches/tags.

### 2.2 Per-workflow Notes

#### `.github/workflows/ci.yml` – CI

- **Lint job (`lint`)**
  - Matrix over `linter: [shfmt, shellcheck, markdownlint, actionlint, yamllint]`.
  - Uses the local composite action `./.github/actions/setup-system-packages` to install system dependencies with retries.
  - Uses Node.js 20 (`actions/setup-node@v6`) for Node-based tooling (markdownlint, actionlint wrapper) and general parity.
  - Linters:
    - `shfmt`: `shfmt -d -s -i 4 -ci -sr .`
    - `shellcheck`: scans `*.sh` and `openwrt_captive_monitor.sh`.
    - `markdownlint`: `DavidAnson/markdownlint-cli2-action@v21` on `**/*.md`.
    - `actionlint`: `reviewdog/action-actionlint@v1`.
    - `yamllint`: only validates `.github/workflows/ci.yml` (relaxed rules), acts as a guard for CI workflow changes.

- **Test job (`test`)**
  - Needs `lint`.
  - Installs `binutils`, `tar`, `busybox` via the composite action.
  - Runs test harness via BusyBox ash: `busybox ash tests/run.sh`.
  - Uploads `tests/_out/` as `test-results` artifact.

- **SDK dev build (`build-dev-package`)** – **main branch only**
  - Condition: `if: github.event_name == 'push' && github.ref == 'refs/heads/main'` and `needs: test`.
  - Matrix over 8 OpenWrt targets, each with:
    - `openwrt_version: '23.05.3'`
    - `target`/`subtarget` (e.g., `x86/64`, `ath79/generic`, `rockchip/armv8`)
    - `arch` (e.g., `x86_64`, `ath79-generic`) and `sdk_slug` (e.g., `x86-64`)
  - Key steps:
    - Prepare a minimal local feed tree under `feed/package/openwrt-captive-monitor` and ensure `feed/feeds.conf.default` exists.
    - **Validate SDK image** using `./scripts/validate-sdk-image.sh` with container `ghcr.io/openwrt/sdk:${{ matrix.sdk_slug }}-${{ matrix.openwrt_version }}`.
    - Build via **OpenWrt SDK**: `openwrt/gh-action-sdk@v9` with:
      - `CONTAINER=ghcr.io/openwrt/sdk:${{ matrix.sdk_slug }}-${{ matrix.openwrt_version }}`
      - `PACKAGES=openwrt-captive-monitor`, `FEEDNAME=local`, `FEED_DIR=${{ github.workspace }}/feed`
      - `ARTIFACTS_DIR=${{ github.workspace }}/artifacts/dev-main`
      - `DEV_SUFFIX` propagated from the `Set DEV suffix` step (1 on `main`).
    - List and sanity-check `.ipk` artifacts under `artifacts/dev-main`.
    - Verify package internals via `./scripts/verify_package.sh`.
    - **Validate IPK version metadata** for all produced `.ipk` files: `./scripts/validate-ipk-version.sh <ipk> main`.
    - Stage artifacts into a normalized `package/` directory with `SHA256SUMS` via `./scripts/stage-package-artifacts.sh`.
    - Upload artifact named `captive-monitor-${{ matrix.sdk_target }}-dev+${{ env.SHORT_SHA }}` (e.g., `captive-monitor-x86-64-dev+a1b2c3d4`).

- **SDK PR build (`build-pr-package`)** – **pull requests only**
  - Condition: `if: github.event_name == 'pull_request'` and `needs: test`.
  - Reuses the same 8-target matrix and SDK flow as the dev build, with differences:
    - Build channel: `BUILD_CHANNEL=pr`, `BUILD_NAME=pr-build`.
    - `DEV_SUFFIX` from `Set DEV suffix` resolves to `0` for PR refs, so no `-dev` suffix inside Version.
    - **Validate IPK version metadata** with mode `pr`: `./scripts/validate-ipk-version.sh <ipk> pr` (rejects any Version including `-dev`).
    - Artifacts staged via `stage-package-artifacts.sh` and uploaded as `captive-monitor-${{ matrix.sdk_target }}-pr+${{ env.SHORT_SHA }}`.

#### `.github/workflows/security-scanning.yml` – Security Scanning

- **Dependency Review (`dependency-review`)**
  - Runs only on `pull_request` events (guarded with `if: github.event_name == 'pull_request'`).
  - Uses `actions/dependency-review-action@v4` with:
    - `fail-on-severity: moderate`
    - Denied licenses: `GPL-3.0`, `AGPL-3.0`
    - Always comments a summary on the PR.

- **Trivy Security Scan (`trivy-scan`)**
  - Runs on pushes, PRs, schedules, and manual triggers.
  - Uses `aquasecurity/trivy-action@0.33.1` in filesystem (`fs`) mode over the repo root.
  - Produces SARIF `trivy-results.sarif` and uploads it via `github/codeql-action/upload-sarif@v4` under category `trivy-scan`.
  - Uses `exit-code: '0'` so findings do not directly fail the job, but the job itself must succeed for the status check.

- **ShellCheck Security Analysis (`shellcheck-security`)**
  - Installs `shellcheck` and `jq` via `apt-get`.
  - Finds `.sh` scripts (excluding `.git/*` and `tests/*`) plus `openwrt_captive_monitor.sh` if present.
  - Runs `shellcheck --format=json` and converts JSON to SARIF using `.github/scripts/convert-to-sarif.jq`.
  - Uploads SARIF results to GitHub Security via `github/codeql-action/upload-sarif@v4` (category `shellcheck-security`).

- **Security summary (`security-summary`)**
  - Depends on the three scanners and runs `if: always()`.
  - Writes a short Markdown table to `$GITHUB_STEP_SUMMARY` listing the result of each scanner (not a required check itself).

#### `.github/workflows/tag-build-release.yml` – Build and Release Package

- **Pre-flight check (`pre-check`)**
  - Validates that the event is either a tag push (`ref_type == tag`) or a manual dispatch (with `tag` input).
  - Outputs `should_proceed` and the effective `tag_name`.

- **Build OpenWrt Package (`build-package`)**
  - Runs only if `needs.pre-check.outputs.should_proceed == 'true'`.
  - Environment is pinned to OpenWrt **23.05.2 x86/64** (`OPENWRT_VERSION=23.05.2`, `OPENWRT_ARCH=x86_64`).
  - Key steps:
    - Checkout at the requested tag.
    - Verify version consistency between the tag (`vX.Y.Z`), `VERSION` file, and `PKG_VERSION` in `package/openwrt-captive-monitor/Makefile`.
    - Install broad build dependencies via `apt-get` with retry logic; install `axel` downloader.
    - **Validate SDK Docker image** via `./scripts/validate-sdk-image.sh` for `ghcr.io/openwrt/sdk:${{ env.OPENWRT_ARCH }}-${{ env.OPENWRT_VERSION }}` and target `x86/64`.
    - **Validate SDK tarball URLs** via `./scripts/validate-sdk-url.sh $OPENWRT_VERSION x86/64 $OPENWRT_ARCH` before downloading.
    - Download the SDK tarball from a prioritized mirror list (including a GitHub-hosted mirror), verifying a pinned SHA256 checksum.
    - Locate SDK directory, copy the package into `SDK_DIR/package/openwrt-captive-monitor`, update and install feeds with robust retries, and run `make package/openwrt-captive-monitor/compile V=s`.
    - Stage artifacts using `scripts/stage_artifacts.sh` into `artifacts/${BUILD_NAME}` and derive `ipk_name`/`artifact_name` from the staged IPK.
    - Enforce that the release IPK filename does **not** contain `dev`.
    - Validate the package via `./scripts/validate_ipk.sh` and show control metadata.
    - Collect all `.ipk` files from `SDK_DIR/bin`, copy them into `package/`, and create `SHA256SUMS`; upload both `package/` and the raw artifacts as Actions artifacts.

- **Sign and Publish Release (`sign-and-publish`)**
  - Runs only if the build succeeded.
  - Optionally assumes an AWS role via `./.github/actions/oidc-assume-role` using OIDC.
  - Generates an in-toto/SLSA-style provenance JSON for the IPK, signs artifacts using **cosign** with keyless signing, verifies signatures, and uploads non-IPK artifacts plus later the `package/` IPKs and `SHA256SUMS` to the GitHub Release.
  - Updates the release body with a deterministic “Downloads” section and verifies that at least one asset exists.

#### `.github/workflows/release-please.yml` – Release Please

- **Lint & Test**
  - Duplicates the core lint and test structure from `ci.yml` (without the `yamllint` axis) for changes to `main` and manual runs.

- **Create Release (`release-please`)**
  - Runs `googleapis/release-please-action@v4` to drive release PRs and tags based on conventional commits.
  - Extracts the semantic version from the generated tag and validates that an OIDC token can be minted (basic Sigstore readiness check).

- **Update Version Metadata (`update-version`)**
  - After a release is created, checks out the repo with write access, updates:
    - `VERSION`
    - `package/openwrt-captive-monitor/Makefile` (`PKG_VERSION` and `PKG_RELEASE`),
  - Commits and pushes a `chore(release): bump version to X.Y.Z` commit.

- **Publish Release Event (`publish-release`)**
  - Emits a concise log summarizing the tag and version and points to the downstream tag-triggered build workflow (`tag-build-release.yml`).

#### `.github/workflows/auto-version-tag.yml` – Auto Version Tag and Release

- Single job **`tag-and-release`** triggered on pushes to `main`.
  - Computes a date-based tag `vYYYY.M.D.N` (`N` is sequence for that day) based on existing tags.
  - Generates simple Markdown release notes summarizing commits since the previous tag.
  - Creates an annotated tag and GitHub Release using the `gh` CLI, when they do not already exist.

#### `.github/workflows/build-simple.yml` – Simple Build

- Single job **`build`** triggered on tag pushes and manual runs.
  - Installs build toolchain and headers via `apt-get`.
  - **Uses `scripts/setup-opkg-utils.sh`** to install `opkg-build` and `opkg-make-index` correctly on Ubuntu 24.04 (instead of deprecated `apt install opkg-utils`).
  - Runs `scripts/build_ipk.sh` to perform host-side IPK packaging and opkg feed generation under `dist/opkg/$arch`.
  - Stages artifacts to `artifacts/${BUILD_NAME}` using `scripts/stage_artifacts.sh` (via the build script) and uploads them as `ipk-host-build+${SHORT_SHA}`.

#### `.github/workflows/upload-sdk-to-release.yml` – Upload SDK to GitHub Release

- Single job **`upload-sdk`**, manual only.
  - Validates `sdk_version` format (`X.Y` or `X.Y.Z`) and HEAD-checks the constructed OpenWrt SDK URL for x86/64 before downloading.
  - Downloads `openwrt-sdk-${sdk_version}-x86-64_gcc-12.3.0_musl.Linux-x86_64.tar.xz` with retry/backoff, computes its SHA256, and publishes it into a dedicated `sdk-${sdk_version}` GitHub Release (creating or updating as needed).
  - Writes a `sdk-checksum.txt` asset and verifies the resulting download URL with a `wget --spider` check.

#### `.github/workflows/cleanup.yml` – Cleanup Artifacts and Runs

- Single job **`cleanup`**, scheduled daily and manually runnable.
  - On manual runs with `inputs.force == 'true'`, deletes **all** workflow artifacts via the `gh` CLI.
  - On scheduled runs, deletes artifacts older than `ARTIFACT_RETENTION_DAYS` (default 7) via `actions/github-script@v8`.
  - Cleans up older workflow runs based on `WORKFLOW_RETENTION_DAYS` and `WORKFLOW_MINIMUM_RUNS` using the GitHub REST API.

---

## 3. Required Checks and Branch Protection Mapping

This section maps the required branch protection checks to their underlying jobs.

| Required check name (UI) | Workflow file | Job key / matrix | Job name in YAML | When it runs | What it validates |
|--------------------------|--------------|------------------|------------------|--------------|-------------------|
| **Lint (shfmt)** | `ci.yml` | `jobs.lint` with `matrix.linter: shfmt` | `name: Lint` | `push` to `main`, `pull_request` to `main`, `workflow_dispatch` | Shell script formatting via `shfmt` over the whole repo. |
| **Lint (shellcheck)** | `ci.yml` | `jobs.lint` with `matrix.linter: shellcheck` | `name: Lint` | Same as above | Static analysis of shell scripts (`*.sh` and `openwrt_captive_monitor.sh`) via `shellcheck`. |
| **Lint (markdownlint)** | `ci.yml` | `jobs.lint` with `matrix.linter: markdownlint` | `name: Lint` | Same as above | Markdown linting for `**/*.md` using `markdownlint-cli2`. |
| **Lint (actionlint)** | `ci.yml` | `jobs.lint` with `matrix.linter: actionlint` | `name: Lint` | Same as above | GitHub Actions workflow linting via `reviewdog/action-actionlint`. |
| **Test** | `ci.yml` | `jobs.test` | `name: Test` | After all lint variants pass (`needs: lint`), on `push`/`pull_request` to `main` | Executes the BusyBox-based test harness (`busybox ash tests/run.sh`), uploading test outputs. |
| **ShellCheck Security Analysis** | `security-scanning.yml` | `jobs.shellcheck-security` | `name: ShellCheck Security Analysis` | `push`/`pull_request` to `main`, scheduled weekly, manual | Security-focused ShellCheck analysis with SARIF upload to GitHub’s code scanning. |
| **Dependency Review** | `security-scanning.yml` | `jobs.dependency-review` | `name: Dependency Review` | **Only** on `pull_request` to `main` | GitHub Dependency Review: vulnerability and license checks on dependency changes; fails PRs on >= moderate severity. |
| **Trivy Security Scan** | `security-scanning.yml` | `jobs.trivy-scan` | `name: Trivy Security Scan` | `push`/`pull_request` to `main`, scheduled weekly, manual | Repo-wide vulnerability/misconfiguration scan using Trivy in filesystem mode, with SARIF upload. |

Notes:

- The `Lint` job in `ci.yml` is a matrix job; GitHub surfaces each matrix entry as a separate status such as `Lint (shfmt)`, `Lint (shellcheck)`, etc. The additional `yamllint` axis is **not** required by the project guidelines but runs as part of the same job.
- The security checks are centralized in `security-scanning.yml` and run in parallel. For PRs into `main`, all three required security checks will appear as separate statuses.

---

## 4. SDK-Related and Packaging Jobs

### 4.1 Jobs using `openwrt/gh-action-sdk`

**Workflow:** `.github/workflows/ci.yml`  
**Jobs:** `build-dev-package`, `build-pr-package`

- Both jobs invoke `openwrt/gh-action-sdk@v9` as the core SDK build step:

  ```yaml
  - name: Build with OpenWrt SDK (${{ matrix.sdk_target }})
    uses: openwrt/gh-action-sdk@v9
    env:
      CONTAINER: ghcr.io/openwrt/sdk:${{ matrix.sdk_slug }}-${{ matrix.openwrt_version }}
      PACKAGES: openwrt-captive-monitor
      ARTIFACTS_DIR: ${{ github.workspace }}/artifacts/${{ env.BUILD_NAME }}
      FEED_DIR: ${{ github.workspace }}/feed
      FEEDNAME: local
      SDK_TARGET: ${{ matrix.sdk_target }}
      ARCH: ${{ matrix.arch }}
      DEV_SUFFIX: ${{ steps.dev.outputs.DEV_SUFFIX }}
  ```

- **SDK container tag construction**
  - For each matrix entry, the container image is:
    - `CONTAINER = ghcr.io/openwrt/sdk:${sdk_slug}-${openwrt_version}`
    - Examples:
      - `ghcr.io/openwrt/sdk:x86-64-23.05.3`
      - `ghcr.io/openwrt/sdk:ath79-generic-23.05.3`
      - `ghcr.io/openwrt/sdk:rockchip-armv8-23.05.3`
  - `scripts/validate-sdk-image.sh` is called immediately before the SDK build to verify:
    - Version/target/slug formats.
    - That the container tag suffix matches `${sdk_slug}-${openwrt_version}`.
    - That the image manifest exists in GHCR (via Docker or direct registry HTTP calls with retries).

### 4.2 Jobs running `scripts/validate-sdk-image.sh` or `scripts/validate-sdk-url.sh`

- **`ci.yml` / `build-dev-package` and `build-pr-package`**
  - Step: **Validate SDK image and target**
    - Calls: `./scripts/validate-sdk-image.sh "ghcr.io/openwrt/sdk:${{ matrix.sdk_slug }}-${{ matrix.openwrt_version }}" "${{ matrix.sdk_target }}" "${{ matrix.openwrt_version }}" "${{ matrix.sdk_slug }}"`.
    - Ensures bad SDK tags/targets fail fast before invoking `openwrt/gh-action-sdk`.

- **`tag-build-release.yml` / `build-package`**
  - Step: **Validate SDK image and target**
    - Calls: `./scripts/validate-sdk-image.sh "ghcr.io/openwrt/sdk:${{ env.OPENWRT_ARCH }}-${{ env.OPENWRT_VERSION }}" "x86/64" "${{ env.OPENWRT_VERSION }}" "${{ env.OPENWRT_ARCH }}"`.
  - Step: **Validate SDK download URLs**
    - Calls: `./scripts/validate-sdk-url.sh "${{ env.OPENWRT_VERSION }}" "x86/64" "${{ env.OPENWRT_ARCH }}"`.
    - Verifies that at least one mirror (GitHub-hosted or official OpenWrt) exposes the SDK tarball via HTTP 200 before download.

- **`upload-sdk-to-release.yml`**
  - Does **not** call the shared script, but performs inline validation equivalent to `validate-sdk-url.sh`:
    - Validates the version format and checks `curl --head` response for HTTP 200 for the constructed SDK URL.

### 4.3 Jobs running `scripts/validate-ipk-version.sh`

All current uses are in `.github/workflows/ci.yml`:

- **`build-dev-package`** (main branch)
  - Step **"Validate IPK version metadata"**:

    ```bash
    ./scripts/validate-ipk-version.sh "$IPK_FILE" "main"
    ```

  - Enforces that the `Version` field in the IPK control file matches:
    - Pattern: `^[0-9][0-9\.]*-dev(-[0-9]{8}([0-9]{2})?)?$`
    - i.e., **must** include `-dev` suffix, with optional date-based `PKG_RELEASE` suffix.

- **`build-pr-package`** (PRs)
  - Step **"Validate IPK version metadata"**:

    ```bash
    ./scripts/validate-ipk-version.sh "$IPK_FILE" "pr"
    ```

  - Enforces that `Version` **does not** include `-dev` and matches:
    - Pattern: `^[0-9][0-9\.]*(-[0-9]{8}([0-9]{2})?)?$`.

- Both modes also validate optional PKG_RELEASE suffixes (date `YYYYMMDD` or `YYYYMMDDHHMM`) and error out on malformed values.

> Release builds in `tag-build-release.yml` use `scripts/validate_ipk.sh` (older-style structural validation) but intentionally **do not** enforce dev/PR suffix semantics.

### 4.4 Where builds are staged and how artifacts are named

- **Dev builds (main branch, `build-dev-package`)**
  - SDK artifacts directory: `artifacts/dev-main`.
  - After validation, `scripts/stage-package-artifacts.sh "artifacts/${BUILD_NAME}"` copies all `.ipk` files into a clean `package/` directory, generates `SHA256SUMS`, and lists contents.
  - Artifact name per target:
    - `captive-monitor-${{ matrix.sdk_target }}-dev+${{ env.SHORT_SHA }}`
    - Example: `captive-monitor-x86-64-dev+1a2b3c4d`.

- **PR builds (`build-pr-package`)**
  - SDK artifacts directory: `artifacts/pr-build`.
  - Same staging process to `package/` with `SHA256SUMS`.
  - Artifact name per target:
    - `captive-monitor-${{ matrix.sdk_target }}-pr+${{ env.SHORT_SHA }}`
    - Example: `captive-monitor-x86-64-pr+1a2b3c4d`.

- **Tagged release builds (`tag-build-release.yml`)**
  - SDK artifacts directory: `artifacts/${BUILD_NAME}` (where `BUILD_NAME` is "release" or a timestamp+shortSHA fallback).
  - `scripts/stage_artifacts.sh` stages SDK outputs there; later, a separate step copies all `.ipk` files under `SDK_DIR/bin` into a `package/` directory and generates `SHA256SUMS`.
  - Two artifact streams are uploaded:
    - Raw build directory: `${artifact_dir}` as `ipk-x86-64-${BUILD_NAME}`.
    - Consolidated `package/` directory as `package-${BUILD_NAME}`.
  - Release assets ultimately include individual IPKs plus `SHA256SUMS`, referenced in the release notes "Downloads" section.

- **Host-side build (`build-simple.yml`)**
  - `scripts/build_ipk.sh` writes the final IPK into `dist/opkg/$arch` and stages all relevant files into `artifacts/${BUILD_NAME}` via `scripts/stage_artifacts.sh`.
  - Uploaded artifact name: `ipk-host-build+${SHORT_SHA}`.

---

## 5. Static Risk / Fragility Analysis and Suggestions

This section highlights potential sources of CI fragility based purely on the current YAML and script implementations.

### 5.1 Hard-coded SDK versions, tags, and filenames

**Observations**

- `ci.yml` uses a hard-coded OpenWrt version `23.05.3` across all SDK-based CI builds.
- `tag-build-release.yml` uses `OPENWRT_VERSION=23.05.2` for tagged releases and encodes specific SDK tarball filenames and checksums:
  - `openwrt-sdk-${SDK_VERSION}-x86-64_gcc-12.3.0_musl.Linux-x86_64.tar.xz`.
- `upload-sdk-to-release.yml` similarly assumes the same GCC and platform string for all versions.

**Risks**

- When OpenWrt releases move forward (e.g., 24.x, 25.x) or GCC versions change, these hard-coded filenames and checksums will need manual updates; until then, CI will fail fast at validation steps.
- CI builds for development (23.05.3) and releases (23.05.2) currently diverge in base SDK version, which is acceptable but requires awareness when debugging discrepancies between CI and tagged releases.

**Suggestions**

- Centralize OpenWrt version/architecture metadata (e.g., in a small JSON/YAML file or environment section) so that updates are done in one place and consumed by both `ci.yml` and `tag-build-release.yml`.
- Document the intended version skew (if any) between dev (CI) and release builds in the release docs to avoid confusion.
- Consider adding a small script or check that verifies consistency between SDK-related variables across workflows.

### 5.2 Ubuntu 24.04 environment assumptions

**Observations**

- All workflows use `runs-on: ubuntu-24.04` and assume availability of:
  - `curl`, `wget`, `sha256sum`, `tar`, `git`, `python3`, etc. (base image tools).
  - APT packages like `shellcheck`, `jq`, `axel`, and build-essential toolchain packages.
- The repository correctly avoids `apt install opkg-utils` on Ubuntu 24.04 and instead uses `scripts/setup-opkg-utils.sh` in `build-simple.yml` to install `opkg-build` and `opkg-make-index` from upstream.

**Risks**

- If Ubuntu 24.04 updates or future runner images remove certain packages from the default repositories, direct `apt-get install` steps (especially outside the reusable `setup-system-packages` composite) may begin to fail.
- `security-scanning.yml` and `tag-build-release.yml` still contain bespoke `apt-get` logic rather than relying exclusively on `./.github/actions/setup-system-packages`, so they dont get the same retry/backoff behavior.

**Suggestions**

- Gradually migrate remaining `apt-get` sequences (particularly in `security-scanning.yml` and `tag-build-release.yml`) to use the `setup-system-packages` composite for consistent retry behavior.
- Periodically validate workflows on updated runner images (e.g., via a temporary branch) when GitHub announces base image changes.

### 5.3 Branch-coupled IPK version validation

**Observations**

- `scripts/validate-ipk-version.sh` encodes **two modes**: `main` (must have `-dev` suffix) and `pr` (must not have `-dev`).
- `ci.yml` selects modes as follows:
  - `build-dev-package` (push to `main`): invokes validation with mode `main`.
  - `build-pr-package` (pull_request events) uses mode `pr` and relies on `github.ref != 'refs/heads/main'` to set `DEV_SUFFIX=0`.

**Risks**

- If additional branches or workflows were to reuse these jobs or scripts without carefully choosing `branch_type`, they could easily mis-label packages (e.g., a long-lived release branch accidentally treated as `pr` mode).
- The logic is currently tightly bound to `main` vs. `pull_request` and assumes all non-main builds that matter are PRs.

**Suggestions**

- Keep the `validate-ipk-version.sh` entrypoints constrained to the CI jobs in `ci.yml` and avoid ad-hoc use elsewhere.
- If future workflows need dev-like builds from non-`main` branches, introduce an explicit `BUILD_CHANNEL`/`branch_type` parameter and document its mapping to `main`/`pr` semantics rather than inferring from `github.ref`.
- Optionally add a small wrapper script or step that logs which mode (`main` vs `pr`) is being used along with the originating branch/ref for easier debugging.

### 5.4 Matrix duplication and maintenance overhead

**Observations**

- The 8-target SDK matrix (targets, subtargets, arch, sdk_slug, sdk_target) is duplicated verbatim in both `build-dev-package` and `build-pr-package` within `ci.yml`.

**Risks**

- Any future change (e.g., adding/removing a target, bumping versions) must be applied in two places; omission in one job would cause dev and PR pipelines to diverge.

**Suggestions**

- Use YAML anchors/aliases within `ci.yml` to define the matrix once and reuse it (GitHub supports standard YAML features).
- Alternatively, consider a reusable workflow or job template, though for this repository anchors may be simpler and sufficient.

### 5.5 Network and external service dependencies

**Observations**

- SDK image and tarball validation scripts already implement retries and multi-mirror support.
- Feed updates in the tagged build pipeline include extensive retry logic with exponential backoff and jitter.
- Security scans (Trivy, ShellCheck SARIF upload, Dependency Review) depend on GitHub and third-party services.

**Risks**

- Despite improved resilience, prolonged outages of GHCR, OpenWrt mirrors, or GitHub Security APIs can still cause CI failures.
- The Trivy job uses `exit-code: 0`, so vulnerabilities will not fail the job, but transient runtime errors (e.g., timeouts, broken SARIF upload) still can.

**Suggestions**

- Maintain and periodically review the troubleshooting docs already present (`docs/SECURITY_SCANNING.md`, `docs/ci/CI_SDK_VALIDATION_IMPLEMENTATION.md`) to ensure they match current action versions and configuration.
- For Trivy, consider adjusting `timeout-minutes` or adding simple log markers to make transient network issues easier to identify.

### 5.6 Documentation vs. implementation drift

**Observations**

- Several documentation files (e.g., `docs/ci/CI_SDK_VALIDATION_IMPLEMENTATION.md`, `docs/SECURITY_SCANNING.md`, `docs/reports/GITHUB_ACTIONS_DIAGNOSTICS.md`) describe previous action versions and scanner configurations that have since evolved (e.g., updated action versions, Trivy scanners list, SDK tag examples).

**Risks**

- Future maintainers may be confused if docs and actual workflows diverge (e.g., docs referencing `openwrt/gh-action-sdk@v6` while CI uses `@v9`).

**Suggestions**

- Periodically regenerate or update CI-related documentation from the current YAML (either manually or via small helper scripts) to keep them in sync.
- In new documentation (including this report), always reference the **current** versions/actions and, where relevant, mention that older docs may describe legacy configurations.

---

## 6. Recommendations Summary

From the analysis above, the current GitHub Actions setup is broadly aligned with the projects CI guidelines and uses modern best practices (pinned Ubuntu runners, explicit permissions, concurrency control, SDK validation, and IPK metadata checks). To further improve robustness over time, the following incremental improvements are recommended:

1. **Centralize SDK configuration** (versions, architectures, tarball filenames/checksums) so that upgrades require fewer manual edits and reduce the risk of mismatch across workflows.
2. **Standardize on the reusable `setup-system-packages` composite** for all `apt-get` usage where practical, to maximize retry and backoff coverage.
3. **Keep IPK version validation semantics explicit and documented** wherever `scripts/validate-ipk-version.sh` is used, and avoid reusing it in new workflows without a clear mapping to `main` vs `pr` behavior.
4. **De-duplicate SDK matrices** in `ci.yml` using YAML anchors or similar patterns, reducing the chance of drift between dev and PR builds.
5. **Periodically reconcile docs with workflows**, especially for action versions, SDK tags, and scanner configurations, so onboarding contributors can rely on documentation when debugging CI issues.

This report is intended to be directly usable in PR descriptions or issues when discussing CI behavior, required checks, and future refactors of the GitHub Actions configuration.
