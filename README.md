# openwrt-captive-monitor

Hybrid automation for Conn4-based captive portals (e.g. Leonardo Hotels). Lightweight connectivity checks plus browser-based authentication when cookies expire or the portal drops the session.

---

## Features

- **Automatic Authentication** — Selenium + Chromium against complex portal UIs
- **Docker Packaging** — Chrome, Selenium, and Python in one Debian-based image
- **Adaptive Daemon** — Fast curl/ping loop (default 5s) with exponential backoff on outage (up to 60s); Chrome only when needed
- **Session Maintenance** — Cookie TTL + optional keepalive throttle (`REFRESH_INTERVAL`)

## Quick Start

### System Requirements

- Debian 11+ / Ubuntu 20.04+ / Linux Mint 20+
- Docker & Docker Compose
- 512MB+ RAM (1GB recommended for Chromium)

### Option 1: Install from .deb Package

```bash
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor-docker_latest_all.deb
sudo dpkg -i openwrt-captive-monitor-docker_*.deb
```

### Option 2: Docker Compose (local build)

From the repository root (build context must be the project root):

```bash
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor
docker build -f docker/daemon-selenium/Dockerfile -t captive-portal-daemon:latest .
cd docker/daemon-selenium
docker compose up -d
```

On Windows/PowerShell you can use `docker/daemon-selenium/manage.ps1`:

```powershell
.\manage.ps1 build
.\manage.ps1 start
.\manage.ps1 status
.\manage.ps1 logs
```

## Management

```bash
docker ps -a --filter name=captive-daemon
docker logs -f captive-daemon
```

## Configuration

Cookies and metadata live on the host under `docker/daemon-selenium/data/` (or `/var/lib/captive-daemon/` for the .deb install).

Environment (compose / systemd):

| Variable | Default | Meaning |
|----------|---------|---------|
| `CHECK_INTERVAL` | `5` | Baseline sleep between checks (seconds) |
| `REFRESH_INTERVAL` | `1800` | Min seconds between Chrome keepalives when cookies are still valid |
| `DAEMON_MODE` | `true` | Loop forever; set `false` for one-shot |
| `LOG_LEVEL` | `INFO` | Logging level |

On network failure the daemon doubles the sleep interval up to **60s**, then resets to `CHECK_INTERVAL` after a successful check. Chrome is **not** kept warm in memory — it starts only when cookies need refresh, keepalive is due, or connectivity is down.

Detailed docs: [docs/docker-master.md](docs/docker-master.md) (if present) and [docs/commands_cheatsheet.md](docs/commands_cheatsheet.md).

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests/ -v
```

## License

This project is licensed under the [MIT License](LICENSE).
