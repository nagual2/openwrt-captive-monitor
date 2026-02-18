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

### Voraussetzungen

- OpenWrt 21.02+ (oder jedes System mit `opkg`, `curl` und `cron`)
- `curl` Paket installiert (wird automatisch durch Abhängigkeit behandelt)

### Installation

#### Option 1: Vorgefertigtes Paket (Empfohlen)

```bash
## Aktuelles Paket herunterladen
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_*.ipk

## Auf Router installieren
scp openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

Das Paket wird automatisch:
1. Das Auth-Skript nach `/usr/sbin/auth_conn4.sh` installieren
2. Einen Cron-Job zu `/etc/crontabs/root` hinzufügen, der jede Minute läuft
3. Den Cron-Dienst neu starten

#### Option 2: Aus Quellcode erstellen

```bash
## Repository klonen
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor

## Paket erstellen
scripts/build_ipk.sh --arch all

## Installieren
scp dist/opkg/all/openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

## 🔧 Konfiguration

Die Konfiguration ist berührungslos (Zero-Touch). Das Skript erkennt die Portal-URL automatisch.

Um den Zeitplan zu deaktivieren oder zu ändern, bearbeiten Sie die Root-Crontab:

```bash
crontab -e
```

Standard-Eintrag:
```cron
*/1 * * * * /usr/sbin/auth_conn4.sh
```

## 🔍 Fehlerbehebung

**Logs prüfen:**
```bash
logread | grep conn4_auth
```

**Manuell ausführen:**
```bash
sh /usr/sbin/auth_conn4.sh
```

**Installation überprüfen:**
```bash
ls -l /usr/sbin/auth_conn4.sh
grep auth_conn4 /etc/crontabs/root
```

## 📄 Lizenz

Dieses Projekt ist unter der [MIT License](LICENSE) lizenziert.
