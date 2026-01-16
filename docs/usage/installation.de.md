# Installationsanleitung

---

## 🌐 Sprache

[English](installation.md) | **[Deutsch](installation.de.md)** | [Русский](installation.ru.md)

---

Diese Anleitung behandelt die verschiedenen Möglichkeiten zur Installation von **openwrt-captive-monitor** auf Ihrem OpenWrt-Router.

## 📦 Installationsoptionen

| Methode | Am besten für | Komplexität | Wartung |
|---------|---------------|-------------|---------|
| Vorgefertigtes Paket | Schnelle Bereitstellung, Produktionsnutzung | ⭐ Einfach | Automatische Updates |
| SDK-Build | Benutzerdefinierte Builds, Entwicklung | ⭐⭐ Mittel | Manuelle Updates |
| Lokaler Build | Testen, benutzerdefinierte Änderungen | ⭐⭐⭐ Schwierig | Manuelle Updates |

---

## 🚀 Methode 1: Vorgefertigtes Paket (Empfohlen)

### Schritt 1: Paket herunterladen

Besuchen Sie die [GitHub Releases](https://github.com/nagual2/openwrt-captive-monitor/releases) Seite und laden Sie die neueste `.ipk`-Datei für Ihre Architektur herunter.

```bash
## Beispiel für die neueste Version
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_*.ipk
```

### Schritt 2: Zum Router übertragen

```bash
scp openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
```

### Schritt 3: Paket installieren

```bash
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

### Schritt 4: Konfigurieren und starten

```bash
ssh root@192.168.1.1 <<'EOSSH'
## Dienst aktivieren
uci set captive-monitor.config.enabled='1'
uci commit captive-monitor

## Dienst starten
/etc/init.d/captive-monitor enable
/etc/init.d/captive-monitor start

## Status überprüfen
logread | grep captive-monitor | tail -10
EOSSH
```

---

## 🔧 Methode 2: OpenWrt SDK-Build

### Voraussetzungen

- OpenWrt SDK, das Ihrer Zielarchitektur entspricht
- Build-Umgebung (Linux/macOS/WSL)

### Schritt 1: OpenWrt SDK herunterladen

```bash
## Beispiel für OpenWrt 22.03.5, ath79 Ziel
wget https://downloads.openwrt.org/releases/22.03.5/targets/ath79/generic/openwrt-sdk-22.03.5-ath79-generic_gcc-11.2.0_musl.Linux-x86_64.tar.xz
tar -xf openwrt-sdk-*.tar.xz
cd openwrt-sdk-*
```

### Schritt 2: Paketquelle hinzufügen

```bash
## Klonen Sie dieses Repository in das package-Verzeichnis
git clone https://github.com/nagual2/openwrt-captive-monitor.git package/openwrt-captive-monitor
```

### Schritt 3: Paket bauen

```bash
## Paket-Feeds aktualisieren
./scripts/feeds update -a
./scripts/feeds install openwrt-captive-monitor

## Paket bauen
make package/openwrt-captive-monitor/compile V=s
```

### Schritt 4: Suchen und installieren

Das gebaute Paket befindet sich unter:
```
bin/packages/<arch>/base/openwrt-captive-monitor_<version>_<arch>.ipk
```

```bash
## Übertragen und installieren
scp bin/packages/*/base/openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

---

## 🛠️ Methode 3: Lokaler Build (Entwicklung)

### Voraussetzungen

Installieren Sie Build-Abhängigkeiten:

```bash
## Debian/Ubuntu
sudo apt-get update
sudo apt-get install -y binutils busybox gzip pigz tar xz-utils

## Oder verwenden Sie das Build-Skript, das Abhängigkeiten überprüft
scripts/build_ipk.sh --check-deps
```

### Schritt 1: Paket bauen

```bash
## Für spezifische Architektur bauen
scripts/build_ipk.sh --arch mips_24kc

## Oder für alle Architekturen bauen
scripts/build_ipk.sh --arch all
```

### Schritt 2: Installieren

```bash
## Das Paket wird in dist/opkg/<arch>/ erstellt
scp dist/opkg/*/openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

---

## 🔍 Architektur-Kompatibilität

| Architektur | OpenWrt-Ziel | Paketname |
|-------------|-------------|-----------|
| `all` | Universell | `openwrt-captive-monitor_*_all.ipk` |
| `mips_24kc` | ath79, ramips | `openwrt-captive-monitor_*_mips_24kc.ipk` |
| `aarch64_cortex-a53` | filogic, mediatek | `openwrt-captive-monitor_*_aarch64_cortex-a53.ipk` |
| `x86_64` | x86/64 | `openwrt-captive-monitor_*_x86_64.ipk` |

**Hinweis**: Das `all` Architektur-Paket funktioniert auf den meisten Systemen, da dies ein Shell-Skript-Paket ist.

---

## 📋 Überprüfung nach der Installation

### 1. Paketinstallation überprüfen

```bash
ssh root@192.168.1.1 "opkg list-installed | grep captive-monitor"
```

### 2. Dienstdateien überprüfen

```bash
ssh root@192.168.1.1 <<'EOSSH'
## Ausführbare Datei überprüfen
ls -la /usr/sbin/openwrt_captive_monitor

## Init-Skript überprüfen
ls -la /etc/init.d/captive-monitor

## Konfiguration überprüfen
cat /etc/config/captive-monitor
EOSSH
```

### 3. Dienst testen

```bash
ssh root@192.168.1.1 <<'EOSSH'
## Dienst aktivieren
uci set captive-monitor.config.enabled='1'
uci commit captive-monitor

## Dienst starten
/etc/init.d/captive-monitor start

## Protokolle überprüfen
logread | grep captive-monitor | tail -10
EOSSH
```

---

## 🔄 Upgrade

### Aus vorgefertigtem Paket

```bash
ssh root@192.168.1.1 <<'EOSSH'
## Neue Version herunterladen und installieren
wget -O /tmp/new-package.ipk "https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_*.ipk"
opkg install /tmp/new-package.ipk

## Dienst neu starten
/etc/init.d/captive-monitor restart
EOSSH
```

### Aus dem Quellcode

Folgen Sie demselben Build-Prozess wie oben, installieren Sie dann das neue Paket. Der Upgrade-Prozess bewahrt Ihre UCI-Konfiguration.

---

## 🗑️ Deinstallation

```bash
ssh root@192.168.1.1 <<'EOSSH'
## Dienst stoppen und deaktivieren
/etc/init.d/captive-monitor stop
/etc/init.d/captive-monitor disable

## Paket entfernen
opkg remove openwrt-captive-monitor

## Konfiguration bereinigen (optional)
uci delete captive-monitor.config
uci commit captive-monitor
EOSSH
```

---

## 🆘 Fehlerbehebung bei der Installation

### Paketinstallation schlägt fehl

```bash
## Paketabhängigkeiten überprüfen
opkg info openwrt-captive-monitor

## Verfügbaren Speicherplatz überprüfen
df -h

## Paketintegrität überprüfen
file /tmp/openwrt-captive-monitor_*.ipk
```

### Dienst startet nicht

```bash
## Protokolle überprüfen
logread | grep conn4_auth

## Manueller Test
sh /usr/sbin/auth_conn4.sh
```

### Konfigurationsprobleme

```bash
## Cron-Job überprüfen
cat /etc/cron.d/auth_conn4
```

Weitere Tipps zur Fehlerbehebung finden Sie in der [Anleitung zur Fehlerbehebung](../guides/troubleshooting.md).
