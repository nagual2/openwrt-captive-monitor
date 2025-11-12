# CI Notes

## 2025-XX-XX - CI Workflow Simplification

- **Simplified SDK workflow**: Restructured `.github/workflows/ci.yml` to follow documented OpenWrt SDK workflow - removed `make distclean` and `make toolchain/install` steps, relying on SDK's prebuilt toolchain.
- **Removed redundant workflows**: Deleted `.github/workflows/build.yml` and `.github/workflows/build-openwrt-package.yml` to eliminate duplication.
- **Single clear pipeline**: Unified workflow now follows lint → test → SDK build → artifact upload pattern.
- **Faster builds**: Build time reduced from ~30-40 minutes to ~15-20 minutes (or 5-10 with cache) by avoiding unnecessary toolchain compilation.
- **Release integration**: Added automatic artifact attachment to GitHub releases on tag pushes using `softprops/action-gh-release@v2`.
- **Updated documentation**: Updated README badges, release checklist, packaging guide, and SDK build workflow guide to reference new simplified pipeline.

## 2025-01-30 - CI Consolidation and Release Automation

- **Consolidated CI workflows**: Merged separate lint and test workflows into a single `.github/workflows/ci.yml` with matrix strategy for parallel execution of shfmt and shellcheck.
- **Enhanced packaging workflow**: Updated `openwrt-build.yml` to consume CI results, added matrix builds for primary OpenWrt targets (generic, x86-64, armvirt-64, mips_24kc), implemented concurrency controls, and tuned artifact retention to 30 days.
- **Automated release management**: Integrated `release-please` for semantic versioning, changelog generation, and GitHub releases. The workflow automatically creates release PRs and updates package versions.
- **Dependency management**: Added `.github/dependabot.yml` to keep GitHub Actions dependencies up to date with weekly scheduled updates and automatic PR creation.
- **Streamlined linting**: Focused on essential shell script quality checks with shfmt and shellcheck for OpenWrt compatibility.
- **Improved caching**: Enhanced apt package caching across workflows to reduce build times.
- **Separate release job**: Isolated release asset publishing into a dedicated job that runs only on tags, improving workflow clarity.

## 2025-01-30 - Release Please Permissions Fix

- **Enhanced workflow permissions**: Added explicit `actions: read` and `checks: write` permissions to release-please workflow to ensure proper token access.
- **PAT token fallback**: Added configuration comments and documentation for using Personal Access Token as fallback when GitHub Actions permissions are restricted.
- **Troubleshooting documentation**: Created comprehensive troubleshooting guide in `RELEASE_PLEASE_TROUBLESHOOTING.md` for common permission issues and solutions.
- **Repository settings guidance**: Documented required GitHub repository settings for enabling GitHub Actions PR creation.

## 2024-10-24

- Updated the lint workflow to run on pushes and pull requests targeting `main` or `feature/*` branches, and to gather shell targets once for both `shfmt` and `shellcheck`.
- Pinned all referenced GitHub Actions to explicit patch versions and ensured package installs run in non-interactive mode.
- Standardised shell formatting configuration via `.editorconfig` and `.shfmt.conf`, and applied guarded `pipefail` handling in project shell scripts for BusyBox compatibility.
- Extended the build workflow triggers to cover `feature/*` branches, set package installs to non-interactive mode, and pinned all artifact-related actions used for builds and releases.
- Required status checks for GitHub branches must be enabled manually in the repository settings (not configurable from CI code).
