# Installation Guide

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---


This guide covers the different ways to install **openwrt-captive-monitor** on your OpenWrt router.

## 📦 Installation Options

| Method | Best For | Complexity | Maintenance |
|--------|----------|------------|-------------|
| Prebuilt Package | Quick deployment, production use | ⭐ Easy | Automatic updates |
| SDK Build | Custom builds, development | ⭐⭐ Medium | Manual updates |
| Local Build | Testing, custom modifications | ⭐⭐⭐ Hard | Manual updates |

---

## 🚀 Method 1: Prebuilt Package (Recommended)

### Step 1: Download Package

Visit the [GitHub Releases](https://github.com/nagual2/openwrt-captive-monitor/releases) page and download the latest `.ipk` file for your architecture.

```bash
## Example for the latest release
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_*.ipk
```

### Step 2: Transfer to Router

```bash
scp openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
```

### Step 3: Install Package

```bash
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

### Step 4: Configure and Start

```bash
ssh root@192.168.1.1 <<'EOSSH'
## Enable the service
uci set captive-monitor.config.enabled='1'
uci commit captive-monitor

## Start the service
/etc/init.d/captive-monitor enable
/etc/init.d/captive-monitor start

## Check status
logread | grep captive-monitor | tail -10
EOSSH
```

---

## 🔧 Method 2: OpenWrt SDK Build

### Prerequisites

- OpenWrt SDK matching your target architecture
- Build environment (Linux/macOS/WSL)

### Step 1: Download OpenWrt SDK

```bash
## Example for OpenWrt 22.03.5, ath79 target
wget https://downloads.openwrt.org/releases/22.03.5/targets/ath79/generic/openwrt-sdk-22.03.5-ath79-generic_gcc-11.2.0_musl.Linux-x86_64.tar.xz
tar -xf openwrt-sdk-*.tar.xz
cd openwrt-sdk-*
```

### Step 2: Add Package Source

```bash
## Clone this repository into the package directory
git clone https://github.com/nagual2/openwrt-captive-monitor.git package/openwrt-captive-monitor
```

### Step 3: Build Package

```bash
## Update package feeds
./scripts/feeds update -a
./scripts/feeds install openwrt-captive-monitor

## Build the package
make package/openwrt-captive-monitor/compile V=s
```

### Step 4: Locate and Install

The built package will be at:
```
bin/packages/<arch>/base/openwrt-captive-monitor_<version>_<arch>.ipk
```

```bash
## Transfer and install
scp bin/packages/*/base/openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

---

## 🛠️ Method 3: Local Build (Development)

### Prerequisites

Install build dependencies:

```bash
## Debian/Ubuntu
sudo apt-get update
sudo apt-get install -y binutils busybox gzip pigz tar xz-utils

## Or use the build script that checks dependencies
scripts/build_ipk.sh --check-deps
```

### Step 1: Build Package

```bash
## Build for specific architecture
scripts/build_ipk.sh --arch mips_24kc

## Or build for all architectures
scripts/build_ipk.sh --arch all
```

### Step 2: Install

```bash
## The package is created in dist/opkg/<arch>/
scp dist/opkg/*/openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
```

---

## 🔍 Architecture Compatibility

| Architecture | OpenWrt Target | Package Name |
|--------------|---------------|--------------|
| `all` | Universal | `openwrt-captive-monitor_*_all.ipk` |
| `mips_24kc` | ath79, ramips | `openwrt-captive-monitor_*_mips_24kc.ipk` |
| `aarch64_cortex-a53` | filogic, mediatek | `openwrt-captive-monitor_*_aarch64_cortex-a53.ipk` |
| `x86_64` | x86/64 | `openwrt-captive-monitor_*_x86_64.ipk` |

**Note**: The `all` architecture package works on most systems since this is a shell script package.

---

## 📋 Post-Installation Verification

### 1. Check Package Installation

```bash
ssh root@192.168.1.1 "opkg list-installed | grep captive-monitor"
```

### 2. Verify Service Files

```bash
ssh root@192.168.1.1 <<'EOSSH'
## Check executable
ls -la /usr/sbin/openwrt_captive_monitor

## Check init script
ls -la /etc/init.d/captive-monitor

## Check configuration
cat /etc/config/captive-monitor
EOSSH
```

### 3. Test Service

```bash
ssh root@192.168.1.1 <<'EOSSH'
## Enable service
uci set captive-monitor.config.enabled='1'
uci commit captive-monitor

## Start service
/etc/init.d/captive-monitor start

## Check logs
logread | grep captive-monitor | tail -10
EOSSH
```

---

## 🔄 Upgrading

### From Prebuilt Package

```bash
ssh root@192.168.1.1 <<'EOSSH'
## Download and install new version
wget -O /tmp/new-package.ipk "https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_*.ipk"
opkg install /tmp/new-package.ipk

## Restart service
/etc/init.d/captive-monitor restart
EOSSH
```

### From Source

Follow the same build process as above, then install the new package. The upgrade process preserves your UCI configuration.

---

## 🗑️ Uninstallation

```bash
ssh root@192.168.1.1 <<'EOSSH'
## Stop and disable service
/etc/init.d/captive-monitor stop
/etc/init.d/captive-monitor disable

## Remove package
opkg remove openwrt-captive-monitor

## Clean up configuration (optional)
uci delete captive-monitor.config
uci commit captive-monitor
EOSSH
```

---

## 🆘 Troubleshooting Installation

### Package Installation Fails

```bash
## Check package dependencies
opkg info openwrt-captive-monitor

## Check available space
df -h

## Check package integrity
file /tmp/openwrt-captive-monitor_*.ipk
```

### Service Won't Start

```bash
## Check service status
/etc/init.d/captive-monitor status

## Check logs
logread | grep captive-monitor

## Manual test
/usr/sbin/openwrt_captive_monitor --help
```

### Configuration Issues

```bash
## Validate UCI configuration
uci show captive-monitor

## Reset to defaults
uci revert captive-monitor
```

For more troubleshooting tips, see the [Troubleshooting Guide](../guides/troubleshooting.md).
