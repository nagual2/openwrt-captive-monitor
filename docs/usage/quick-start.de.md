# Schnellstart-Anleitung

---

## 🌐 Sprache

[English](quick-start.md) | **[Deutsch](quick-start.de.md)** | [Русский](quick-start.ru.md)

---

Bringen Sie **openwrt-captive-monitor** auf Ihrem OpenWrt-Router in wenigen Minuten zum Laufen.

## 🎯 Voraussetzungen

- OpenWrt-Router (21.02+ empfohlen)
- Root-Zugang zum Router
- Grundlegendes Verständnis der OpenWrt-UCI-Konfiguration

## 📦 Option 1: Vorgefertigtes Paket installieren (Empfohlen)

1. **Laden Sie das neueste Paket herunter**:
   ```bash
   wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_*.ipk
   ```

2. **Übertragen Sie es auf den Router**:
   ```bash
   scp openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
   ```

3. **Installieren Sie es auf dem Router**:
   ```bash
   ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
   ```

## 🔧 Option 2: Aus Quellcode erstellen

Detaillierte Build-Anweisungen mit dem OpenWrt SDK finden Sie in der [Installationsanleitung](installation.md).

## ⚙️ Grundkonfiguration

1. **Aktivieren Sie den Dienst**:
   ```bash
   ssh root@192.168.1.1
   uci set captive-monitor.config.enabled='1'
   uci commit captive-monitor
   ```

2. **Konfigurieren Sie WiFi-Schnittstellen** (falls abweichend von den Standardwerten):
   ```bash
   uci set captive-monitor.config.wifi_interface='phy1-sta0'
   uci set captive-monitor.config.wifi_logical='wwan'
   uci commit captive-monitor
   ```

3. **Starten Sie den Dienst**:
   ```bash
   /etc/init.d/captive-monitor enable
   /etc/init.d/captive-monitor start
   ```

## ✅ Installation überprüfen

Überprüfen Sie den Dienststatus:
```bash
logread | grep captive-monitor
```

Sie sollten Logs sehen, die anzeigen, dass der Dienst die Konnektivität überwacht.

## 🎉 Sie sind fertig!

Der Captive-Monitor wird nun:
- Kontinuierlich die Internetkonnektivität überwachen
- Captive Portals automatisch erkennen
- LAN-Clients bei Bedarf zum Portal umleiten
- Automatisch aufräumen, sobald der Internetzugang wiederhergestellt ist

## 🔍 Nächste Schritte

- [Erweiterte Konfiguration](../configuration/advanced-config.md) - Feinabstimmung der Überwachungsintervalle und Erkennungsmethoden
- [Fehlerbehebung](../guides/troubleshooting.md) - Häufige Probleme und Lösungen
- [Captive-Portal-Schritt-für-Schritt-Anleitung](../guides/captive-portal-walkthrough.md) - End-to-End-Verwendungsbeispiel

## 🆘 Brauchen Sie Hilfe?

- Schauen Sie in die [FAQ](../project/faq.md) für häufige Fragen
- Besuchen Sie unseren [Support-Leitfaden](../../.github/SUPPORT.md)
- Eröffnen Sie ein [Problem auf GitHub](https://github.com/nagual2/openwrt-captive-monitor/issues)