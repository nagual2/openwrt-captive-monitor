# Quick Start Guide

Get **openwrt-captive-monitor** up and running on your OpenWrt router in just a few minutes.

## 🎯 Prerequisites

- OpenWrt router (21.02+ recommended)
- Root access to the router
- Basic understanding of OpenWrt UCI configuration

## 📦 Option 1: Install Prebuilt Package (Recommended)

1. **Download the latest package**:
   ```bash
   wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_*.ipk
   ```

2. **Transfer to router**:
   ```bash
   scp openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
   ```

3. **Install on router**:
   ```bash
   ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
   ```

## 🔧 Option 2: Build from Source

See the [Installation Guide](installation.md) for detailed build instructions using the OpenWrt SDK.

## ⚙️ Basic Configuration

1. **Enable the service**:
   ```bash
   ssh root@192.168.1.1
   uci set captive-monitor.config.enabled='1'
   uci commit captive-monitor
   ```

2. **Configure WiFi interfaces** (if different from defaults):
   ```bash
   uci set captive-monitor.config.wifi_interface='phy1-sta0'
   uci set captive-monitor.config.wifi_logical='wwan'
   uci commit captive-monitor
   ```

3. **Start the service**:
   ```bash
   /etc/init.d/captive-monitor enable
   /etc/init.d/captive-monitor start
   ```

## ✅ Verify Installation

Check the service status:
```bash
logread | grep captive-monitor
```

You should see logs indicating the service is monitoring connectivity.

## 🎉 You're Done!

The captive monitor will now:
- Continuously monitor internet connectivity
- Automatically detect captive portals
- Redirect LAN clients to the portal when needed
- Clean up automatically once internet access is restored

## 🔍 Next Steps

- [Advanced Configuration](../configuration/advanced-config.md) - Fine-tune monitoring intervals and detection methods
- [Troubleshooting](../guides/troubleshooting.md) - Common issues and solutions
- [Captive Portal Walkthrough](../guides/captive-portal-walkthrough.md) - End-to-end usage example

## 🆘 Need Help?

- Check the [FAQ](../project/faq.md) for common questions
- Visit our [Support Guide](../../.github/SUPPORT.md)
- Open an [issue on GitHub](https://github.com/nagual2/openwrt-captive-monitor/issues)
