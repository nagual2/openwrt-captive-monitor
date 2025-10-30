# CI Notes

## 2024-10-24

- Updated the lint workflow to run on pushes and pull requests targeting `main` or `feature/*` branches, and to gather shell targets once for both `shfmt` and `shellcheck`.
- Pinned all referenced GitHub Actions to explicit patch versions and ensured package installs run in non-interactive mode.
- Standardised shell formatting configuration via `.editorconfig` and `.shfmt.conf`, and applied guarded `pipefail` handling in project shell scripts for BusyBox compatibility.
- Extended the build workflow triggers to cover `feature/*` branches, set package installs to non-interactive mode, and pinned all artifact-related actions used for builds and releases.
- Required status checks for GitHub branches must be enabled manually in the repository settings (not configurable from CI code).
