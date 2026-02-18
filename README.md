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

### System Requirements

- Debian 11+ / Ubuntu 20.04+ / Linux Mint 20+
- 4GB+ RAM (recommended)
- Python 3.8+
- Chromium or Google Chrome

### Installation from .deb Package

```bash
# Download latest package
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_2026.2.19.1-1_all.deb

# Install package
sudo dpkg -i openwrt-captive-monitor_*.deb

# Install dependencies (if errors occur)
sudo apt-get install -f
```

The package will automatically:
1. Install Python script to `/usr/bin/captive-portal-monitor`
2. Install systemd service for autostart (default mode)
3. Enable service for automatic startup on boot

**Startup Mode:**
- **systemd** (default) - Service runs continuously in background with automatic restart
- **cron** - Script runs every minute via cron (minimal resource usage)

To switch to cron mode, edit `/etc/default/captive-portal-monitor` and set `USE_CRON=true`, then reinstall the package.

### Service Management

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

### Build from Source

```bash
# Clone repository
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor

# Build package
bash scripts/build_deb.sh

# Install
sudo dpkg -i dist/deb/openwrt-captive-monitor_*.deb
sudo apt-get install -f
```

📖 **Detailed Documentation:** [docs/debian-installation.md](docs/debian-installation.md)

## 🔧 Configuration

The service works automatically. For configuration, create file `/etc/default/captive-portal-monitor`:

```bash
# Use cron instead of systemd (default: false)
# Set to "true" to use cron, "false" to use systemd
USE_CRON=false

# OpenWrt router for SOCKS proxy
OPENWRT_SSH_HOST=192.168.1.1
OPENWRT_SSH_USER=root

# SOCKS proxy port (default 10800)
NOJS_SOCKS_PORT=10800

# Environment (dev or prod)
CPM_ENV=prod
```

**To switch between modes:**
```bash
# Edit configuration
sudo nano /etc/default/captive-portal-monitor
# Change USE_CRON=true or USE_CRON=false

# Reinstall package to apply changes
sudo apt-get install --reinstall openwrt-captive-monitor
```

## 🔍 Troubleshooting

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

## 📄 License

This project is licensed under the [MIT License](LICENSE).
