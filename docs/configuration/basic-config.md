# Basic Configuration

This guide covers the essential configuration options for **openwrt-captive-monitor** to get you started quickly.

## 📋 Core Configuration Options

The main configuration is stored in `/etc/config/captive-monitor`. Here are the most important settings:

### Enable/Disable Service

```uci
config captive_monitor 'config'
    option enabled '1'    # Set to '1' to enable, '0' to disable
```

### Operation Mode

```uci
config captive_monitor 'config'
    option mode 'monitor'    # 'monitor' (default) or 'oneshot'
```

- **monitor**: Continuous monitoring with specified interval
- **oneshot**: Single check and exit (useful for cron-based execution)

### WiFi Interface Configuration

```uci
config captive_monitor 'config'
    option wifi_interface 'phy1-sta0'    # Physical WiFi interface
    option wifi_logical 'wwan'          # Logical OpenWrt interface name
```

### Monitoring Settings

```uci
config captive_monitor 'config'
    option monitor_interval '60'        # Check interval in seconds
    option ping_servers '1.1.1.1 8.8.8.8 9.9.9.9'    # Servers to ping
```

### Captive Portal Detection

```uci
config captive_monitor 'config'
    option captive_check_urls 'http://connectivitycheck.gstatic.com/generate_204 http://detectportal.firefox.com/success.txt'
```

### Logging

```uci
config captive_monitor 'config'
    option enable_syslog '1'    # Enable syslog logging
```

---

## 🎯 Quick Configuration Examples

### Basic Setup (Most Common)

```uci
config captive_monitor 'config'
    option enabled '1'
    option mode 'monitor'
    option wifi_interface 'phy1-sta0'
    option wifi_logical 'wwan'
    option monitor_interval '60'
    option enable_syslog '1'
```

### Aggressive Monitoring (Frequent Checks)

```uci
config captive_monitor 'config'
    option enabled '1'
    option mode 'monitor'
    option monitor_interval '30'        # Check every 30 seconds
    option ping_servers '1.1.1.1 8.8.8.8'
```

### Conservative Setup (Less Frequent)

```uci
config captive_monitor 'config'
    option enabled '1'
    option mode 'monitor'
    option monitor_interval '300'       # Check every 5 minutes
    option ping_servers '8.8.8.8'       # Single server
```

### Oneshot Mode (Manual/Cron-based)

```uci
config captive_monitor 'config'
    option enabled '1'
    option mode 'oneshot'
    option wifi_interface 'phy1-sta0'
    option wifi_logical 'wwan'
```

---

## ⚙️ Applying Configuration Changes

### Method 1: UCI Commands

```bash
# Set configuration
uci set captive-monitor.config.enabled='1'
uci set captive-monitor.config.mode='monitor'
uci set captive-monitor.config.monitor_interval='60'
uci commit captive-monitor

# Restart service
/etc/init.d/captive-monitor restart
```

### Method 2: Edit Configuration File

```bash
# Edit the configuration file
vi /etc/config/captive-monitor

# Apply changes
/etc/init.d/captive-monitor restart
```

### Method 3: Environment Variables (Temporary)

```bash
# Override configuration for single run
export MONITOR_INTERVAL=30
/usr/sbin/openwrt_captive_monitor --oneshot
```

---

## 🔍 Interface Detection

### Automatic Detection (Default)

The service automatically detects:
- LAN interface (usually `br-lan`)
- LAN IP address
- IPv6 support
- Firewall backend (iptables/nftables)

### Manual Interface Specification

If automatic detection fails, you can specify interfaces manually:

```uci
config captive_monitor 'config'
    option lan_interface 'br-lan'        # LAN bridge interface
    option lan_ip '192.168.1.1'          # LAN IP address
    option lan_ipv6 'fd00::1'           # LAN IPv6 address (optional)
    option firewall_backend 'iptables'   # Force specific backend
```

---

## 📊 Monitoring Intervals Guide

| Interval | Use Case | Pros | Cons |
|----------|----------|------|------|
| 30 seconds | High-availability environments | Fast detection | Higher resource usage |
| 60 seconds | Standard home/office use | Balanced performance | Moderate resource usage |
| 300 seconds | Resource-constrained devices | Low resource usage | Slower detection |
| 900 seconds | Minimal monitoring | Very low resource usage | Slow detection |

---

## 🌐 Network Configuration Examples

### Typical Home Router

```uci
config captive_monitor 'config'
    option enabled '1'
    option mode 'monitor'
    option wifi_interface 'phy0-sta0'
    option wifi_logical 'wwan'
    option monitor_interval '60'
    option ping_servers '1.1.1.1 8.8.8.8'
```

### Travel Router (Multiple Networks)

```uci
config captive_monitor 'config'
    option enabled='1'
    option mode='monitor'
    option monitor_interval='45'
    option ping_servers='1.1.1.1 8.8.8.8 208.67.222.222'
    option captive_check_urls='http://connectivitycheck.gstatic.com/generate_204 http://detectportal.firefox.com/success.txt http://captive.apple.com/hotspot-detect.html'
```

### Enterprise Environment

```uci
config captive_monitor 'config'
    option enabled='1'
    option mode='monitor'
    option wifi_interface='phy1-sta0'
    option wifi_logical='wan'
    option monitor_interval='30'
    option ping_servers='8.8.8.8 1.1.1.1 208.67.222.222'
    option enable_syslog='1'
```

---

## ✅ Configuration Validation

### Check Current Configuration

```bash
# Show current configuration
uci show captive-monitor

# Validate configuration syntax
uci -c /tmp validate captive-monitor
```

### Test Configuration

```bash
# Test with oneshot mode
/usr/sbin/openwrt_captive_monitor --oneshot

# Check logs for errors
logread | grep captive-monitor | tail -20
```

### Verify Service Status

```bash
# Check if service is running
/etc/init.d/captive-monitor status

# Check recent logs
logread | grep captive-monitor | tail -10
```

---

## 🔄 Common Configuration Changes

### Change Monitoring Frequency

```bash
uci set captive-monitor.config.monitor_interval='120'
uci commit captive-monitor
/etc/init.d/captive-monitor restart
```

### Add More Ping Servers

```bash
uci add_list captive-monitor.config.ping_servers='208.67.222.222'
uci add_list captive-monitor.config.ping_servers='9.9.9.9'
uci commit captive-monitor
/etc/init.d/captive-monitor restart
```

### Switch to Oneshot Mode

```bash
uci set captive-monitor.config.mode='oneshot'
uci commit captive-monitor
/etc/init.d/captive-monitor restart
```

---

## 🆘 Troubleshooting Configuration

### Configuration Not Applied

```bash
# Check if configuration is valid
uci show captive-monitor

# Force reload
uci commit captive-monitor
/etc/init.d/captive-monitor restart

# Check for syntax errors
logread | grep captive-monitor
```

### Service Won't Start

```bash
# Check if enabled
uci get captive-monitor.config.enabled

# Check configuration syntax
uci -c /tmp validate captive-monitor

# Manual test
/usr/sbin/openwrt_captive_monitor --help
```

### Interface Detection Issues

```bash
# Check available interfaces
ip link show

# Check network status
ifstatus wan
ifstatus lan

# Manually specify if needed
uci set captive-monitor.config.lan_interface='br-lan'
uci commit captive-monitor
```

For advanced configuration options, see the [Advanced Configuration Guide](advanced-config.md).