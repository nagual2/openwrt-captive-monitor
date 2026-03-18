# openwrt-captive-monitor 🐳

Hybrid automation system for Conn4-based captive portals (e.g. Leonardo Hotels). Lightweight monitoring on OpenWrt and powerful browser-based authentication on a dedicated Docker-enabled device.

---

## ✨ Features

- **🔍 Automatic Authentication** — Uses Selenium & Chromium to authenticate against complex portals
- **🐳 Docker Packaging** — Everything (Chrome, Selenium, Python) bundled in a single Debian-based image
- **🔄 Session Maintenance** — Optimized daemon monitors connectivity and re-authenticates only when needed
- **🛡️ Secure & Clean** — Runs in an isolated Docker environment with resource limits

## 🚀 Quick Start

### System Requirements

- Debian 11+ / Ubuntu 20.04+ / Linux Mint 20+
- Docker & Docker Compose
- 512MB+ RAM (Docker instance limit)

### Option 1: Install from .deb Package (Recommended)

The easiest way to deploy on a Debian-based server.

```bash
# Download latest package
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor-docker_latest_all.deb

# Install
sudo dpkg -i openwrt-captive-monitor-docker_*.deb
```

### Option 2: Docker Compose (Local Build)

```bash
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor/docker/daemon-selenium

# Build and start
docker compose up -d
```

## 🔧 Management

### Using PowerShell (Windows/WSL)
Use the included management script in `docker/daemon-selenium/manage.ps1`:
```powershell
.\manage.ps1 status    # Check status
.\manage.ps1 logs      # View logs
.\manage.ps1 restart   # Restart daemon
```

### Using Docker CLI
```bash
# Check status
docker ps -a --filter name=captive-daemon

# View logs
docker logs -f captive-daemon
```

## ⚙️ Configuration

Config file (on host): `/var/lib/captive-daemon/cookies.pkl` (automatically managed)
Systemd Environment: `/etc/default/captive-daemon`

```bash
CHECK_INTERVAL=60
LOG_LEVEL=INFO
```

## 📦 OpenWrt Package

For the router side (Xiaomi AX3000T, etc.), you can build and install a lightweight `.ipk` package using the OpenWrt SDK:

```bash
# Build using OpenWrt SDK (see docs/docker-master.md)
# Then install on router:
opkg install openwrt-captive-monitor_*.ipk
```

📖 **Detailed Documentation:** [docs/docker-master.md](docs/docker-master.md)

## 📄 License

This project is licensed under the [MIT License](LICENSE).
