# openwrt-captive-monitor

[![CI](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/ci.yml/badge.svg?branch=main&label=CI)](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/ci.yml?query=branch%3Amain)
[![Package Build](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/openwrt-build.yml/badge.svg?branch=main&label=Package%20Build)](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/openwrt-build.yml?query=branch%3Amain)
[![Release](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/release-please.yml/badge.svg?branch=main&label=Release)](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/release-please.yml?query=branch%3Amain)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub release](https://img.shields.io/github/release/nagual2/openwrt-captive-monitor.svg)](https://github.com/nagual2/openwrt-captive-monitor/releases)
[![GitHub stars](https://img.shields.io/github/stars/nagual2/openwrt-captive-monitor.svg?style=social)](https://github.com/nagual2/openwrt-captive-monitor/stargazers)
## ✨ Features

- **🔍 Automatic Detection** - Detects captive portals without user intervention
- **🌐 Traffic Interception** - Temporarily redirects DNS/HTTP traffic to portal
- **🔄 Self-Healing** - Automatically restores normal operation after authentication
- **⚡ Lightweight** - Minimal resource usage on router hardware
- **🛡️ Security-First** - HTTPS traffic never intercepted, preserves privacy
- **🔧 Flexible Configuration** - UCI, environment variables, and CLI options
- **📊 Robust Monitoring** - Multiple detection methods and fallbacks
- **🌍 IPv6 Support** - Full dual-stack network support

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

```bash
## Clone repository
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor

## Build package
scripts/build_ipk.sh --arch all

## For advanced packaging options and release automation, see:
## docs/packaging.md

## Install built package
scp dist/opkg/all/openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

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
|---------|-----------|-------------|-------------|
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
    option lan_ipv6 'fd00::1'              # IPv6 address
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

## Linting
shellcheck openwrt_captive_monitor.sh
shfmt -i 2 -ci -sr -d openwrt_captive_monitor.sh

## Manual testing
/usr/sbin/openwrt_captive_monitor --oneshot --verbose
```

### Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📚 Documentation

- [Documentation Index](docs/index.md) - Complete guides and reference
- [Quick Start Guide](docs/usage/quick-start.md) - Get started in minutes
- [Configuration Reference](docs/configuration/reference.md) - All configuration options
- [Troubleshooting Guide](docs/guides/troubleshooting.md) - Common issues and solutions
- [Architecture Overview](docs/guides/architecture.md) - System design and components

## 🤝 Community

### Support

- [GitHub Issues](https://github.com/nagual2/openwrt-captive-monitor/issues) - Bug reports and feature requests
- [GitHub Discussions](https://github.com/nagual2/openwrt-captive-monitor/discussions) - General questions and help
- [Documentation](docs/index.md) - Comprehensive guides and reference

### Security

- [Security Policy](.github/SECURITY.md) - Security vulnerability reporting
- [Security Advisories](https://github.com/nagual2/openwrt-captive-monitor/security/advisories) - Security notifications

### Contributing

- [Contributing Guide](CONTRIBUTING.md) - Development guidelines and process
- [Code of Conduct](CODE_OF_CONDUCT.md) - Community guidelines
- [Project Management](docs/project/management.md) - Roadmap and release process

## 📊 Project Status

### Latest Release

- **Version**: v1.0.3 (See [releases page](https://github.com/nagual2/openwrt-captive-monitor/releases) for details)
- **License**: [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
- **Platform**: [![OpenWrt](https://img.shields.io/badge/OpenWrt-21.02%2B-blue.svg)](https://openwrt.org/)

### Compatibility

| OpenWrt Version | Status | Notes |
|-----------------|---------|--------|
| 21.02 (LTS) | ✅ Supported | Uses iptables backend |
| 22.03 (LTS) | ✅ Supported | Auto-detects backend |
| 23.05 (Stable) | ✅ Supported | Full nftables support |
| 24.10 (Development) | ✅ Supported | Latest features |

| Architecture | Status | Package |
|-------------|---------|----------|
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
