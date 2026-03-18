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
- **OpenWrt Router** — minimal shell script for captive portal detection and curl-based auth
- **External Server (Docker)** — Python daemon with Selenium for browser-based authentication

**Recommended Hardware for Authentication Server:**
- Raspberry Pi 3 or higher
- Any x86-64 mini-PC with 4GB+ RAM
- Linux Mint / Ubuntu / Debian

This hybrid approach leverages the advantages of both platforms: lightweight monitoring on the router and powerful browser automation on a dedicated device.

---

## ✨ Features

- **🔍 Automatic Authentication** — Automatically authenticates against Conn4 captive portals (e.g. Leonardo Hotels)
- **🐳 Docker Packaging** — All dependencies (Chrome, Selenium, Python) bundled in a single container
- **🔄 Session Maintenance** — Daemon continuously monitors connectivity and re-authenticates when needed
- **🛡️ Secure** — Isolated Docker environment, no system-wide dependencies

> **Note**: This package is specifically designed for Conn4-based captive portals.

## 🚀 Quick Start

### System Requirements

- Debian 11+ / Ubuntu 20.04+ / Linux Mint 20+
- Docker installed (`curl -fsSL https://get.docker.com | sudo sh`)
- 4GB+ RAM (recommended)

### Option 1: Install from .deb Package (Recommended)

The .deb package includes the pre-built Docker image and a systemd service.

```bash
# Download latest package
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor-docker_latest_all.deb

# Install
sudo dpkg -i openwrt-captive-monitor-docker_*.deb
```

The package will automatically:
1. Load the Docker image
2. Install a systemd service
3. Start the daemon

### Option 2: Docker Compose

```bash
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor/docker/daemon

cp .env.example .env
# Edit .env if needed

docker compose up -d
```

### Option 3: Docker Run

```bash
# Build image
docker build -f docker/daemon/Dockerfile -t captive-portal-daemon:latest .

# Run
docker run -d \
  --name captive-daemon \
  --network host \
  --restart unless-stopped \
  -v /var/log/captive-daemon:/var/log \
  -v /dev/shm:/dev/shm \
  -e CHECK_INTERVAL=60 \
  captive-portal-daemon:latest
```

## 🔧 Service Management

```bash
# Check status
sudo systemctl status captive-daemon

# View logs
sudo journalctl -u captive-daemon -f
# or
tail -f /var/log/captive-daemon/captive_portal_daemon.log

# Restart
sudo systemctl restart captive-daemon

# Stop
sudo systemctl stop captive-daemon
```

## ⚙️ Configuration

Edit `/etc/default/captive-daemon`:

```bash
# Check interval in seconds (default: 60)
CHECK_INTERVAL=60

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

## 📦 OpenWrt Package

For OpenWrt routers, a lightweight shell script package is available:

```bash
# Download from GitHub Releases
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_latest_all.ipk

# Install on router
opkg install openwrt-captive-monitor_*.ipk
```

The OpenWrt package uses `curl` for HTTP-based authentication without browser dependencies.

## 🔍 Troubleshooting

**Check container status:**
```bash
docker ps -a --filter name=captive-daemon
```

**View daemon logs:**
```bash
docker logs captive-daemon --tail 50
```

**Restart daemon:**
```bash
docker restart captive-daemon
```

**Rebuild image:**
```bash
docker compose -f docker/daemon/docker-compose.yml build --no-cache
docker compose -f docker/daemon/docker-compose.yml up -d
```

📖 **Detailed Documentation:** [docs/debian-installation.md](docs/debian-installation.md)

## 📄 License

This project is licensed under the [MIT License](LICENSE).
