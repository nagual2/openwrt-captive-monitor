# Changelog

## v0.1.4 (Unreleased)

### Packaging & Distribution
- **Refreshed packaging metadata** to align with current OpenWrt packaging guidelines
- Updated maintainer contact to team-based identifier with proper URL format
- Added `PKG_LICENSE_FILES`, `PKG_SOURCE_URL`, `PKG_SOURCE_PROTO`, and `PKG_SOURCE_VERSION` fields
- Enhanced package categorization with `SUBMENU:=Captive Portals` for better discoverability
- Updated `Makefile.template` with current OpenWrt packaging best practices

### Build Tooling
- **Enhanced `scripts/build_ipk.sh`** with maintainer-configurable metadata support:
  - `--maintainer` and `--maintainer-email` options for overriding maintainer information
  - `--spdx-id` option for custom SPDX license identifiers
  - `--release-mode` flag for publication-ready artifact generation
- **Release mode features**:
  - Detailed checksum summaries (MD5, SHA256) for all artifacts
  - JSON metadata output for release automation
  - Semantic version-based artifact naming
  - OPKG feed setup instructions

### Documentation
- **New `docs/packaging.md`** comprehensive guide covering:
  - Local development builds and custom builds
  - CI/CD integration and release workflow
  - Custom OPKG feed setup (local and GitHub Pages)
  - Automated distribution and release scripts
  - Package signing and quality assurance
- Updated documentation navigation in `mkdocs.yml` to include packaging guide
- Enhanced build script help documentation with all new options

### Version Mapping & Release Automation
- **Semantic version mapping**: Package versions now follow `vX.Y.Z` tag mapping to `PKG_VERSION`
- **Release workflow**: Documented automated release process with artifact generation
- **Feed structure**: Standardized OPKG feed layout with `Packages`, `Packages.gz`, and JSON metadata
- **Checksum automation**: Built-in checksum generation for release verification

## v0.1.3

### Packaging & QA
- Bump the OpenWrt package version to `0.1.3` and keep the release scoped to a single `PKG_RELEASE`.
- Extend the BusyBox test harness with an integration test for `scripts/build_ipk.sh` to make sure the `.ipk` payload ships the expected init script, config, and uci-defaults files.
- Confirm package metadata (control fields, dependencies, conffiles) via automated assertions to guard future regressions.

### Documentation
- Refresh the release checklist and contributing guide with the updated tag/version flow and instructions for running the quick `.ipk` builder.
- Document download & installation steps for GitHub releases in the README and add dedicated v0.1.3 release notes under `docs/releases/`.

## v0.1.2

### Documentation & Reporting
- Add comprehensive PROJECT_COMMIT_REPORT.md with detailed analysis of all 59 commits
- Enhanced project documentation with complete commit history and categorization
- Improved README with better contribution guidelines and project overview

### Code Quality & CI/CD
- All shell scripts pass shellcheck validation without errors
- Enhanced GitHub Actions workflows with improved reliability
- Better POSIX compatibility across all shell scripts
- Improved workflow file detection and validation processes
- **Fixed OpenWrt SDK version compatibility** (updated to 23.05.5)

### Bug Fixes
- Fixed all shellcheck warnings and compatibility issues
- Enhanced shell script syntax validation
- **Fixed GitHub Actions SDK download issues**
- Improved project maintainability with better documentation

## v0.1.1

### Packaging & CI
- Bump package metadata to `v0.1.1` and ensure the GitHub Actions SDK build
  enables target-specific package compilation via `defconfig`.
- Keep opkg feed indexes (`Packages`, `Packages.gz`) in the release artifacts for
  ath79/generic and ramips/mt7621 matrices.

### Documentation
- Refresh release references for `v0.1.1`, including the runbook and README
  pointers.

## v0.1.0

### Highlights
- First public release of `openwrt-captive-monitor` packaged for OpenWrt.
- Captive portal detection with automated DNS and HTTP interception for LAN clients.
- Seamless cleanup once internet access is restored, including dnsmasq overrides,
  NAT rules, and temporary HTTP server assets.

### Networking & Compatibility
- Support for both `iptables` and `nftables` firewalls, including IPv4/IPv6 NAT
  redirect rules and safe teardown.
- WiFi recovery helpers that recycle the logical or physical STA interface when
  captive checks repeatedly fail.
- BusyBox `ash`-compatible scripting style validated with ShellCheck to avoid
  POSIX regressions on OpenWrt targets.

### Packaging & Tooling
- OpenWrt package layout with `/usr/sbin`, `/etc/init.d`, `/etc/config`, and
  `uci-defaults` assets wired for procd service management.
- GitHub Actions workflows covering ShellCheck linting plus matrix builds
  against official OpenWrt SDKs to produce `.ipk` artifacts and feed indexes.
- `scripts/build_ipk.sh` helper to assemble release-ready `.ipk` packages along
  with `Packages`/`Packages.gz` indexes for publishing custom opkg feeds.
