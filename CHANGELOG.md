# Changelog

## [1.0.0](https://github.com/nagual2/openwrt-captive-monitor/compare/v0.1.0...v1.0.0) (2025-10-30)


### ⚠ BREAKING CHANGES

* **workflows:** Old workflows and status checks are replaced; branch protection and local lint/test commands must be updated accordingly.
* **audit:** Documentation now targets OpenWrt 24.x/filogic, with adjusted requirements for formatting, firewall integration, and test plans. Some default config and workflow expectations have changed.

### Features

* **health-check:** add HTTP/HTTPS probes and exponential backoff to connectivity checks ([#25](https://github.com/nagual2/openwrt-captive-monitor/issues/25)) ([07fa174](https://github.com/nagual2/openwrt-captive-monitor/commit/07fa174ada1942bfdd1395f4f161c572118b7676))
* **minimal:** remove complex testing, keep only essential linting ([a4cf30d](https://github.com/nagual2/openwrt-captive-monitor/commit/a4cf30d0dc2f9937ef35f8f289f5dbdaca3b4918))
* **packaging:** align OpenWrt packaging, build, and docs with current best practices ([baeccf4](https://github.com/nagual2/openwrt-captive-monitor/commit/baeccf4e02898022d4532189f2bc9da89c05440b))
* **testing:** add comprehensive testing suite for remote servers ([7dacbd5](https://github.com/nagual2/openwrt-captive-monitor/commit/7dacbd5691442fc171939a7dfbeb703147d4aba7))


### Bug Fixes

* **build:** enforce .ipk artifact creation and add hard fail on missing artifacts ([ae1858c](https://github.com/nagual2/openwrt-captive-monitor/commit/ae1858c43e5317ba5a729f53d161898f6d5706da))
* **build:** improve OpenWrt SDK package compilation process ([5c66326](https://github.com/nagual2/openwrt-captive-monitor/commit/5c663268f1952304438636088d4cd6fd380d438e))
* **build:** synchronize PKG_VERSION with release branch and verify end-to-end package build ([#60](https://github.com/nagual2/openwrt-captive-monitor/issues/60)) ([a3dfc0f](https://github.com/nagual2/openwrt-captive-monitor/commit/a3dfc0fdbe6b3f073b635fa8c851343f0e4a70c7))
* **ci:** correct OpenWrt build workflow to ensure package build dir context ([e6fd6e0](https://github.com/nagual2/openwrt-captive-monitor/commit/e6fd6e0e6dd19f4f495f35b66a2c198b18d6a334))
* **ci:** harden and verify OpenWrt package workflow and docs ([7915044](https://github.com/nagual2/openwrt-captive-monitor/commit/79150446fe38c89a25b699e55ba3b70598d30630))
* **ci:** resolve OpenWrt SDK version and dependency issues ([96c5fbe](https://github.com/nagual2/openwrt-captive-monitor/commit/96c5fbe4540c4c4202950a6bedbda994ec22528f))
* **ci:** resolve shell compatibility issues in GitHub Actions ([95b39d3](https://github.com/nagual2/openwrt-captive-monitor/commit/95b39d30ba5e91afceb8c4785e3d4dbc133c4eee))
* **ci:** resolve YAML syntax errors and simplify workflow scripts ([9c3b7d5](https://github.com/nagual2/openwrt-captive-monitor/commit/9c3b7d5224dfe350ae8cfc4904b04bbe8a01dfea))
* **dns:** replace resolveip usage with nslookup/host-based DNS resolution and timeout ([6e9e72e](https://github.com/nagual2/openwrt-captive-monitor/commit/6e9e72e1c168f8b8c920bab4b9d0fd97144ce142))
* **openwrt-captive-monitor:** rebase and modernize captive portal intercept & packaging for OpenWrt 24.x ([7b5e2d6](https://github.com/nagual2/openwrt-captive-monitor/commit/7b5e2d624f1a2fe0cf51266cdc1f7aeb13651097))
* **openwrt:** convert tests to pure OpenWrt validation ([1ab308f](https://github.com/nagual2/openwrt-captive-monitor/commit/1ab308f42cfb7011a06e5ad21e1799a949f0b0e2))
* **sdk:** improve OpenWrt SDK package build process ([5b8c756](https://github.com/nagual2/openwrt-captive-monitor/commit/5b8c7563512a5da8b4438fa84044ab4526688661))
* **sdk:** use OpenWrt feeds system for package building ([53372c1](https://github.com/nagual2/openwrt-captive-monitor/commit/53372c1101d941eca85889eb4a3fc4444cd9a7ff))
* **shellcheck:** add comprehensive ash compatibility annotations ([0f7a7bb](https://github.com/nagual2/openwrt-captive-monitor/commit/0f7a7bb1b85cba991838926dfb7c7c1f2b6e1592))
* **shellcheck:** add comprehensive disable annotations and simplify workflow ([008cba3](https://github.com/nagual2/openwrt-captive-monitor/commit/008cba3452ddcd5ad948350a22f4a55ca0ad6c91))
* **shellcheck:** clean up excessive disable annotations ([df81fc4](https://github.com/nagual2/openwrt-captive-monitor/commit/df81fc4f931954eea6606e111722f634a8bd285d))
* **shellcheck:** comprehensive ash compatibility fixes ([0616788](https://github.com/nagual2/openwrt-captive-monitor/commit/06167883016059405b1af255249ed122877fee71))
* **shellcheck:** fix ash compatibility and workflow file patterns ([86e3645](https://github.com/nagual2/openwrt-captive-monitor/commit/86e36459b5e882681f4c5637b8bd3f3ef890724f))
* **shellcheck:** fix sh -n syntax validation commands ([3feb8b8](https://github.com/nagual2/openwrt-captive-monitor/commit/3feb8b8627c8db602da194f2264a95b7b9477d37))
* **shellcheck:** improve workflow file detection and POSIX compatibility ([16d459a](https://github.com/nagual2/openwrt-captive-monitor/commit/16d459a8caa517bc3b95796aff3fd5ddffc29844))
* **shell:** fix POSIX shell compatibility in test scripts ([1ab45c3](https://github.com/nagual2/openwrt-captive-monitor/commit/1ab45c33f12e7e2eb47eb35bd3c2d31584905061))
* **shell:** resolve POSIX shell compatibility issues ([faf23e2](https://github.com/nagual2/openwrt-captive-monitor/commit/faf23e2fdca434b420d7be66ea50eca45564d169))
* **shfmt:** remove -filename option from shfmt config ([04cb8d8](https://github.com/nagual2/openwrt-captive-monitor/commit/04cb8d81973a15f9256b85088a37d7747adfc172))
* **test:** resolve busybox mock recursion & httpd sleep, stabilize test harness ([9e79438](https://github.com/nagual2/openwrt-captive-monitor/commit/9e79438c2b36abe0b72c49bb73403405b978b8e3))
* **tests:** debug and fix stateful iptables mock, unblock hanging test ([5b5aee1](https://github.com/nagual2/openwrt-captive-monitor/commit/5b5aee14f26e571773c3b66120435fcf93af7350))


### Documentation

* **audit:** update audit, backlog, and test plan for OpenWrt 24.x/filogic ([#17](https://github.com/nagual2/openwrt-captive-monitor/issues/17)) ([c2c6e39](https://github.com/nagual2/openwrt-captive-monitor/commit/c2c6e39494953a4a605d65ebf768e0ec3dab9db6))


### Continuous Integration

* **workflows:** consolidate CI workflows, add release automation, and improve packaging ([e515939](https://github.com/nagual2/openwrt-captive-monitor/commit/e51593937ec355bc9539003e257cc1cfb798ab5f))

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
