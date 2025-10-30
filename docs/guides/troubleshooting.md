# Troubleshooting Guide

Comprehensive troubleshooting guide for **openwrt-captive-monitor** covering common issues, diagnostics, and solutions.

## 🔍 Quick Diagnosis

### Immediate Checks

```bash
# 1. Check if service is running
ps aux | grep openwrt_captive_monitor

# 2. Check service status
/etc/init.d/captive-monitor status

# 3. Check recent logs
logread | grep captive-monitor | tail -20

# 4. Check configuration
uci show captive-monitor
```

### Health Check Script

```bash
# Create comprehensive health check
cat > /usr/local/bin/captive-health-check.sh <<'EOF'
#!/bin/sh

echo "=== OpenWrt Captive Monitor Health Check ==="
echo ""

# Check service status
echo "1. Service Status:"
if pgrep -f openwrt_captive_monitor > /dev/null; then
    echo "   ✓ Process is running"
    PID=$(pgrep -f openwrt_captive_monitor)
    echo "   PID: $PID"
else
    echo "   ✗ Process is NOT running"
fi

# Check configuration
echo -e "\n2. Configuration:"
if uci -q get captive-monitor.config.enabled > /dev/null; then
    echo "   ✓ UCI configuration exists"
    ENABLED=$(uci get captive-monitor.config.enabled)
    MODE=$(uci get captive-monitor.config.mode)
    echo "   Enabled: $ENABLED, Mode: $MODE"
else
    echo "   ✗ UCI configuration not found"
fi

# Check required binaries
echo -e "\n3. Required Binaries:"
MISSING=""
for binary in curl iptables dnsmasq; do
    if command -v $binary > /dev/null; then
        echo "   ✓ $binary is available"
    else
        echo "   ✗ $binary is MISSING"
        MISSING="$MISSING $binary"
    fi
done

# Check network interfaces
echo -e "\n4. Network Interfaces:"
WIFI_IFACE=$(uci -q get captive-monitor.config.wifi_interface)
if [ -n "$WIFI_IFACE" ]; then
    if ip link show "$WIFI_IFACE" > /dev/null 2>&1; then
        echo "   ✓ WiFi interface $WIFI_IFACE exists"
        STATUS=$(ip link show "$WIFI_IFACE" | grep -o 'state [A-Z]*')
        echo "   Status: $STATUS"
    else
        echo "   ✗ WiFi interface $WIFI_IFACE NOT found"
    fi
fi

# Check firewall state
echo -e "\n5. Firewall State:"
if iptables -t nat -L CAPTIVE_HTTP_REDIRECT -n 2>/dev/null | grep -q "Chain CAPTIVE_HTTP_REDIRECT"; then
    echo "   ⚠ Captive portal rules are ACTIVE"
    RULES=$(iptables -t nat -L CAPTIVE_HTTP_REDIRECT -n | wc -l)
    echo "   Rules count: $RULES"
else
    echo "   ✓ No captive portal rules active"
fi

# Check DNS overrides
echo -e "\n6. DNS Overrides:"
if [ -f /tmp/dnsmasq.d/captive_intercept.conf ]; then
    echo "   ⚠ DNS intercept file EXISTS"
    echo "   Content:"
    cat /tmp/dnsmasq.d/captive_intercept.conf | sed 's/^/     /'
else
    echo "   ✓ No DNS intercept file found"
fi

# Recent errors
echo -e "\n7. Recent Errors:"
ERRORS=$(logread | grep captive-monitor | grep -i error | tail -5)
if [ -n "$ERRORS" ]; then
    echo "   ⚠ Recent errors found:"
    echo "$ERRORS" | sed 's/^/   /'
else
    echo "   ✓ No recent errors"
fi

echo -e "\n=== Health Check Complete ==="

if [ -n "$MISSING" ]; then
    echo "⚠ Missing dependencies:$MISSING"
    echo "Install with: opkg install$MISSING"
fi
EOF

chmod +x /usr/local/bin/captive-health-check.sh
```

---

## 🚫 Common Issues and Solutions

### Issue 1: Service Won't Start

#### Symptoms
- Process not running after enabling service
- No logs in syslog
- Service status shows "not running"

#### Diagnosis
```bash
# Check if service is enabled
uci get captive-monitor.config.enabled

# Check init script
ls -la /etc/init.d/captive-monitor

# Try manual start
/etc/init.d/captive-monitor start

# Check for errors
logread | grep captive-monitor
```

#### Solutions

**Solution 1: Enable service**
```bash
uci set captive-monitor.config.enabled='1'
uci commit captive-monitor
/etc/init.d/captive-monitor enable
/etc/init.d/captive-monitor start
```

**Solution 2: Fix permissions**
```bash
chmod +x /usr/sbin/openwrt_captive_monitor
chmod +x /etc/init.d/captive-monitor
```

**Solution 3: Check configuration**
```bash
# Validate configuration
uci -c /tmp validate captive-monitor

# Reset to defaults if corrupted
uci revert captive-monitor
# Then reconfigure as needed
```

### Issue 2: Captive Portal Not Detected

#### Symptoms
- Router connected to network with captive portal
- No redirection occurs for clients
- Logs show "Internet connectivity OK" (false positive)

#### Diagnosis
```bash
# Test captive detection URLs manually
curl -I http://connectivitycheck.gstatic.com/generate_204
curl -I http://detectportal.firefox.com/success.txt

# Check response codes
curl -s -w "%{http_code}" http://connectivitycheck.gstatic.com/generate_204 -o /dev/null
```

#### Solutions

**Solution 1: Add custom detection URLs**
```bash
uci add_list captive-monitor.config.captive_check_urls='http://your-portal.com/detect'
uci add_list captive-monitor.config.captive_check_urls='http://another-portal.com/check'
uci commit captive-monitor
/etc/init.d/captive-monitor restart
```

**Solution 2: Adjust timing**
```bash
uci set captive-monitor.config.http_probe_timeout='10'
uci set captive-monitor.config.internet_check_retries='3'
uci commit captive-monitor
/etc/init.d/captive-monitor restart
```

**Solution 3: Test manually**
```bash
/usr/sbin/openwrt_captive_monitor --oneshot --verbose
```

### Issue 3: DNS Redirection Not Working

#### Symptoms
- Clients can resolve domain names but don't get redirected
- DNS queries go to real servers instead of router

#### Diagnosis
```bash
# Check if DNS intercept file exists
cat /tmp/dnsmasq.d/captive_intercept.conf

# Check dnsmasq configuration
ps aux | grep dnsmasq

# Test DNS resolution from client
nslookup google.com  # Should return router IP
```

#### Solutions

**Solution 1: Restart dnsmasq**
```bash
/etc/init.d/dnsmasq restart
sleep 5
# Test again
nslookup google.com
```

**Solution 2: Check dnsmasq configuration**
```bash
# Ensure dnsmasq reads the drop-in directory
grep -E "^conf-dir|^conf-file" /etc/dnsmasq.conf

# If missing, add to configuration
echo "conf-dir=/tmp/dnsmasq.d" >> /etc/dnsmasq.conf
/etc/init.d/dnsmasq restart
```

**Solution 3: Manual DNS intercept**
```bash
# Create manual intercept file
mkdir -p /tmp/dnsmasq.d
cat > /tmp/dnsmasq.d/captive_intercept.conf <<'EOF'
address=/#/192.168.1.1
local-ttl=0
min-cache-ttl=0
max-cache-ttl=0
no-negcache
EOF

/etc/init.d/dnsmasq restart
```

### Issue 4: HTTP Redirection Not Working

#### Symptoms
- DNS redirection works but HTTP requests don't get redirected
- Clients get router IP but can't access redirect page

#### Diagnosis
```bash
# Check firewall rules
iptables -t nat -L CAPTIVE_HTTP_REDIRECT -n -v
iptables -t nat -L PREROUTING -n -v | grep CAPTIVE

# Check if HTTP server is running
ps aux | grep httpd
netstat -ln | grep :8080

# Test HTTP server locally
curl http://127.0.0.1:8080/
```

#### Solutions

**Solution 1: Check firewall backend**
```bash
# Determine if using iptables or nftables
which iptables >/dev/null && echo "iptables available" || echo "iptables not available"
which nft >/dev/null && echo "nft available" || echo "nft not available"

# Force specific backend
uci set captive-monitor.config.firewall_backend='iptables'
uci commit captive-monitor
/etc/init.d/captive-monitor restart
```

**Solution 2: Manual firewall rules**
```bash
# Create manual redirect rules
LAN_IF=br-lan
LAN_IP=192.168.1.1

iptables -t nat -N CAPTIVE_HTTP_REDIRECT 2>/dev/null
iptables -t nat -F CAPTIVE_HTTP_REDIRECT
iptables -t nat -A CAPTIVE_HTTP_REDIRECT -p tcp --dport 80 -j DNAT --to-destination $LAN_IP:8080
iptables -t nat -I PREROUTING 1 -i "$LAN_IF" -p tcp --dport 80 -j CAPTIVE_HTTP_REDIRECT
```

**Solution 3: Start HTTP server manually**
```bash
mkdir -p /tmp/captive_httpd
cat > /tmp/captive_httpd/index.html <<'EOF'
<meta http-equiv="refresh" content="0; url=http://portal.example.com">
EOF

busybox httpd -f -p 8080 -h /tmp/captive_httpd &
```

### Issue 5: Cleanup Not Working

#### Symptoms
- Captive portal rules remain after authentication
- DNS intercept file not removed
- HTTP server keeps running

#### Diagnosis
```bash
# Check for remaining rules
iptables -t nat -L CAPTIVE_HTTP_REDIRECT -n -v
iptables -t nat -L PREROUTING -n -v | grep CAPTIVE

# Check for remaining files
ls -la /tmp/dnsmasq.d/captive_intercept.conf
ps aux | grep httpd
```

#### Solutions

**Solution 1: Force cleanup**
```bash
/usr/sbin/openwrt_captive_monitor --force-cleanup
```

**Solution 2: Manual cleanup**
```bash
# Remove firewall rules
iptables -t nat -F CAPTIVE_HTTP_REDIRECT
iptables -t nat -D PREROUTING -i br-lan -p tcp --dport 80 -j CAPTIVE_HTTP_REDIRECT 2>/dev/null
iptables -t nat -X CAPTIVE_HTTP_REDIRECT 2>/dev/null

# Remove DNS intercept
rm -f /tmp/dnsmasq.d/captive_intercept.conf
/etc/init.d/dnsmasq restart

# Stop HTTP server
pkill -f "busybox httpd.*8080"
```

**Solution 3: Restart service**
```bash
/etc/init.d/captive-monitor stop
sleep 5
/etc/init.d/captive-monitor start
```

---

## 🔧 Advanced Troubleshooting

### Debug Mode

```bash
# Enable comprehensive debugging
export CAPTIVE_DEBUG="1"
export CAPTIVE_VERBOSE="1"

# Run with debug output
sh -x /usr/sbin/openwrt_captive_monitor --oneshot 2>&1 | tee /tmp/captive-debug.log

# Monitor logs in real-time
logread -f | grep captive-monitor &
/usr/sbin/openwrt_captive_monitor --monitor --verbose
```

### Network Analysis

```bash
# Capture network traffic
tcpdump -i br-lan port 53 -n -vvv    # DNS traffic
tcpdump -i br-lan port 80 -n -vvv    # HTTP traffic
tcpdump -i phy1-sta0 -n -vvv        # WAN traffic

# Check routing
ip route show
ip route get 8.8.8.8

# Check interface status
ip addr show
ip link show
```

### System State Inspection

```bash
# Check system resources
free -h
df -h
top -b -n 1 | head -20

# Check system logs
dmesg | grep -E "(error|fail|warn)" | tail -20
logread | grep -E "(error|fail|warn)" | tail -20
```

---

## 📊 Performance Issues

### High CPU Usage

#### Diagnosis
```bash
# Check CPU usage
top | grep openwrt_captive_monitor

# Monitor over time
while true; do
    echo "$(date): $(ps -o pid,pcpu,pmem,cmd -p $(pgrep openwrt_captive_monitor))"
    sleep 5
done
```

#### Solutions
- Increase monitoring interval
- Reduce number of ping servers
- Disable verbose logging
- Use oneshot mode instead of monitor mode

### High Memory Usage

#### Diagnosis
```bash
# Check memory usage
ps aux | grep openwrt_captive_monitor

# Monitor memory leaks
while true; do
    echo "$(date): $(cat /proc/$(pgrep openwrt_captive_monitor)/status | grep -E 'VmSize|VmRSS')"
    sleep 30
done
```

#### Solutions
- Restart service periodically
- Reduce monitoring frequency
- Check for memory leaks in dependencies

---

## 🌐 Network-Specific Issues

### WiFi Interface Problems

#### Diagnosis
```bash
# Check WiFi interface status
iwconfig
iw dev
ifstatus wwan

# Check wireless configuration
uci show wireless
```

#### Solutions
```bash
# Restart WiFi interface
wifi down
sleep 5
wifi up

# Restart specific interface
ifdown wwan
sleep 5
ifup wwan
```

### IPv6 Issues

#### Diagnosis
```bash
# Check IPv6 configuration
ip -6 addr show
ip -6 route show

# Test IPv6 connectivity
ping6 -c 2 2001:4860:4860::8888
```

#### Solutions
```bash
# Enable IPv6 support
uci set captive-monitor.config.enable_ipv6='1'
uci set captive-monitor.config.lan_ipv6='fd00::1'
uci commit captive-monitor
/etc/init.d/captive-monitor restart
```

---

## 📋 Troubleshooting Checklist

### Initial Diagnosis Checklist

- [ ] Service is running (`ps aux | grep openwrt_captive_monitor`)
- [ ] Service is enabled (`uci get captive-monitor.config.enabled`)
- [ ] Configuration is valid (`uci show captive-monitor`)
- [ ] Required binaries available (`curl`, `iptables`, `dnsmasq`)
- [ ] Network interfaces exist and are up
- [ ] No syntax errors in configuration
- [ ] Recent logs show no critical errors

### Captive Portal Issues Checklist

- [ ] Can manually access captive portal URLs
- [ ] Detection URLs return appropriate responses
- [ ] Firewall rules are created when needed
- [ ] DNS intercept file is created
- [ ] HTTP server starts on correct port
- [ ] Client traffic is properly redirected

### Cleanup Issues Checklist

- [ ] Firewall rules are removed after authentication
- [ ] DNS intercept file is deleted
- [ ] HTTP server is stopped
- [ ] dnsmasq is reloaded
- [ ] No residual processes remain

---

## 🆘 Getting Help

### Collect Debug Information

```bash
# Create debug report
cat > /tmp/captive-debug-report.txt <<'EOF'
=== OpenWrt Captive Monitor Debug Report ===
Generated: $(date)

System Information:
-----------------
$(uname -a)
$(cat /etc/openwrt_release)

Service Status:
---------------
$(ps aux | grep openwrt_captive_monitor)
$(/etc/init.d/captive-monitor status)

Configuration:
-------------
$(uci show captive-monitor)

Recent Logs:
------------
$(logread | grep captive-monitor | tail -50)

Network State:
--------------
$(ip addr show)
$(ip route show)

Firewall State:
---------------
$(iptables -t nat -L -n -v)

DNS Configuration:
-----------------
$(cat /etc/resolv.conf)
$(ls -la /tmp/dnsmasq.d/ 2>/dev/null || echo "No dnsmasq.d directory")

=== End of Report ===
EOF

echo "Debug report saved to /tmp/captive-debug-report.txt"
```

### Support Channels

1. **GitHub Issues**: [Create an issue](https://github.com/nagual2/openwrt-captive-monitor/issues)
2. **GitHub Discussions**: [Start a discussion](https://github.com/nagual2/openwrt-captive-monitor/discussions)
3. **Documentation**: [Check this guide and other docs](https://github.com/nagual2/openwrt-captive-monitor/tree/main/docs)

### When Reporting Issues

Include the following information:

1. **OpenWrt version** and target device
2. **Package version** of openwrt-captive-monitor
3. **Configuration** (sanitized if necessary)
4. **Debug report** from above
5. **Expected behavior** vs. **actual behavior**
6. **Steps to reproduce** the issue

---

## 📚 Additional Resources

- [Configuration Reference](../configuration/reference.md) - Complete configuration options
- [Advanced Configuration](../configuration/advanced-config.md) - Advanced settings and customization
- [Captive Portal Walkthrough](captive-portal-walkthrough.md) - End-to-end example
- [Project FAQ](../project/faq.md) - Frequently asked questions

For ongoing issues or feature requests, please use the project's GitHub issue tracker.