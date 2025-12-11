# openwrt-captive-monitor

[![CI](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/ci.yml/badge.svg?branch=main&label=CI)](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/ci.yml?query=branch%3Amain)
[![Security Scanning](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/security-scanning.yml/badge.svg?branch=main&label=Security)](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/security-scanning.yml?query=branch%3Amain)
[![Package Build](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/openwrt-build.yml/badge.svg?branch=main&label=Package%20Build)](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/openwrt-build.yml?query=branch%3Amain)
[![Release](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/release-please.yml/badge.svg?branch=main&label=Release)](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/release-please.yml?query=branch%3Amain)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub release](https://img.shields.io/github/release/nagual2/openwrt-captive-monitor.svg)](https://github.com/nagual2/openwrt-captive-monitor/releases)
[![GitHub stars](https://img.shields.io/github/stars/nagual2/openwrt-captive-monitor.svg?style=social)](https://github.com/nagual2/openwrt-captive-monitor/stargazers)

---

## 🌐 Language

**English** | [Deutsch](README.de.md) | [Русский](README.ru.md)

---

## ✨ Features

- **🔍 Automatic Detection** - Detects captive portals without user intervention
- **🌐 Traffic Interception** - Temporarily redirects DNS/HTTP traffic to portal
- **🔄 Self-Healing** - Automatically restores normal operation after authentication
- **⚡ Lightweight** - Minimal resource usage on router hardware
- **🛡️ Security-First** - HTTPS traffic never intercepted, preserves privacy
- **🔧 Flexible Configuration** - UCI, environment variables, and CLI options
- **📊 Robust Monitoring** - Multiple detection methods and fallbacks

> **Note**: IPv6 is not supported. The service operates in IPv4-only mode.

## 🏗️ Architecture Overview

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client        │    │   Router        │    │   External      │
│   Devices       │◄──►│  (OpenWrt +     │◄──►│   Network       │
│                 │    │  Captive        │    │                 │
│                 │    │  Monitor)       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

The service integrates seamlessly with OpenWrt's networking stack:
- **dnsmasq** - DNS hijacking for client redirection
- **iptables/nftables** - Traffic interception and redirection
- **procd** - Service management and monitoring
- **UCI** - Configuration management

## 🚀 Quick Start

### Prerequisites

- OpenWrt 21.02+ (22.03+ recommended)
- Root access to router
- 64MB+ RAM (128MB+ recommended)

### Installation

#### Option 1: Prebuilt Package (Recommended)

```bash
## Download latest package
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_*.ipk

## Install on router
scp openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

#### Option 2: Build from Source

**Local Build (Simple):**
```bash
## Clone repository
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor

## Build package locally
scripts/build_ipk.sh --arch all

## Install built package
scp dist/opkg/all/openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

**SDK Build (Official):**
```bash
## Clone repository
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor

## The project uses OpenWrt SDK for official builds
## See: docs/guides/sdk-build-workflow.md

## For local SDK builds:
wget https://downloads.openwrt.org/releases/23.05.3/targets/x86/64/openwrt-sdk-23.05.3-x86-64_gcc-12.3.0_musl.Linux-x86_64.tar.xz
tar -xf openwrt-sdk-*.tar.xz
cd openwrt-sdk-*/
cp -r ../package/openwrt-captive-monitor package/
./scripts/feeds update -a && ./scripts/feeds install -a
make package/openwrt-captive-monitor/compile V=s
```

> **Note**: The CI/CD pipeline automatically builds packages using the official OpenWrt SDK. See [docs/guides/sdk-build-workflow.md](docs/guides/sdk-build-workflow.md) for details.

### Basic Configuration

```bash
## Enable service
ssh root@192.168.1.1 <<'EOSSH'
uci set captive-monitor.config.enabled='1'
uci commit captive-monitor
/etc/init.d/captive-monitor enable
/etc/init.d/captive-monitor start
EOSSH
```

### Verification

```bash
## Check service status
ssh root@192.168.1.1 "logread | grep captive-monitor | tail -5"
```

## 📋 Table of Contents


- [Installation](#-quick-start)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Basic Configuration](#basic-configuration)
- [Installation Options](#-installation-options)
  - [Installation Matrix](#installation-matrix)
  - [OpenWrt SDK Build](#openwrt-sdk-build)
  - [Dependencies](#dependencies)
- [Configuration](#-configuration)
  - [Basic Settings](#basic-settings)
  - [Advanced Options](#advanced-options)
  - [Environment Variables](#environment-variables)
- [Usage](#-usage)
  - [Operation Modes](#operation-modes)
  - [Monitoring](#monitoring)
- [Troubleshooting](#-troubleshooting)
  - [Common Issues](#common-issues)
  - [Health Check](#health-check)
- [Development](#-development)
  - [Building](#building)
  - [Testing](#testing)
  - [How to Contribute](#how-to-contribute)
- [Documentation](#-documentation)
- [Community](#-community)
  - [Support](#support)
  - [Security](#security)
  - [Contributing](#contributing)
- [Project Status](#-project-status)
  - [Latest Release](#latest-release)
  - [Compatibility](#compatibility)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)
- [Related Projects](#-related-projects)


## 📦 Installation Options

### Installation Matrix

| Method | Use Case | Complexity | Maintenance |
| ------- | --------- | ----------- | ----------- |
| **Prebuilt Package** | Production, quick deployment | ⭐ Easy | Automatic updates |
| **SDK Build** | Custom builds, development | ⭐⭐ Medium | Manual updates |
| **Local Build** | Testing, modifications | ⭐⭐⭐ Hard | Manual updates |

### OpenWrt SDK Build

```bash
## Download OpenWrt SDK
wget https://downloads.openwrt.org/releases/22.03.5/targets/ath79/generic/openwrt-sdk-22.03.5-ath79-generic_gcc-11.2.0_musl.Linux-x86_64.tar.xz
tar -xf openwrt-sdk-*.tar.xz
cd openwrt-sdk-*

## Add package source
git clone https://github.com/nagual2/openwrt-captive-monitor.git package/openwrt-captive-monitor

## Build package
./scripts/feeds update -a
./scripts/feeds install openwrt-captive-monitor
make package/openwrt-captive-monitor/compile V=s
```

### Dependencies

**Runtime dependencies:**
- `dnsmasq` - DNS and DHCP server
- `curl` - HTTP probes and captive detection
- `iptables` or `nftables` - Traffic redirection

**Build dependencies:**
- `binutils`, `busybox`, `gzip`, `pigz`, `tar`, `xz-utils`

## 🔧 Configuration

### Basic Settings

```uci
config captive_monitor 'config'
    option enabled '1'                    # Enable service
    option mode 'monitor'                 # monitor or oneshot
    option wifi_interface 'phy1-sta0'       # WiFi interface
    option wifi_logical 'wwan'              # Logical interface
    option monitor_interval '60'            # Check interval (seconds)
    option ping_servers '1.1.1.1 8.8.8.8'   # Ping servers
    option enable_syslog '1'               # Enable logging
```

### Advanced Options

```uci
config captive_monitor 'config'
    # Network settings
    option lan_interface 'br-lan'           # LAN interface (auto-detect)
    option firewall_backend 'auto'            # iptables/nftables/auto
    
    # Timing settings
    option ping_timeout '2'                 # Ping timeout
    option http_probe_timeout '5'            # HTTP probe timeout
    option gateway_check_retries '2'         # Gateway check retries
    
    # Captive detection
    option captive_check_urls 'http://connectivitycheck.gstatic.com/generate_204 http://detectportal.firefox.com/success.txt'
```

### Environment Variables

```bash
## Override configuration
export MONITOR_INTERVAL="30"
export WIFI_INTERFACE="wlan0"
export PING_SERVERS="1.1.1.1 9.9.9.9"
export CAPTIVE_DEBUG="1"
```

## 📖 Usage

### Operation Modes

#### Monitor Mode (Default)

Continuous monitoring with specified interval:

```bash
## Start monitoring
/usr/sbin/openwrt_captive_monitor --monitor

## With custom interval
/usr/sbin/openwrt_captive_monitor --monitor --interval 30
```

#### Oneshot Mode

Single check and exit, ideal for cron:

```bash
## Single check
/usr/sbin/openwrt_captive_monitor --oneshot

## Cron job (every 15 minutes)
*/15 * * * * /usr/sbin/openwrt_captive_monitor --oneshot
```

### Monitoring

**Service Status:**
```bash
## Check if running
ps aux | grep openwrt_captive_monitor

## Service status
/etc/init.d/captive-monitor status

## Recent logs
logread | grep captive-monitor | tail -20
```

**Debug Mode:**
```bash
## Verbose output
/usr/sbin/openwrt_captive_monitor --oneshot --verbose

## Debug mode
export CAPTIVE_DEBUG="1"
/usr/sbin/openwrt_captive_monitor --oneshot
```

## 🔍 Troubleshooting

### Common Issues

**Service won't start:**
```bash
## Check configuration
uci show captive-monitor

## Check permissions
ls -la /usr/sbin/openwrt_captive_monitor

## Manual test
/usr/sbin/openwrt_captive_monitor --help
```

**Captive portal not detected:**
```bash
## Test detection URLs manually
curl -I http://connectivitycheck.gstatic.com/generate_204
curl -I http://detectportal.firefox.com/success.txt

## Add custom URLs
uci add_list captive-monitor.config.captive_check_urls='http://your-portal.com/detect'
```

**Redirection not working:**
```bash
## Check firewall rules
iptables -t nat -L CAPTIVE_HTTP_REDIRECT -n -v

## Check DNS overrides
cat /tmp/dnsmasq.d/captive_intercept.conf

## Restart services
/etc/init.d/dnsmasq restart
```

### Health Check

```bash
## Comprehensive health check
/usr/local/bin/captive-health-check.sh

## Manual cleanup (if needed)
/usr/sbin/openwrt_captive_monitor --force-cleanup
```

## 🧪 Development

### Optimized Build System

The project uses an optimized CI/CD build system with pre-built Docker SDK images:

**Features:**
- ⚡ **2-3 minutes faster** builds using Docker SDK images
- 🐳 Pre-built images in GitHub Container Registry (GHCR)
- 🔄 Automatic image updates and cleanup
- 📦 Support for 8 OpenWrt architectures

**Build times:**
- With Docker SDK: ~1.5-2.5 minutes
- Traditional SDK: ~3-5 minutes
- **Savings: 40-60%**

📖 See [Docker SDK Images Documentation](docs/docker-sdk-images.md) for details.

### Building

```bash
## Install build dependencies
sudo apt-get install -y binutils busybox gzip pigz tar xz-utils

## Build package
scripts/build_ipk.sh --arch all

## Validate package
tar -tzf dist/opkg/all/openwrt-captive-monitor_*.ipk
```

### Testing

```bash
## Run test suite
busybox sh tests/run.sh

## VM-based end-to-end testing
./scripts/run_openwrt_vm.sh

## Linting
shellcheck openwrt_captive_monitor.sh
shfmt -i 2 -ci -sr -d openwrt_captive_monitor.sh

## Manual testing
/usr/sbin/openwrt_captive_monitor --oneshot --verbose
```

#### VM Test Harness

The project includes a comprehensive VM-based testing system that automates end-to-end validation:

- **Automated OpenWrt VM provisioning** with QEMU/KVM
- **Package building and installation** in isolated environment
- **Smoke tests** for baseline, captive portal, and monitor modes
- **Artifact collection** for debugging and analysis
- **CI/CD ready** with fallback to TCG emulation

```bash
# Basic VM testing
./scripts/run_openwrt_vm.sh

# Custom configuration
./scripts/run_openwrt_vm.sh --openwrt-version 23.05 --workdir /tmp/test

# CI environment (no KVM)
./scripts/run_openwrt_vm.sh --reuse-vm --no-kvm
```

See [Virtualization Guide](docs/guides/virtualization.md) for detailed VM testing documentation.

### Creating a Release

This project uses a **manual release workflow** for creating new releases. Maintainers can trigger releases on-demand through GitHub Actions.

**To create a new release:**

1. Go to **Actions** → **Manual Release** in the GitHub repository
2. Click **"Run workflow"**
3. Configure the release (all fields are optional):
   - **Custom version**: Specify a version like `2025.11.27.1`, or leave empty for auto-generation based on current date
   - **Release notes**: Provide custom release notes, or leave empty for automatic generation
   - **Pre-release**: Check this box to mark the release as a pre-release
4. Click **"Run workflow"** to start the release process

**What happens during the release:**

The workflow will automatically:
- Generate or use the specified version tag (`vYYYY.M.D.N`)
- Update `VERSION` file and `PKG_VERSION` in Makefile
- Create a commit with version changes
- Create and push a git tag
- Build the universal package (`arch=all`)
- Validate the package
- Create a GitHub Release with the package attached
- Upload the `.ipk` file and `SHA256SUMS` to the release

**Version format:**
- **Tag:** `vYYYY.M.D.N` (e.g., `v2025.11.27.1`)
- **VERSION file:** `YYYY.M.D.N` (no leading `v`)
- **PKG_VERSION** in Makefile: `YYYY.M.D.N`
- **PKG_RELEASE:** always `1` for official releases

> **Example:**
> - Tag: `v2025.11.27.1`
> - `VERSION` file: `2025.11.27.1`
> - `package/openwrt-captive-monitor/Makefile`:
>   - `PKG_VERSION:=2025.11.27.1`
>   - `PKG_RELEASE:=1`

**Workflow parameters:**

| Parameter       | Description                            | Required | Default                              |
| --------------- | -------------------------------------- | -------- | ------------------------------------ |
| `version`       | Custom version (e.g., `2025.11.27.1`)  | No       | Auto-generated from current date     |
| `release_notes` | Custom release notes                   | No       | Auto-generated from git commits      |
| `prerelease`    | Mark as pre-release                    | No       | `false`                              |

For detailed information about the release process, see:
- [Manual Release Workflow](.github/workflows/manual-release.yml)
- [Auto Version Tag Guide](docs/release/AUTO_VERSION_TAG.md)
- [Release Process Documentation](docs/release/RELEASE_PROCESS.md)

### Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes using conventional commits (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

See [CONTRIBUTING.md](docs/contributing/CONTRIBUTING.md) for detailed guidelines.

## 📚 Documentation

- [Documentation Index](docs/index.md) - Complete guides and reference
- [Quick Start Guide](docs/usage/quick-start.md) - Get started in minutes
- [Configuration Reference](docs/configuration/reference.md) - All configuration options
- [Troubleshooting Guide](docs/guides/troubleshooting.md) - Common issues and solutions
- [Architecture Overview](docs/guides/architecture.md) - System design and components
- [Release Process](docs/release/RELEASE_PROCESS.md) - Release workflow and versioning
- [Release Restoration](docs/release/RELEASE_RESTORATION.md) - Restore missing releases

## 🤝 Community

### Support

- [GitHub Issues](https://github.com/nagual2/openwrt-captive-monitor/issues) - Bug reports and feature requests
- [GitHub Discussions](https://github.com/nagual2/openwrt-captive-monitor/discussions) - General questions and help
- [Documentation](docs/index.md) - Comprehensive guides and reference

### Security

- [Security Policy](.github/SECURITY.md) - Security vulnerability reporting
- [Security Advisories](https://github.com/nagual2/openwrt-captive-monitor/security/advisories) - Security notifications
- [Security Scanning](docs/SECURITY_SCANNING.md) - Automated security scanning documentation

### Contributing

- [Contributing Guide](docs/contributing/CONTRIBUTING.md) - Development guidelines and process
- [Code of Conduct](docs/contributing/CODE_OF_CONDUCT.md) - Community guidelines
- [Project Management](docs/project/management.md) - Roadmap and release process

## 📊 Project Status

### Latest Release

- **Version**: v1.0.6 (See [releases page](https://github.com/nagual2/openwrt-captive-monitor/releases) for details)
- **License**: [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
- **Platform**: [![OpenWrt](https://img.shields.io/badge/OpenWrt-21.02%2B-blue.svg)](https://openwrt.org/)

### Compatibility

| OpenWrt Version | Status | Notes |
| ---------------- | ------- | ----- |
| 21.02 (LTS) | ✅ Supported | Uses iptables backend |
| 22.03 (LTS) | ✅ Supported | Auto-detects backend |
| 23.05 (Stable) | ✅ Supported | Full nftables support |
| 24.10 (Development) | ✅ Supported | Latest features |

| Architecture | Status | Package |
| ----------- | ------- | ------- |
| mips_24kc | ✅ Supported | `openwrt-captive-monitor_*_mips_24kc.ipk` |
| aarch64_cortex-a53 | ✅ Supported | `openwrt-captive-monitor_*_aarch64_cortex-a53.ipk` |
| x86_64 | ✅ Supported | `openwrt-captive-monitor_*_x86_64.ipk` |
| all | ✅ Universal | `openwrt-captive-monitor_*_all.ipk` |

## 📄 License

This project is licensed under the [MIT License](LICENSE) - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenWrt Community** - For the excellent router firmware and tools
- **BusyBox Project** - Providing essential Unix utilities for embedded systems
- **Contributors** - Everyone who has helped improve this project

## 🔗 Related Projects

- [uspot](https://github.com/f00b4r0/uspot) - Full-featured captive portal for OpenWrt
- [apfree-wifidog](https://github.com/liudf0716/apfree-wifidog) - High-performance captive portal
- [CaptivePortalAutologin](https://github.com/jsparber/CaptivePortalAutologin) - Android auto-login app

---

<div align="center">
[📖 Documentation](docs/) • [🐛 Issues](https://github.com/nagual2/openwrt-captive-monitor/issues) • [💬 Discussions](https://github.com/nagual2/openwrt-captive-monitor/discussions)

Made with ❤️ for the OpenWrt community

</div>
