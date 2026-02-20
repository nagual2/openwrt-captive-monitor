# openwrt-captive-monitor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub release](https://img.shields.io/github/release/nagual2/openwrt-captive-monitor.svg)](https://github.com/nagual2/openwrt-captive-monitor/releases)
[![GitHub stars](https://img.shields.io/github/stars/nagual2/openwrt-captive-monitor.svg?style=social)](https://github.com/nagual2/openwrt-captive-monitor/stargazers)

---

## 🌐 Sprache

[English](README.md) | **Deutsch** | [Русский](README.ru.md)

---

## 🤖 Über die Projektentwicklung

Dieses Projekt wurde vollständig mit Hilfe von KI-Agenten entwickelt und hat eine bedeutende Evolution durchlaufen. Ursprünglich als einfaches Shell-Skript für OpenWrt gestartet, entwickelte sich das Projekt zu einer vollwertigen Python-Lösung basierend auf der Selenium-Bibliothek.

Während des Debuggings wurde klar, dass eine zuverlässige Authentifizierung über Browser-Technologien auf kompakten Routern mit begrenzten Ressourcen unmöglich ist. Selenium-basierte Skripte benötigen erheblichen RAM (mindestens 2-4 GB) und einen vollständigen Chrome/Chromium-Browser.

**Aktuelle Architektur:**
- **OpenWrt Router** — minimales Shell-Skript zur Erkennung von Captive Portals und curl-basierte Auth
- **Externer Server (Docker)** — Python-Daemon mit Selenium für browserbasierte Authentifizierung

**Empfohlene Hardware für Authentifizierungsserver:**
- Raspberry Pi 3 oder höher
- Beliebiger x86-64 Mini-PC mit 4GB+ RAM
- Linux Mint / Ubuntu / Debian

---

## ✨ Funktionen

- **🔍 Automatische Authentifizierung** — Authentifiziert sich automatisch an Conn4 Captive Portalen (z.B. Leonardo Hotels)
- **🐳 Docker-Paketierung** — Alle Abhängigkeiten (Chrome, Selenium, Python) in einem Container
- **🔄 Sitzungserhaltung** — Daemon überwacht kontinuierlich die Konnektivität und re-authentifiziert bei Bedarf
- **🛡️ Sicher** — Isolierte Docker-Umgebung, keine systemweiten Abhängigkeiten

> **Hinweis**: Dieses Paket wurde speziell für Conn4-basierte Captive Portale entwickelt.

## 🚀 Schnellstart

### Systemanforderungen

- Debian 11+ / Ubuntu 20.04+ / Linux Mint 20+
- Docker installiert (`curl -fsSL https://get.docker.com | sudo sh`)
- 4GB+ RAM (empfohlen)

### Variante 1: Installation aus .deb-Paket (Empfohlen)

Das .deb-Paket enthält das vorgebaute Docker-Image und einen systemd-Dienst.

```bash
# Aktuelles Paket herunterladen
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor-docker_latest_all.deb

# Installieren
sudo dpkg -i openwrt-captive-monitor-docker_*.deb
```

### Variante 2: Docker Compose

```bash
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor/docker/daemon

cp .env.example .env
docker compose up -d
```

### Variante 3: Docker Run

```bash
docker build -f docker/daemon/Dockerfile -t captive-portal-daemon:latest .

docker run -d \
  --name captive-daemon \
  --network host \
  --restart unless-stopped \
  -v /var/log/captive-daemon:/var/log \
  -v /dev/shm:/dev/shm \
  -e CHECK_INTERVAL=60 \
  captive-portal-daemon:latest
```

## 🔧 Dienstverwaltung

```bash
# Status prüfen
sudo systemctl status captive-daemon

# Logs anzeigen
sudo journalctl -u captive-daemon -f

# Neustart
sudo systemctl restart captive-daemon

# Stoppen
sudo systemctl stop captive-daemon
```

## ⚙️ Konfiguration

Bearbeiten Sie `/etc/default/captive-daemon`:

```bash
# Prüfintervall in Sekunden (Standard: 60)
CHECK_INTERVAL=60

# Log-Level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

## 📦 OpenWrt-Paket

Für OpenWrt-Router ist ein leichtgewichtiges Shell-Skript-Paket verfügbar:

```bash
opkg install openwrt-captive-monitor_*.ipk
```

## 🔍 Fehlerbehebung

```bash
# Container-Status
docker ps -a --filter name=captive-daemon

# Daemon-Logs
docker logs captive-daemon --tail 50

# Neustart
docker restart captive-daemon
```

📖 **Ausführliche Dokumentation:** [docs/debian-installation.md](docs/debian-installation.md)

## 📄 Lizenz

Dieses Projekt ist unter der [MIT License](LICENSE) lizenziert.
