# openwrt-captive-monitor

[![CI](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/ci.yml/badge.svg?branch=main&label=CI)](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/ci.yml?query=branch%3Amain)
[![Security Scanning](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/security-scanning.yml/badge.svg?branch=main&label=Security)](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/security-scanning.yml?query=branch%3Amain)
[![Package Build](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/openwrt-build.yml/badge.svg?branch=main&label=Package%20Build)](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/openwrt-build.yml?query=branch%3Amain)
[![Release](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/release-please.yml/badge.svg?branch=main&label=Release)](https://github.com/nagual2/openwrt-captive-monitor/actions/workflows/release-please.yml?query=branch%3Amain)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub release](https://img.shields.io/github/release/nagual2/openwrt-captive-monitor.svg)](https://github.com/nagual2/openwrt-captive-monitor/releases)
[![GitHub stars](https://img.shields.io/github/stars/nagual2/openwrt-captive-monitor.svg?style=social)](https://github.com/nagual2/openwrt-captive-monitor/stargazers)

---

## 🌐 Sprache

[English](README.md) | **Deutsch** | [Русский](README.ru.md)

---

## ✨ Funktionen

- **🔍 Automatische Erkennung** - Erkennt Captive Portale ohne Benutzereingriff
- **🌐 Traffic-Abfang** - Temporäre Umleitung von DNS/HTTP-Traffic zum Portal
- **🔄 Selbstheilung** - Stellt automatisch den normalen Betrieb nach der Authentifizierung wieder her
- **⚡ Leichtgewichtig** - Minimaler Ressourcenverbrauch auf Router-Hardware
- **🛡️ Sicherheit zuerst** - HTTPS-Traffic wird niemals abgefangen, Privatsphäre bleibt gewahrt
- **🔧 Flexible Konfiguration** - UCI, Umgebungsvariablen und CLI-Optionen
- **📊 Robustes Monitoring** - Mehrere Erkennungsmethoden und Fallbacks

> **Hinweis**: IPv6 wird nicht unterstützt. Der Service arbeitet nur im IPv4-Modus.

## 🏗️ Architektur-Übersicht

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client        │    │   Router        │    │   Externes      │
│   Geräte        │◄──►│  (OpenWrt +     │◄──►│   Netzwerk      │
│                 │    │  Captive        │    │                 │
│                 │    │  Monitor)       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

Der Service integriert sich nahtlos in den Netzwerk-Stack von OpenWrt:
- **dnsmasq** - DNS-Hijacking für Client-Umleitung
- **iptables/nftables** - Traffic-Abfang und Umleitung
- **procd** - Service-Verwaltung und Überwachung
- **UCI** - Konfigurationsverwaltung

## 🚀 Schnellstart

### Voraussetzungen

- OpenWrt 21.02+ (22.03+ empfohlen)
- Root-Zugriff auf den Router
- 64MB+ RAM (128MB+ empfohlen)

### Installation

#### Option 1: Vorgefertigtes Paket (Empfohlen)

```bash
## Aktuelles Paket herunterladen
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_*.ipk

## Auf Router installieren
scp openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

#### Option 2: Aus Quellcode erstellen

**Lokaler Build (Einfach):**
```bash
## Repository klonen
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor

## Paket lokal erstellen
scripts/build_ipk.sh --arch all

## Erstelltes Paket installieren
scp dist/opkg/all/openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

**SDK Build (Offiziell):**
```bash
## Repository klonen
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor

## Das Projekt verwendet OpenWrt SDK für offizielle Builds
## Siehe: docs/guides/sdk-build-workflow.md

## Für lokale SDK-Builds:
wget https://downloads.openwrt.org/releases/23.05.3/targets/x86/64/openwrt-sdk-23.05.3-x86-64_gcc-12.3.0_musl.Linux-x86_64.tar.xz
tar -xf openwrt-sdk-*.tar.xz
cd openwrt-sdk-*/
cp -r ../package/openwrt-captive-monitor package/
./scripts/feeds update -a && ./scripts/feeds install -a
make package/openwrt-captive-monitor/compile V=s
```

> **Hinweis**: Die CI/CD-Pipeline erstellt Pakete automatisch mit dem offiziellen OpenWrt SDK. Siehe [docs/guides/sdk-build-workflow.md](docs/guides/sdk-build-workflow.md) für Details.

### Basis-Konfiguration

```bash
## Service aktivieren
ssh root@192.168.1.1 <<'EOSSH'
uci set captive-monitor.config.enabled='1'
uci commit captive-monitor
/etc/init.d/captive-monitor enable
/etc/init.d/captive-monitor start
EOSSH
```

### Überprüfung

```bash
## Service-Status prüfen
ssh root@192.168.1.1 "logread | grep captive-monitor | tail -5"
```

## 📋 Inhaltsverzeichnis

- [Installation](#-schnellstart)
  - [Voraussetzungen](#voraussetzungen)
  - [Installation](#installation)
  - [Basis-Konfiguration](#basis-konfiguration)
- [Installationsoptionen](#-installationsoptionen)
  - [Installationsmatrix](#installationsmatrix)
  - [OpenWrt SDK Build](#openwrt-sdk-build)
  - [Abhängigkeiten](#abhängigkeiten)
- [Konfiguration](#-konfiguration)
  - [Grundeinstellungen](#grundeinstellungen)
  - [Erweiterte Optionen](#erweiterte-optionen)
  - [Umgebungsvariablen](#umgebungsvariablen)
- [Verwendung](#-verwendung)
  - [Betriebsmodi](#betriebsmodi)
  - [Überwachung](#überwachung)
- [Fehlerbehebung](#-fehlerbehebung)
  - [Häufige Probleme](#häufige-probleme)
  - [Gesundheitsprüfung](#gesundheitsprüfung)
- [Entwicklung](#-entwicklung)
  - [Build](#build)
  - [Tests](#tests)
  - [Beitragen](#beitragen-1)
- [Dokumentation](#-dokumentation)
- [Community](#-community)
  - [Support](#support)
  - [Sicherheit](#sicherheit)
  - [Mitwirken](#mitwirken)
- [Projektstatus](#-projektstatus)
  - [Aktuelles Release](#aktuelles-release)
  - [Kompatibilität](#kompatibilität)
- [Lizenz](#-lizenz)
- [Danksagungen](#-danksagungen)
- [Verwandte Projekte](#-verwandte-projekte)

## 📦 Installationsoptionen

### Installationsmatrix

| Methode | Anwendungsfall | Komplexität | Wartung |
| ------- | -------------- | ----------- | ------- |
| **Vorgefertigtes Paket** | Produktion, schnelle Bereitstellung | ⭐ Einfach | Automatische Updates |
| **SDK Build** | Custom Builds, Entwicklung | ⭐⭐ Mittel | Manuelle Updates |
| **Lokaler Build** | Tests, Modifikationen | ⭐⭐⭐ Schwer | Manuelle Updates |

### OpenWrt SDK Build

```bash
## OpenWrt SDK herunterladen
wget https://downloads.openwrt.org/releases/22.03.5/targets/ath79/generic/openwrt-sdk-22.03.5-ath79-generic_gcc-11.2.0_musl.Linux-x86_64.tar.xz
tar -xf openwrt-sdk-*.tar.xz
cd openwrt-sdk-*

## Paketquelle hinzufügen
git clone https://github.com/nagual2/openwrt-captive-monitor.git package/openwrt-captive-monitor

## Paket erstellen
./scripts/feeds update -a
./scripts/feeds install openwrt-captive-monitor
make package/openwrt-captive-monitor/compile V=s
```

### Abhängigkeiten

**Laufzeit-Abhängigkeiten:**
- `dnsmasq` - DNS- und DHCP-Server
- `curl` - HTTP-Prüfungen und Captive-Erkennung
- `iptables` oder `nftables` - Traffic-Umleitung

**Build-Abhängigkeiten:**
- `binutils`, `busybox`, `gzip`, `pigz`, `tar`, `xz-utils`

## 🔧 Konfiguration

### Grundeinstellungen

```uci
config captive_monitor 'config'
    option enabled '1'                    # Service aktivieren
    option mode 'monitor'                 # monitor oder oneshot
    option wifi_interface 'phy1-sta0'       # WiFi-Schnittstelle
    option wifi_logical 'wwan'              # Logische Schnittstelle
    option monitor_interval '60'            # Prüfintervall (Sekunden)
    option ping_servers '1.1.1.1 8.8.8.8'   # Ping-Server
    option enable_syslog '1'               # Logging aktivieren
```

### Erweiterte Optionen

```uci
config captive_monitor 'config'
    # Netzwerkeinstellungen
    option lan_interface 'br-lan'           # LAN-Schnittstelle (Auto-Erkennung)
    option firewall_backend 'auto'            # iptables/nftables/auto
    
    # Timing-Einstellungen
    option ping_timeout '2'                 # Ping-Timeout
    option http_probe_timeout '5'            # HTTP-Probe-Timeout
    option gateway_check_retries '2'         # Gateway-Check-Wiederholungen
    
    # Captive-Erkennung
    option captive_check_urls 'http://connectivitycheck.gstatic.com/generate_204 http://detectportal.firefox.com/success.txt'
```

### Umgebungsvariablen

```bash
## Konfiguration überschreiben
export MONITOR_INTERVAL="30"
export WIFI_INTERFACE="wlan0"
export PING_SERVERS="1.1.1.1 9.9.9.9"
export CAPTIVE_DEBUG="1"
```

## 📖 Verwendung

### Betriebsmodi

#### Monitor-Modus (Standard)

Kontinuierliche Überwachung mit festgelegtem Intervall:

```bash
## Überwachung starten
/usr/sbin/openwrt_captive_monitor --monitor

## Mit benutzerdefiniertem Intervall
/usr/sbin/openwrt_captive_monitor --monitor --interval 30
```

#### Oneshot-Modus

Einmalige Prüfung und Beenden, ideal für cron:

```bash
## Einmalige Prüfung
/usr/sbin/openwrt_captive_monitor --oneshot

## Cron-Job (alle 15 Minuten)
*/15 * * * * /usr/sbin/openwrt_captive_monitor --oneshot
```

### Überwachung

**Service-Status:**
```bash
## Prüfen ob läuft
ps aux | grep openwrt_captive_monitor

## Service-Status
/etc/init.d/captive-monitor status

## Aktuelle Logs
logread | grep captive-monitor | tail -20
```

**Debug-Modus:**
```bash
## Ausführliche Ausgabe
/usr/sbin/openwrt_captive_monitor --oneshot --verbose

## Debug-Modus
export CAPTIVE_DEBUG="1"
/usr/sbin/openwrt_captive_monitor --oneshot
```

## 🔍 Fehlerbehebung

### Häufige Probleme

**Service startet nicht:**
```bash
## Konfiguration prüfen
uci show captive-monitor

## Berechtigungen prüfen
ls -la /usr/sbin/openwrt_captive_monitor

## Manueller Test
/usr/sbin/openwrt_captive_monitor --help
```

**Captive Portal wird nicht erkannt:**
```bash
## Erkennungs-URLs manuell testen
curl -I http://connectivitycheck.gstatic.com/generate_204
curl -I http://detectportal.firefox.com/success.txt

## Benutzerdefinierte URLs hinzufügen
uci add_list captive-monitor.config.captive_check_urls='http://your-portal.com/detect'
```

**Umleitung funktioniert nicht:**
```bash
## Firewall-Regeln prüfen
iptables -t nat -L CAPTIVE_HTTP_REDIRECT -n -v

## DNS-Überschreibungen prüfen
cat /tmp/dnsmasq.d/captive_intercept.conf

## Services neustarten
/etc/init.d/dnsmasq restart
```

### Gesundheitsprüfung

```bash
## Umfassende Gesundheitsprüfung
/usr/local/bin/captive-health-check.sh

## Manuelle Bereinigung (falls erforderlich)
/usr/sbin/openwrt_captive_monitor --force-cleanup
```

## 🧪 Entwicklung

### Optimiertes Build-System

Das Projekt verwendet ein optimiertes CI/CD-Build-System mit vorgefertigten Docker SDK Images:

**Funktionen:**
- ⚡ **2-3 Minuten schneller** Builds mit Docker SDK Images
- 🐳 Vorgefertigte Images in GitHub Container Registry (GHCR)
- 🔄 Automatische Image-Updates und Bereinigung
- 📦 Unterstützung für 8 OpenWrt-Architekturen

**Build-Zeiten:**
- Mit Docker SDK: ~1.5-2.5 Minuten
- Traditionelles SDK: ~3-5 Minuten
- **Einsparung: 40-60%**

📖 Siehe [Docker SDK Images Dokumentation](docs/docker-sdk-images.md) für Details.

### Build

```bash
## Build-Abhängigkeiten installieren
sudo apt-get install -y binutils busybox gzip pigz tar xz-utils

## Paket erstellen
scripts/build_ipk.sh --arch all

## Paket validieren
tar -tzf dist/opkg/all/openwrt-captive-monitor_*.ipk
```

### Tests

```bash
## Testsuite ausführen
busybox sh tests/run.sh

## VM-basierte End-to-End-Tests
./scripts/run_openwrt_vm.sh

## Linting
shellcheck openwrt_captive_monitor.sh
shfmt -i 2 -ci -sr -d openwrt_captive_monitor.sh

## Manuelle Tests
/usr/sbin/openwrt_captive_monitor --oneshot --verbose
```

#### VM-Test-Harness

Das Projekt enthält ein umfassendes VM-basiertes Testsystem, das die End-to-End-Validierung automatisiert:

- **Automatisierte OpenWrt VM-Bereitstellung** mit QEMU/KVM
- **Paket-Erstellung und Installation** in isolierter Umgebung
- **Smoke-Tests** für Baseline, Captive Portal und Monitor-Modi
- **Artefakt-Sammlung** für Debugging und Analyse
- **CI/CD-bereit** mit Fallback auf TCG-Emulation

```bash
# Basis VM-Tests
./scripts/run_openwrt_vm.sh

# Benutzerdefinierte Konfiguration
./scripts/run_openwrt_vm.sh --openwrt-version 23.05 --workdir /tmp/test

# CI-Umgebung (ohne KVM)
./scripts/run_openwrt_vm.sh --reuse-vm --no-kvm
```

Siehe [Virtualisierungs-Guide](docs/guides/virtualization.md) für detaillierte VM-Test-Dokumentation.

### Release erstellen

Dieses Projekt verwendet einen **manuellen Release-Workflow** zum Erstellen neuer Releases. Maintainer können Releases auf Abruf über GitHub Actions auslösen.

**Um ein neues Release zu erstellen:**

1. Gehe zu **Actions** → **Manual Release** im GitHub-Repository
2. Klicke auf **"Run workflow"**
3. Konfiguriere das Release (alle Felder sind optional):
   - **Custom version**: Gebe eine Version wie `2025.11.27.1` an, oder lasse es leer für automatische Generierung basierend auf aktuellem Datum
   - **Release notes**: Gebe eigene Release-Notes an, oder lasse es leer für automatische Generierung
   - **Pre-release**: Markiere dieses Kästchen, um das Release als Pre-Release zu kennzeichnen
4. Klicke auf **"Run workflow"**, um den Release-Prozess zu starten

**Was während des Releases passiert:**

Der Workflow wird automatisch:
- Den angegebenen Versions-Tag generieren oder verwenden (`vYYYY.M.D.N`)
- Die Datei `VERSION` und `PKG_VERSION` im Makefile aktualisieren
- Einen Commit mit Versionsänderungen erstellen
- Einen Git-Tag erstellen und pushen
- Das universelle Paket bauen (`arch=all`)
- Das Paket validieren
- Ein GitHub Release mit angehängtem Paket erstellen
- Die `.ipk`-Datei und `SHA256SUMS` zum Release hochladen

**Versionsformat:**
- **Tag:** `vYYYY.M.D.N` (z.B. `v2025.11.27.1`)
- **VERSION-Datei:** `YYYY.M.D.N` (ohne führendes `v`)
- **PKG_VERSION** im Makefile: `YYYY.M.D.N`
- **PKG_RELEASE:** immer `1` für offizielle Releases

> **Beispiel:**
> - Tag: `v2025.11.27.1`
> - `VERSION`-Datei: `2025.11.27.1`
> - `package/openwrt-captive-monitor/Makefile`:
>   - `PKG_VERSION:=2025.11.27.1`
>   - `PKG_RELEASE:=1`

**Workflow-Parameter:**

| Parameter       | Beschreibung                          | Erforderlich | Standard                             |
| --------------- | ------------------------------------- | ------------ | ------------------------------------ |
| `version`       | Benutzerdefinierte Version (z.B. `2025.11.27.1`) | Nein | Auto-Generierung vom aktuellen Datum |
| `release_notes` | Benutzerdefinierte Release-Notes      | Nein         | Auto-Generierung von Git-Commits     |
| `prerelease`    | Als Pre-Release markieren             | Nein         | `false`                              |

Für detaillierte Informationen zum Release-Prozess siehe:
- [Manual Release Workflow](.github/workflows/manual-release.yml)
- [Auto Version Tag Guide](docs/release/AUTO_VERSION_TAG.md)
- [Release Process Documentation](docs/release/RELEASE_PROCESS.md)

### Beitragen

1. Repository forken
2. Feature-Branch erstellen (`git checkout -b feature/amazing-feature`)
3. Änderungen mit Conventional Commits committen (`git commit -m 'feat: add amazing feature'`)
4. Branch pushen (`git push origin feature/amazing-feature`)
5. Pull Request öffnen

Siehe [CONTRIBUTING.md](docs/contributing/CONTRIBUTING.md) für detaillierte Richtlinien.

## 📚 Dokumentation

- [Dokumentations-Index](docs/index.md) - Vollständige Guides und Referenz
- [Schnellstart-Guide](docs/usage/quick-start.md) - In Minuten loslegen
- [Konfigurations-Referenz](docs/configuration/reference.md) - Alle Konfigurationsoptionen
- [Fehlerbehebungs-Guide](docs/guides/troubleshooting.md) - Häufige Probleme und Lösungen
- [Architektur-Übersicht](docs/guides/architecture.md) - Systemdesign und Komponenten
- [Release-Prozess](docs/release/RELEASE_PROCESS.md) - Release-Workflow und Versionierung
- [Release-Wiederherstellung](docs/release/RELEASE_RESTORATION.md) - Fehlende Releases wiederherstellen

## 🤝 Community

### Support

- [GitHub Issues](https://github.com/nagual2/openwrt-captive-monitor/issues) - Bug-Reports und Feature-Requests
- [GitHub Discussions](https://github.com/nagual2/openwrt-captive-monitor/discussions) - Allgemeine Fragen und Hilfe
- [Dokumentation](docs/index.md) - Umfassende Guides und Referenz

### Sicherheit

- [Sicherheitsrichtlinie](.github/SECURITY.md) - Meldung von Sicherheitslücken
- [Sicherheitshinweise](https://github.com/nagual2/openwrt-captive-monitor/security/advisories) - Sicherheitsbenachrichtigungen
- [Sicherheits-Scanning](docs/SECURITY_SCANNING.md) - Dokumentation zum automatisierten Sicherheits-Scanning

### Mitwirken

- [Beitrags-Guide](docs/contributing/CONTRIBUTING.md) - Entwicklungsrichtlinien und PR-Prozess
- [Verhaltenskodex](docs/contributing/CODE_OF_CONDUCT.md) - Community-Richtlinien
- [Projekt-Management](docs/project/management.md) - Roadmap und Release-Prozess

## 📊 Projektstatus

### Aktuelles Release

- **Version**: v1.0.6 (Siehe [Releases-Seite](https://github.com/nagual2/openwrt-captive-monitor/releases) für Details)
- **Lizenz**: [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
- **Plattform**: [![OpenWrt](https://img.shields.io/badge/OpenWrt-21.02%2B-blue.svg)](https://openwrt.org/)

### Kompatibilität

| OpenWrt-Version | Status | Hinweise |
| --------------- | ------ | -------- |
| 21.02 (LTS) | ✅ Unterstützt | Verwendet iptables-Backend |
| 22.03 (LTS) | ✅ Unterstützt | Auto-Erkennung des Backends |
| 23.05 (Stable) | ✅ Unterstützt | Volle nftables-Unterstützung |
| 24.10 (Development) | ✅ Unterstützt | Neueste Features |

| Architektur | Status | Paket |
| ----------- | ------ | ----- |
| mips_24kc | ✅ Unterstützt | `openwrt-captive-monitor_*_mips_24kc.ipk` |
| aarch64_cortex-a53 | ✅ Unterstützt | `openwrt-captive-monitor_*_aarch64_cortex-a53.ipk` |
| x86_64 | ✅ Unterstützt | `openwrt-captive-monitor_*_x86_64.ipk` |
| all | ✅ Universal | `openwrt-captive-monitor_*_all.ipk` |

## 📄 Lizenz

Dieses Projekt ist unter der [MIT License](LICENSE) lizenziert - siehe die [LICENSE](LICENSE)-Datei für Details.

## 🙏 Danksagungen

- **OpenWrt Community** - Für die exzellente Router-Firmware und Tools
- **BusyBox-Projekt** - Bereitstellung essentieller Unix-Utilities für eingebettete Systeme
- **Mitwirkende** - Alle, die geholfen haben, dieses Projekt zu verbessern

## 🔗 Verwandte Projekte

- [uspot](https://github.com/f00b4r0/uspot) - Voll ausgestattetes Captive Portal für OpenWrt
- [apfree-wifidog](https://github.com/liudf0716/apfree-wifidog) - Hochleistungs-Captive-Portal
- [CaptivePortalAutologin](https://github.com/jsparber/CaptivePortalAutologin) - Android Auto-Login-App

---

<div align="center">
[📖 Dokumentation](docs/) • [🐛 Issues](https://github.com/nagual2/openwrt-captive-monitor/issues) • [💬 Discussions](https://github.com/nagual2/openwrt-captive-monitor/discussions)

Mit ❤️ für die OpenWrt Community gemacht

</div>
