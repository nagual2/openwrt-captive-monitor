# Changelog

## [1.0.1](https://github.com/nagual2/openwrt-captive-monitor/compare/v0.1.2...v1.0.1)

### Documentation & Cleanup
- Comprehensive markdown file audit and cleanup
- Removed temporary/technical reports and audit files
- Updated version references throughout documentation to 1.0.1
- Cleaned up repository structure by removing obsolete files

### Version Management
- Synchronized all version files to 1.0.1
- Updated package documentation with current version
- Standardized version references across all documentation

## [0.1.2](https://github.com/nagual2/openwrt-captive-monitor/compare/v0.1.1...v0.1.2)

### Documentation & Reporting
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
