# Configuration Reference

Complete reference for all configuration options available in **openwrt-captive-monitor**, including UCI settings, environment variables, and command-line flags.

## 📋 Configuration Methods

The service supports three configuration methods, applied in order of precedence:

1. **Command-line flags** (highest priority)
2. **Environment variables**
3. **UCI configuration** (lowest priority, default)

---

## 🔧 UCI Configuration

All UCI settings are stored in `/etc/config/captive-monitor`:

```uci
config captive_monitor 'config'
    # Core settings
    option enabled '0'                    # Enable/disable service
    option mode 'monitor'                 # Operation mode
    option wifi_interface 'phy1-sta0'     # Physical WiFi interface
    option wifi_logical 'wwan'            # Logical OpenWrt interface
    option monitor_interval '60'          # Monitoring interval (seconds)
    
    # Network settings
    option lan_interface ''               # LAN interface (auto-detect)
    option lan_ip ''                      # LAN IP address (auto-detect)
    option lan_ipv6 ''                    # LAN IPv6 address (auto-detect)
    option firewall_backend 'auto'        # Firewall backend
    
    # Connectivity checks
    option ping_servers '1.1.1.1 8.8.8.8 9.9.9.9'    # Ping servers
    option captive_check_urls 'http://connectivitycheck.gstatic.com/generate_204 http://detectportal.firefox.com/success.txt'
    
    # Timing settings
    option ping_timeout '2'               # Ping timeout (seconds)
    option http_probe_timeout '5'         # HTTP probe timeout (seconds)
    option gateway_check_retries '2'      # Gateway check retries
    option internet_check_retries '2'     # Internet check retries
    option internet_check_delay '3'       # Delay between retries (seconds)
    
    # Logging
    option enable_syslog '1'              # Enable syslog logging
```

### Core Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `0` | Enable/disable the captive monitor service |
| `mode` | string | `monitor` | Operation mode: `monitor` (continuous) or `oneshot` (single check) |
| `wifi_interface` | string | `phy1-sta0` | Physical WiFi interface name |
| `wifi_logical` | string | `wwan` | Logical OpenWrt interface name |
| `monitor_interval` | integer | `60` | Monitoring interval in seconds |

### Network Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `lan_interface` | string | `auto` | LAN interface name (empty = auto-detect) |
| `lan_ip` | string | `auto` | LAN IPv4 address (empty = auto-detect) |
| `lan_ipv6` | string | `auto` | LAN IPv6 address (empty = auto-detect) |
| `firewall_backend` | string | `auto` | Firewall backend: `auto`, `iptables`, or `nftables` |

### Connectivity Checks

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `ping_servers` | string | `1.1.1.1 8.8.8.8 9.9.9.9` | Space-separated list of ping servers |
| `captive_check_urls` | string | See default | Space-separated list of captive portal detection URLs |

### Timing Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `ping_timeout` | integer | `2` | Ping timeout in seconds |
| `http_probe_timeout` | integer | `5` | HTTP probe timeout in seconds |
| `gateway_check_retries` | integer | `2` | Number of gateway check retries |
| `internet_check_retries` | integer | `2` | Number of internet check retries |
| `internet_check_delay` | integer | `3` | Delay between retries in seconds |

### Logging Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enable_syslog` | boolean | `1` | Enable syslog logging |

---

## 🌍 Environment Variables

All UCI options can be overridden using environment variables. Variable names follow the pattern:

```bash
# UCI option: wifi_interface
# Environment variable: WIFI_INTERFACE
export WIFI_INTERFACE="phy1-sta0"

# UCI option: monitor_interval  
# Environment variable: MONITOR_INTERVAL
export MONITOR_INTERVAL="30"
```

### Complete Environment Variable List

```bash
# Core settings
export CAPTIVE_MONITOR_ENABLED="1"           # Override enabled
export CAPTIVE_MONITOR_MODE="monitor"        # Override mode
export WIFI_INTERFACE="phy1-sta0"            # WiFi interface
export WIFI_LOGICAL="wwan"                    # Logical interface
export MONITOR_INTERVAL="60"                  # Monitoring interval

# Network settings
export LAN_INTERFACE="br-lan"                 # LAN interface
export LAN_IP="192.168.1.1"                   # LAN IPv4 address
export LAN_IPV6="fd00::1"                     # LAN IPv6 address
export REQUESTED_FIREWALL_BACKEND="iptables"  # Firewall backend

# Connectivity checks
export PING_SERVERS="1.1.1.1 8.8.8.8"        # Ping servers
export CAPTIVE_CHECK_URLS="http://example.com" # Captive check URLs
export INTERNET_HTTP_PROBES="http://example.com" # HTTP probe URLs

# Timing settings
export PING_TIMEOUT="2"                       # Ping timeout
export HTTP_PROBE_TIMEOUT="5"                 # HTTP probe timeout
export GATEWAY_CHECK_RETRIES="2"              # Gateway check retries
export INTERNET_CHECK_RETRIES="2"             # Internet check retries
export INTERNET_CHECK_DELAY="3"               # Retry delay

# Logging
export ENABLE_SYSLOG="1"                      # Enable syslog
```

### Special Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CAPTIVE_MONITOR_ENABLED` | `0` | Override service enable/disable |
| `INTERNET_HTTP_PROBES` | Default URLs | Set to empty string `""` to disable HTTP probes |
| `CAPTIVE_CURL_TIMEOUT` | `5` | cURL timeout for captive portal detection |
| `DNS_LOOKUP_TIMEOUT` | `5` | DNS lookup timeout |

---

## ⌨️ Command-Line Flags

Command-line flags provide the highest priority configuration and are useful for testing and manual execution.

### Basic Usage

```bash
# Display help
/usr/sbin/openwrt_captive_monitor --help

# Oneshot mode (single check)
/usr/sbin/openwrt_captive_monitor --oneshot

# Monitor mode (continuous)
/usr/sbin/openwrt_captive_monitor --monitor

# Custom interface
/usr/sbin/openwrt_captive_monitor --oneshot --interface wlan0 --logical wan

# Custom interval
/usr/sbin/openwrt_captive_monitor --monitor --interval 30
```

### Complete Flag List

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--oneshot` | `-o` | flag | - | Run once and exit |
| `--monitor` | `-m` | flag | - | Run continuously in monitor mode |
| `--interface` | `-i` | string | `phy1-sta0` | WiFi interface name |
| `--logical` | `-l` | string | `wwan` | Logical interface name |
| `--interval` | `-t` | integer | `60` | Monitoring interval (seconds) |
| `--help` | `-h` | flag | - | Display help message |
| `--version` | `-v` | flag | - | Display version information |

### Advanced Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--ping-servers` | string | `1.1.1.1 8.8.8.8 9.9.9.9` | Space-separated ping servers |
| `--captive-urls` | string | Default URLs | Captive portal detection URLs |
| `--lan-interface` | string | auto | LAN interface name |
| `--lan-ip` | string | auto | LAN IPv4 address |
| `--firewall-backend` | string | auto | Firewall backend (iptables/nftables) |
| `--syslog-only` | flag | false | Only log to syslog (no stdout) |
| `--verbose` | flag | false | Enable verbose logging |

---

## 📊 Configuration Precedence

Configuration is applied in the following order (highest to lowest priority):

1. **Command-line flags**
2. **Environment variables**  
3. **UCI configuration**

### Example Precedence

```bash
# UCI configuration sets interval to 60
uci set captive-monitor.config.monitor_interval='60'

# Environment variable overrides to 30
export MONITOR_INTERVAL="30"

# Command-line flag overrides to 15
/usr/sbin/openwrt_captive_monitor --monitor --interval 15

# Result: interval = 15 seconds
```

---

## 🎯 Configuration Examples

### Example 1: Development Testing

```bash
# Environment overrides for testing
export MONITOR_INTERVAL="10"
export WIFI_INTERFACE="wlan0"
export ENABLE_SYSLOG="0"

# Run with command-line override
/usr/sbin/openwrt_captive_monitor --monitor --interval 5
```

### Example 2: Production Deployment

```uci
config captive_monitor 'config'
    option enabled '1'
    option mode 'monitor'
    option wifi_interface 'phy1-sta0'
    option wifi_logical 'wwan'
    option monitor_interval '60'
    option ping_servers '1.1.1.1 8.8.8.8'
    option enable_syslog '1'
    option firewall_backend 'auto'
```

### Example 3: Resource-Constrained Device

```uci
config captive_monitor 'config'
    option enabled '1'
    option mode 'monitor'
    option monitor_interval '300'        # 5 minutes
    option ping_servers '8.8.8.8'        # Single server
    option http_probe_timeout '3'        # Faster timeout
    option internet_check_retries '1'    # Fewer retries
```

### Example 4: High-Availability Setup

```uci
config captive_monitor 'config'
    option enabled '1'
    option mode 'monitor'
    option monitor_interval '30'         # 30 seconds
    option ping_servers '1.1.1.1 8.8.8.8 9.9.9.9 208.67.222.222'
    option gateway_check_retries '3'
    option internet_check_retries '3'
    option enable_syslog '1'
```

---

## 🔍 Configuration Validation

### Validate UCI Configuration

```bash
# Check syntax
uci -c /tmp validate captive-monitor

# Show current configuration
uci show captive-monitor

# Check specific option
uci get captive-monitor.config.enabled
```

### Test Configuration

```bash
# Test with oneshot mode
/usr/sbin/openwrt_captive_monitor --oneshot

# Test with custom settings
/usr/sbin/openwrt_captive_monitor --oneshot \
    --interface wlan0 \
    --logical wan \
    --interval 30

# Check logs for configuration application
logread | grep captive-monitor
```

### Environment Variable Testing

```bash
# Set test environment
export MONITOR_INTERVAL="10"
export WIFI_INTERFACE="wlan0"
export PING_SERVERS="8.8.8.8"

# Test with environment overrides
/usr/sbin/openwrt_captive_monitor --oneshot

# Clear environment
unset MONITOR_INTERVAL WIFI_INTERFACE PING_SERVERS
```

---

## 📝 Configuration File Template

```uci
# /etc/config/captive-monitor
# Complete configuration template

config captive_monitor 'config'
    # === Core Settings ===
    option enabled '0'                    # Service enabled?
    option mode 'monitor'                 # monitor | oneshot
    option wifi_interface 'phy1-sta0'     # Physical WiFi interface
    option wifi_logical 'wwan'            # Logical interface name
    option monitor_interval '60'          # Check interval (seconds)
    
    # === Network Settings ===
    option lan_interface ''               # LAN interface (auto if empty)
    option lan_ip ''                      # LAN IPv4 (auto if empty)
    option lan_ipv6 ''                    # LAN IPv6 (auto if empty)
    option firewall_backend 'auto'        # auto | iptables | nftables
    
    # === Connectivity Checks ===
    option ping_servers '1.1.1.1 8.8.8.8 9.9.9.9'
    option captive_check_urls 'http://connectivitycheck.gstatic.com/generate_204 http://detectportal.firefox.com/success.txt'
    
    # === Timing Settings ===
    option ping_timeout '2'               # Ping timeout (seconds)
    option http_probe_timeout '5'         # HTTP probe timeout
    option gateway_check_retries '2'      # Gateway check retries
    option internet_check_retries '2'     # Internet check retries
    option internet_check_delay '3'       # Delay between retries
    
    # === Logging ===
    option enable_syslog '1'              # Enable syslog logging
```

---

## 🆘 Troubleshooting Configuration

### Common Issues

1. **Configuration not applied**
   ```bash
   # Force reload
   uci commit captive-monitor
   /etc/init.d/captive-monitor restart
   ```

2. **Environment variables ignored**
   ```bash
   # Check if variables are set
   env | grep CAPTIVE
   # Ensure service is restarted after setting variables
   ```

3. **Command-line flags not working**
   ```bash
   # Check syntax
   /usr/sbin/openwrt_captive_monitor --help
   # Verify flag names and values
   ```

### Debug Mode

```bash
# Run with debug output
sh -x /usr/sbin/openwrt_captive_monitor --oneshot

# Check configuration application
logread -f | grep captive-monitor &
/usr/sbin/openwrt_captive_monitor --oneshot
```

For more troubleshooting tips, see the [Troubleshooting Guide](../guides/troubleshooting.md).