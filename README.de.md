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
- **OpenWrt Router** - minimales Shell-Skript zur Erkennung von Captive Portals
- **Externer Server** - Python-Skript mit Selenium zur Authentifizierung (Debian/Ubuntu auf Mini-PC mit 4GB RAM)

**Empfohlene Hardware für Authentifizierungsserver:**
- Raspberry Pi 3 oder höher
- Beliebiger x86-64 Mini-PC mit 4GB+ RAM
- Linux Mint / Ubuntu / Debian

Dieser hybride Ansatz nutzt die Vorteile beider Plattformen: leichtgewichtiges Monitoring auf dem Router und leistungsstarke Browser-Automatisierung auf einem dedizierten Gerät.

---

## ✨ Funktionen

- **🔍 Automatische Authentifizierung** - Authentifiziert sich automatisch an Conn4 Captive Portalen (z.B. Leonardo Hotels)
- **⚡ Leichtgewichtig** - Einfaches Shell-Skript (~10KB), keine schweren Abhängigkeiten
- **🔄 Sitzungserhaltung** - Cron-basierte Prüfungen sorgen dafür, dass Sie online bleiben
- **🛡️ Sicher** - Verwendet Standard-Systemtools (`curl`)

> **Hinweis**: Dieses Paket wurde speziell für Conn4-basierte Captive Portale entwickelt.

## 🚀 Schnellstart

### Systemanforderungen

- Debian 11+ / Ubuntu 20.04+ / Linux Mint 20+
- 4GB+ RAM (empfohlen)
- Python 3.8+
- Chromium oder Google Chrome

### Installation aus .deb-Paket

```bash
# Aktuelles Paket herunterladen
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_2026.1.16.5-1_all.deb

# Paket installieren
sudo dpkg -i openwrt-captive-monitor_*.deb

# Abhängigkeiten installieren (falls Fehler auftreten)
sudo apt-get install -f
```

Das Paket wird automatisch:
1. Python-Skript nach `/usr/bin/captive-portal-monitor` installieren
2. Systemd-Dienst für Autostart installieren (Standardmodus)
3. Dienst für automatischen Start beim Booten aktivieren

**Startmodi:**
- **systemd** (Standard) - Dienst läuft kontinuierlich im Hintergrund mit automatischem Neustart
- **cron** - Skript wird jede Minute über cron ausgeführt (minimale Ressourcennutzung)

Um in den Cron-Modus zu wechseln, bearbeiten Sie `/etc/default/captive-portal-monitor` und setzen Sie `USE_CRON=true`, dann installieren Sie das Paket neu.

### Dienstverwaltung

```bash
# Dienst starten
sudo systemctl start captive-portal-monitor

# Status prüfen
sudo systemctl status captive-portal-monitor

# Logs anzeigen
sudo journalctl -u captive-portal-monitor -f

# Dienst stoppen
sudo systemctl stop captive-portal-monitor
```

### Aus Quellcode erstellen

```bash
# Repository klonen
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor

# Paket erstellen
bash scripts/build_deb.sh

# Installieren
sudo dpkg -i dist/deb/openwrt-captive-monitor_*.deb
sudo apt-get install -f
```

📖 **Ausführliche Dokumentation:** [docs/debian-installation.md](docs/debian-installation.md)

## 🔧 Konfiguration

Der Dienst funktioniert automatisch. Für die Konfiguration erstellen Sie die Datei `/etc/default/captive-portal-monitor`:

```bash
# Cron anstelle von systemd verwenden (Standard: false)
# Setzen Sie auf "true" für Cron, "false" für systemd
USE_CRON=false

# OpenWrt Router für SOCKS-Proxy
OPENWRT_SSH_HOST=192.168.1.1
OPENWRT_SSH_USER=root

# SOCKS-Proxy-Port (Standard 10800)
NOJS_SOCKS_PORT=10800

# Umgebung (dev oder prod)
CPM_ENV=prod
```

**Zwischen Modi wechseln:**
```bash
# Konfiguration bearbeiten
sudo nano /etc/default/captive-portal-monitor
# Ändern Sie USE_CRON=true oder USE_CRON=false

# Paket neu installieren, um Änderungen anzuwenden
sudo apt-get install --reinstall openwrt-captive-monitor
```

## 🔍 Fehlerbehebung

**Logs prüfen:**
```bash
sudo journalctl -u captive-portal-monitor -n 50
```

**Manuell ausführen:**
```bash
sudo /usr/bin/captive-portal-monitor
```

**Status prüfen:**
```bash
sudo systemctl status captive-portal-monitor
```

## 📄 Lizenz

Dieses Projekt ist unter der [MIT License](LICENSE) lizenziert.
