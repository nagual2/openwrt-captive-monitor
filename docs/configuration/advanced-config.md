# Advanced Configuration

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---


Advanced configuration options and techniques for power users and specific deployment scenarios.

## 🔧 Advanced UCI Options

### Custom Firewall Backend Selection

```uci
config captive_monitor 'config'
    option firewall_backend 'nftables'    # Force nftables backend
    # or
    option firewall_backend 'iptables'    # Force iptables backend
```

### IPv6-Specific Configuration

```uci
config captive_monitor 'config'
    option lan_ipv6 'fd00::1'             # Manual IPv6 assignment
    option enable_ipv6 '1'                # Enable IPv6 support
    option ipv6_dns_redirect '1'          # Redirect IPv6 DNS queries
```

### Custom HTTP Server Settings

```uci
config captive_monitor 'config'
    option http_port '8080'               # HTTP server port
    option http_root '/tmp/captive_httpd' # HTTP server root directory
    option redirect_delay '0'             # Redirect delay (seconds)
```

### Advanced Timing Configuration

```uci
config captive_monitor 'config'
    option ping_timeout '5'               # Ping timeout (seconds)
    option captive_curl_timeout '10'      # Captive portal detection timeout
    option dns_lookup_timeout '5'         # DNS resolution timeout
    option wifi_restart_delay '10'        # Delay before WiFi restart
    option cleanup_delay '5'             # Delay before cleanup
```

---

## 🌍 Environment Variable Overrides

### Advanced Network Configuration

```bash
## Force specific network configuration
export LAN_INTERFACE="br-lan"
export LAN_IP="192.168.1.1"
export LAN_IPV6="fd00::1"
export REQUESTED_FIREWALL_BACKEND="nftables"

## Custom timing
export MONITOR_INTERVAL="30"
export PING_TIMEOUT="3"
export HTTP_PROBE_TIMEOUT="8"
export GATEWAY_CHECK_RETRIES="3"
export INTERNET_CHECK_RETRIES="3"

## Disable specific checks
export INTERNET_HTTP_PROBES=""           # Disable HTTP probes
export PING_SERVERS=""                    # Disable ping checks
```

### Advanced Debugging Variables

```bash
## Enable debug output
export CAPTIVE_DEBUG="1"                 # Enable debug logging
export CAPTIVE_VERBOSE="1"               # Verbose output
export CAPTIVE_DRY_RUN="1"               # Dry run (no changes made)

## Custom paths
export CAPTIVE_STATE_DIR="/tmp/captive"  # State directory
export CAPTIVE_LOG_FILE="/tmp/captive.log" # Log file
```

---

## ⌨️ Advanced Command-Line Options

### Full Command Reference

```bash
## Basic advanced options
/usr/sbin/openwrt_captive_monitor \
    --monitor \
    --interface phy1-sta0 \
    --logical wwan \
    --interval 30 \
    --ping-servers "1.1.1.1 8.8.8.8" \
    --captive-urls "http://example.com"

## Advanced options
/usr/sbin/openwrt_captive_monitor \
    --monitor \
    --lan-interface br-lan \
    --lan-ip 192.168.1.1 \
    --firewall-backend nftables \
    --http-port 8080 \
    --syslog-only \
    --verbose

## Testing options
/usr/sbin/openwrt_captive_monitor \
    --oneshot \
    --dry-run \
    --debug \
    --verbose
```

### Specialized Flags

| Flag | Description |
|------|-------------|
| `--dry-run` | Show what would be done without making changes |
| `--debug` | Enable debug output |
| `--verbose` | Verbose logging |
| `--syslog-only` | Only log to syslog (no stdout) |
| `--force-cleanup` | Force cleanup of existing rules |
| `--no-wifi-restart` | Skip WiFi restart |
| `--custom-redirect-url` | Custom captive portal redirect URL |

---

## 🎯 Specialized Configuration Scenarios

### Scenario 1: Enterprise Network with Multiple VLANs

```uci
config captive_monitor 'config'
    option enabled '1'
    option mode 'monitor'
    option wifi_interface 'phy1-sta0'
    option wifi_logical 'wan'
    option lan_interface 'br-lan.10'       # VLAN 10
    option lan_ip '192.168.10.1'
    option monitor_interval '30'
    option ping_servers '1.1.1.1 8.8.8.8 208.67.222.222'
    option firewall_backend 'iptables'
    option enable_syslog '1'
```

### Scenario 2: Travel Router with Multiple Networks

```uci
config captive_monitor 'config'
    option enabled '1'
    option mode 'monitor'
    option monitor_interval '45'
    option ping_servers '1.1.1.1 8.8.8.8 9.9.9.9 208.67.222.222'
    option captive_check_urls 'http://connectivitycheck.gstatic.com/generate_204 http://detectportal.firefox.com/success.txt http://captive.apple.com/hotspot-detect.html'
    option gateway_check_retries '3'
    option internet_check_retries '3'
    option http_probe_timeout '8'
    option enable_syslog '1'
```

### Scenario 3: Resource-Constrained IoT Device

```uci
config captive_monitor 'config'
    option enabled '1'
    option mode 'monitor'
    option monitor_interval '300'          # 5 minutes
    option ping_servers '8.8.8.8'           # Single server
    option gateway_check_retries '1'
    option internet_check_retries '1'
    option ping_timeout '2'
    option http_probe_timeout '3'
    option enable_syslog '0'               # Disable logging to save resources
```

### Scenario 4: High-Availability Setup

```uci
config captive_monitor 'config'
    option enabled '1'
    option mode 'monitor'
    option monitor_interval '15'           # 15 seconds
    option ping_servers '1.1.1.1 8.8.8.8 9.9.9.9 208.67.222.222 1.0.0.1'
    option captive_check_urls 'http://connectivitycheck.gstatic.com/generate_204 http://detectportal.firefox.com/success.txt http://captive.apple.com/hotspot-detect.html'
    option gateway_check_retries '5'
    option internet_check_retries '5'
    option internet_check_delay '2'
    option ping_timeout '3'
    option http_probe_timeout '7'
    option enable_syslog '1'
```

---

## 🔧 Custom Scripts and Hooks

### Pre/Post Hooks

```bash
## Create custom hooks directory
mkdir -p /etc/captive-monitor/hooks

## Pre-check hook (runs before connectivity check)
cat > /etc/captive-monitor/hooks/pre-check.sh <<'EOF'
#!/bin/sh
## Custom pre-check logic
logger "Captive monitor: Starting pre-check hook"
## Add your custom logic here
EOF

## Post-captive hook (runs after captive portal detection)
cat > /etc/captive-monitor/hooks/post-captive.sh <<'EOF'
#!/bin/sh
## Custom post-captive logic
logger "Captive monitor: Captive portal detected, running post-captive hook"
## Add your custom logic here
EOF

## Cleanup hook (runs during cleanup)
cat > /etc/captive-monitor/hooks/cleanup.sh <<'EOF'
#!/bin/sh
## Custom cleanup logic
logger "Captive monitor: Running cleanup hook"
## Add your custom cleanup logic here
EOF

## Make hooks executable
chmod +x /etc/captive-monitor/hooks/*.sh
```

### Integration with External Services

```bash
## Example: Send notification when captive portal is detected
cat > /etc/captive-monitor/hooks/notify-captive.sh <<'EOF'
#!/bin/sh
## Send notification to external service
PORTAL_URL="$1"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

## Example: Send to webhook
curl -X POST "https://hooks.slack.com/your-webhook-url" \
  -H 'Content-type: application/json' \
  --data "{\"text\":\"Captive portal detected at $TIMESTAMP: $PORTAL_URL\"}"

## Example: Send email (requires mailx)
echo "Captive portal detected: $PORTAL_URL" | mail -s "Captive Portal Alert" admin@example.com
EOF

chmod +x /etc/captive-monitor/hooks/notify-captive.sh
```

---

## 🔍 Advanced Monitoring and Debugging

### Enhanced Logging Configuration

```bash
## Configure detailed logging
export CAPTIVE_LOG_LEVEL="debug"          # debug, info, warn, error
export CAPTIVE_LOG_FORMAT="detailed"     # simple, detailed, json
export CAPTIVE_LOG_TO_FILE="1"
export CAPTIVE_LOG_FILE="/var/log/captive-monitor.log"

## Rotate logs
cat > /etc/logrotate.d/captive-monitor <<'EOF'
/var/log/captive-monitor.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
EOF
```

### Performance Monitoring

```bash
## Create monitoring script
cat > /usr/local/bin/captive-monitor-stats.sh <<'EOF'
#!/bin/sh
## Monitor captive monitor performance

echo "=== Captive Monitor Statistics ==="
echo "Process status:"
ps aux | grep openwrt_captive_monitor | grep -v grep

echo -e "\nMemory usage:"
cat /proc/$(pgrep openwrt_captive_monitor)/status | grep -E 'VmSize|VmRSS'

echo -e "\nRecent logs:"
logread | grep captive-monitor | tail -20

echo -e "\nFirewall rules:"
iptables -t nat -L CAPTIVE_HTTP_REDIRECT -n -v 2>/dev/null || echo "No captive rules active"

echo -e "\nDNS overrides:"
cat /tmp/dnsmasq.d/captive_intercept.conf 2>/dev/null || echo "No DNS overrides active"
EOF

chmod +x /usr/local/bin/captive-monitor-stats.sh
```

### Health Check Script

```bash
## Create comprehensive health check
cat > /usr/local/bin/captive-monitor-health.sh <<'EOF'
#!/bin/sh
## Health check for captive monitor

EXIT_CODE=0

## Check if service is running
if ! pgrep -f openwrt_captive_monitor > /dev/null; then
    echo "ERROR: Captive monitor process not running"
    EXIT_CODE=1
else
    echo "OK: Captive monitor process is running"
fi

## Check configuration
if ! uci -q get captive-monitor.config.enabled > /dev/null; then
    echo "ERROR: UCI configuration not found"
    EXIT_CODE=1
else
    echo "OK: UCI configuration found"
fi

## Check required binaries
for binary in curl iptables dnsmasq; do
    if ! command -v $binary > /dev/null; then
        echo "ERROR: Required binary $binary not found"
        EXIT_CODE=1
    else
        echo "OK: $binary is available"
    fi
done

## Check network interfaces
if ! ip link show $(uci -q get captive-monitor.config.wifi_interface) > /dev/null 2>&1; then
    echo "WARNING: WiFi interface not found"
else
    echo "OK: WiFi interface found"
fi

exit $EXIT_CODE
EOF

chmod +x /usr/local/bin/captive-monitor-health.sh
```

---

## 🛡️ Security Considerations

### Secure Configuration

```uci
config captive_monitor 'config'
    option enable_syslog '1'              # Keep logs for audit
    option monitor_interval '60'          # Reasonable check interval
    option firewall_backend 'nftables'     # More secure backend
    # Avoid exposing sensitive information in logs
```

### Network Isolation

```bash
## Create isolated network namespace for captive monitor
cat > /etc/captive-monitor/isolation.sh <<'EOF'
#!/bin/sh
## Network isolation for captive monitor

## Create network namespace
ip netns add captive-monitor

## Move captive monitor to namespace
ip netns exec captive-monitor /usr/sbin/openwrt_captive_monitor "$@"

## Cleanup namespace on exit
ip netns delete captive-monitor
EOF

chmod +x /etc/captive-monitor/isolation.sh
```

---

## 📊 Performance Tuning

### Memory Optimization

```bash
## Reduce memory usage for resource-constrained devices
export MONITOR_INTERVAL="300"            # Less frequent checks
export ENABLE_SYSLOG="0"                  # Disable logging
export CAPTIVE_VERBOSE="0"                # Disable verbose output
export PING_SERVERS="8.8.8.8"             # Single ping server
export GATEWAY_CHECK_RETRIES="1"          # Fewer retries
export INTERNET_CHECK_RETRIES="1"
```

### CPU Optimization

```bash
## Optimize for CPU performance
export PING_TIMEOUT="1"                   # Faster ping timeout
export HTTP_PROBE_TIMEOUT="3"             # Faster HTTP timeout
export INTERNET_CHECK_DELAY="1"           # Shorter delays
export CAPTIVE_CURL_TIMEOUT="5"           # Faster cURL timeout
```

---

## 🔧 Customization Examples

### Custom Captive Portal Page

```bash
## Create custom HTML page
mkdir -p /tmp/captive_httpd
cat > /tmp/captive_httpd/index.html <<'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Captive Portal Redirect</title>
    <meta http-equiv="refresh" content="0; url=$PORTAL_URL">
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        .redirect { color: #666; font-size: 14px; }
    </style>
</head>
<body>
    <h1>Redirecting to Captive Portal...</h1>
    <p class="redirect">You will be redirected automatically. If not, <a href="$PORTAL_URL">click here</a>.</p>
</body>
</html>
EOF
```

### Integration with Network Manager

```bash
## Create network manager integration
cat > /etc/captive-monitor/network-manager.sh <<'EOF'
#!/bin/sh
## Integration with network manager

case "$1" in
    "up")
        # Network interface up
        logger "Network up: $2"
        /usr/sbin/openwrt_captive_monitor --oneshot
        ;;
    "down")
        # Network interface down
        logger "Network down: $2"
        # Cleanup any active captive rules
        /usr/sbin/openwrt_captive_monitor --force-cleanup
        ;;
    *)
        echo "Usage: $0 {up|down} interface"
        exit 1
        ;;
esac
EOF

chmod +x /etc/captive-monitor/network-manager.sh
```

---

## 🆘 Advanced Troubleshooting

### Deep Debug Mode

```bash
## Enable comprehensive debugging
export CAPTIVE_DEBUG="1"
export CAPTIVE_VERBOSE="1"
export CAPTIVE_DRY_RUN="1"

## Run with full debugging
sh -x /usr/sbin/openwrt_captive_monitor --oneshot --debug --verbose 2>&1 | tee /tmp/captive-debug.log
```

### State Inspection

```bash
## Inspect current state
cat > /usr/local/bin/captive-inspect.sh <<'EOF'
#!/bin/sh
echo "=== Captive Monitor State Inspection ==="

echo "Process status:"
ps aux | grep openwrt_captive_monitor

echo -e "\nNetwork interfaces:"
ip addr show | grep -E "^[0-9]+:"

echo -e "\nRouting table:"
ip route show

echo -e "\nDNS configuration:"
cat /etc/resolv.conf

echo -e "\nFirewall rules:"
iptables -t nat -L -n -v 2>/dev/null || echo "iptables not available"
nft list ruleset 2>/dev/null || echo "nftables not available"

echo -e "\nDnsmasq configuration:"
cat /tmp/dnsmasq.d/captive_intercept.conf 2>/dev/null || echo "No dnsmasq overrides"

echo -e "\nUCI configuration:"
uci show captive-monitor
EOF

chmod +x /usr/local/bin/captive-inspect.sh
```

For basic troubleshooting, see the [Troubleshooting Guide](../guides/troubleshooting.md).
