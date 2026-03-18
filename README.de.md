# openwrt-captive-monitor 🐳

Hybrides Automatisierungssystem für Conn4-basierte Captive Portals (z. B. Leonardo Hotels). Leichtgewichtiges Monitoring auf OpenWrt und leistungsstarke browserbasierte Authentifizierung auf einem dedizierten Docker-fähigen Gerät.

---

## ✨ Funktionen

- **🔍 Automatische Authentifizierung** — verwendet Selenium & Chromium für komplexe Portale
- **🐳 Docker-Paketierung** — alle Abhängigkeiten (Chrome, Selenium, Python) in einem Debian-basierten Image
- **🔄 Sitzungspflege** — optimierter Daemon überwacht die Verbindung und authentifiziert sich nur bei Bedarf neu
- **🛡️ Sicher & Sauber** — isolierte Docker-Umgebung mit Ressourcenlimits

## 🚀 Schnellstart

### Systemanforderungen

- Debian 11+ / Ubuntu 20.04+ / Linux Mint 20+
- Docker & Docker Compose
- 512MB+ RAM (Docker-Instanzlimit)

### Option 1: Installation aus dem .deb Paket (Empfohlen)

Der einfachste Weg zur Bereitstellung auf einem Debian-basierten Server.

```bash
# Aktuelles Paket herunterladen
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor-docker_latest_all.deb

# Installieren
sudo dpkg -i openwrt-captive-monitor-docker_*.deb
```

### Option 2: Docker Compose (Lokaler Build)

```bash
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor/docker/daemon-selenium

# Build und Start
docker compose up -d
```

## 🔧 Verwaltung

### Verwendung von PowerShell (Windows/WSL)
Nutzen Sie das Verwaltungsskript in `docker/daemon-selenium/manage.ps1`:
```powershell
.\manage.ps1 status    # Status prüfen
.\manage.ps1 logs      # Logs anzeigen
.\manage.ps1 restart   # Daemon neu starten
```

### Verwendung der Docker CLI
```bash
# Container-Status
docker ps -a --filter name=captive-daemon

# Logs anzeigen
docker logs -f captive-daemon
```

## ⚙️ Konfiguration

Cookie-Datei (auf dem Host): `/var/lib/captive-daemon/cookies.pkl` (automatisch verwaltet)
Systemd-Umgebung: `/etc/default/captive-daemon`

```bash
CHECK_INTERVAL=60
LOG_LEVEL=INFO
```

## 📦 OpenWrt-Paket

Für den Router (Xiaomi AX3000T usw.) können Sie ein leichtgewichtiges `.ipk`-Paket mit dem OpenWrt SDK erstellen und installieren:

```bash
# Build mit OpenWrt SDK (siehe docs/docker-master.md)
# Dann auf dem Router installieren:
opkg install openwrt-captive-monitor_*.ipk
```

📖 **Detaillierte Dokumentation:** [docs/docker-master.md](docs/docker-master.md)

## 📄 Lizenz

Dieses Projekt ist unter der [MIT License](LICENSE) lizenziert.
