# openwrt-captive-monitor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub release](https://img.shields.io/github/release/nagual2/openwrt-captive-monitor.svg)](https://github.com/nagual2/openwrt-captive-monitor/releases)
[![GitHub stars](https://img.shields.io/github/stars/nagual2/openwrt-captive-monitor.svg?style=social)](https://github.com/nagual2/openwrt-captive-monitor/stargazers)

---

## 🌐 Language

**English** | [Deutsch](README.de.md) | [Русский](README.ru.md)

---

## 🤖 About Project Development

This project was entirely developed with the assistance of AI agents and has undergone a significant evolution. Initially starting as a simple shell script for OpenWrt, the project evolved into a full-fledged Python solution based on the Selenium library.

During debugging, it became clear that reliable authentication through browser technologies is impossible on compact routers with limited resources. Selenium-based scripts require significant RAM (minimum 2-4 GB) and a full Chrome/Chromium browser.

**Current Architecture:**
- **OpenWrt Router** - minimal shell script for captive portal detection
- **External Server** - Python script with Selenium for authentication (Debian/Ubuntu on mini-PC with 4GB RAM)

**Recommended Hardware for Authentication Server:**
- Raspberry Pi 3 or higher
- Any x86-64 mini-PC with 4GB+ RAM
- Linux Mint / Ubuntu / Debian

This hybrid approach leverages the advantages of both platforms: lightweight monitoring on the router and powerful browser automation on a dedicated device.

---

## ✨ Features

- **🔍 Automatic Authentication** - Automatically authenticates against Conn4 captive portals (e.g. Leonardo Hotels)
- **⚡ Lightweight** - Simple shell script (~10KB), no heavy dependencies
- **🔄 Session Maintenance** - Cron-based checks ensure you stay online
- **🛡️ Secure** - Uses standard system tools (`curl`)

> **Note**: This package is specifically designed for Conn4-based captive portals.

## 🚀 Quick Start

### For Debian/Ubuntu/Linux Mint (Recommended)

#### System Requirements
- Debian 11+ / Ubuntu 20.04+ / Linux Mint 20+
- 4GB+ RAM
- Python 3.8+
- Chromium or Google Chrome

#### Installation from .deb Package

```bash
# Download latest package
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_2026.1.16.5-1_all.deb

# Install package
sudo dpkg -i openwrt-captive-monitor_*.deb

# Install dependencies (if errors occur)
sudo apt-get install -f
```

The package will automatically:
1. Install Python script to `/usr/bin/captive-portal-monitor`
2. Install systemd service for autostart
3. Enable service for automatic startup on boot

#### Service Management

```bash
# Start service
sudo systemctl start captive-portal-monitor

# Check status
sudo systemctl status captive-portal-monitor

# View logs
sudo journalctl -u captive-portal-monitor -f

# Stop service
sudo systemctl stop captive-portal-monitor
```

📖 **Detailed Documentation:** [docs/debian-installation.md](docs/debian-installation.md)

---

### For OpenWrt Routers

#### Prerequisites
- OpenWrt 21.02+ (or any system with `opkg`, `curl` and `cron`)
- `curl` package installed (automatically handled by dependency)

#### Installation

**Option 1: Prebuilt Package (Recommended)**

```bash
# Download latest package
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_*.ipk

# Install on router
scp openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

The package will automatically:
1. Install the auth script to `/usr/sbin/auth_conn4.sh`
2. Add a cron job to `/etc/crontabs/root` to run every minute
3. Restart the cron service

**Option 2: Build from Source**

```bash
# Clone repository
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor

# Build package
scripts/build_ipk.sh --arch all

# Install
scp dist/opkg/all/openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

## 🔧 Configuration

### For Debian/Ubuntu

The service works automatically. For configuration, create file `/etc/default/captive-portal-monitor`:

```bash
# OpenWrt router for SOCKS proxy
OPENWRT_SSH_HOST=192.168.1.1
OPENWRT_SSH_USER=root

# SOCKS proxy port (default 10800)
NOJS_SOCKS_PORT=10800

# Environment (dev or prod)
CPM_ENV=prod
```

### For OpenWrt

Configuration is zero-touch. The script detects the portal URL automatically.

To disable or change the schedule, edit the root crontab:

```bash
crontab -e
```

Default entry:
```cron
*/1 * * * * /usr/sbin/auth_conn4.sh
```

## 🔍 Troubleshooting

### For Debian/Ubuntu

**Check logs:**
```bash
sudo journalctl -u captive-portal-monitor -n 50
```

**Run manually:**
```bash
sudo /usr/bin/captive-portal-monitor
```

**Check status:**
```bash
sudo systemctl status captive-portal-monitor
```

### For OpenWrt

**Check logs:**
```bash
logread | grep conn4_auth
```

**Run manually:**
```bash
sh /usr/sbin/auth_conn4.sh
```

**Verify installation:**
```bash
ls -l /usr/sbin/auth_conn4.sh
grep auth_conn4 /etc/crontabs/root
```

## 📄 License

This project is licensed under the [MIT License](LICENSE).
