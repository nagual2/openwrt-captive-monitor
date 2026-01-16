# openwrt-captive-monitor


[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub release](https://img.shields.io/github/release/nagual2/openwrt-captive-monitor.svg)](https://github.com/nagual2/openwrt-captive-monitor/releases)
[![GitHub stars](https://img.shields.io/github/stars/nagual2/openwrt-captive-monitor.svg?style=social)](https://github.com/nagual2/openwrt-captive-monitor/stargazers)

---

## 🌐 Language

**English** | [Deutsch](README.de.md) | [Русский](README.ru.md)

---

## ✨ Features

- **🔍 Automatic Authentication** - Automatically authenticates against Conn4 captive portals (e.g. Leonardo Hotels)
- **⚡ Lightweight** - Simple shell script (~10KB), no heavy dependencies
- **🔄 Session Maintenance** - Cron-based checks ensure you stay online
- **🛡️ Secure** - Uses standard system tools (`curl`)

> **Note**: This package is specifically designed for Conn4-based captive portals.

## 🚀 Quick Start

### Prerequisites

- OpenWrt 21.02+ (or any system with `opkg`, `curl` and `cron`)
- `curl` package installed (automatically handled by dependency)

### Installation

#### Option 1: Prebuilt Package (Recommended)

```bash
## Download latest package
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_*.ipk

## Install on router
scp openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

The package will automatically:
1. Install the auth script to `/usr/sbin/auth_conn4.sh`
2. Add a cron job to `/etc/crontabs/root` to run every minute
3. Restart the cron service

#### Option 2: Build from Source

```bash
## Clone repository
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor

## Build package
scripts/build_ipk.sh --arch all

## Install
scp dist/opkg/all/openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

## 🔧 Configuration

Configuration is zero-touch. The script detects the portal URL automatically.

To disable or change the schedule, edit the root crontab:

```bash
crontab -e
```

Default entry:
```cron
*/1 * * * * /usr/sbin/auth_conn4.sh
```

## 🔍 Troubleshooting

**Check logs:**
```bash
logread | grep conn4_auth
```

**Run manually:**
```bash
sh /usr/sbin/auth_conn4.sh
```

**Verify installation:**
```bash
ls -l /usr/sbin/auth_conn4.sh
grep auth_conn4 /etc/crontabs/root
```

## 📄 License

This project is licensed under the [MIT License](LICENSE).
