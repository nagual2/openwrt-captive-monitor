# openwrt-captive-monitor

[![CI](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/ci.yml/badge.svg?branch=main&label=CI)](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/ci.yml?query=branch%3Amain)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub release](https://img.shields.io/github/release/nagual2/openwrt-captive-monitor.svg)](https://github.com/nagual2/openwrt-captive-monitor/releases)

---

## 🌐 Sprache

[English](README.md) | **Deutsch** | [Русский](README.ru.md)

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
