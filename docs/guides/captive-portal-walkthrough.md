# Captive Portal Walkthrough

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---


A complete end-to-end example of how **openwrt-captive-monitor** detects and handles captive portal scenarios.

## 🎯 Scenario Overview

In this walkthrough, we'll simulate a typical captive portal situation:

1. **Router connects** to a WiFi network with internet access
2. **Captive portal appears** (e.g., hotel, airport, coffee shop)
3. **Monitor detects** the portal and activates interception
4. **Client devices** are redirected to the portal
5. **User authenticates** and internet access is restored
6. **Monitor cleans up** automatically

---

## 🏗️ Test Environment Setup

### Hardware Requirements

- OpenWrt router (physical or virtual)
- Client device (laptop, phone)
- Network with captive portal (or simulated)

### Software Configuration

```uci
## /etc/config/captive-monitor
config captive_monitor 'config'
    option enabled '1'
    option mode 'monitor'
    option wifi_interface 'phy1-sta0'
    option wifi_logical 'wwan'
    option monitor_interval '30'          # Check every 30 seconds
    option ping_servers '1.1.1.1 8.8.8.8'
    option captive_check_urls 'http://connectivitycheck.gstatic.com/generate_204 http://detectportal.firefox.com/success.txt'
    option enable_syslog '1'
```

### Start the Service

```bash
## Apply configuration and start service
uci commit captive-monitor
/etc/init.d/captive-monitor enable
/etc/init.d/captive-monitor start

## Verify it's running
logread | grep captive-monitor | tail -5
```

---

## 📋 Step 1: Normal Internet Connection

### Initial State

When the router first connects to a network with working internet:

```bash
## Check service logs
logread | grep captive-monitor

## Expected output:
## captive-monitor: Starting connectivity check
## captive-monitor: Internet connectivity OK
## captive-monitor: No captive portal detected
## captive-monitor: Monitoring continues in 30 seconds
```

### Network State

```bash
## Check routing
ip route show default

## Check DNS resolution
nslookup google.com

## Check internet connectivity
ping -c 2 8.8.8.8
curl -I http://connectivitycheck.gstatic.com/generate_204
```

### Firewall State

```bash
## No captive portal rules should be active
iptables -t nat -L CAPTIVE_HTTP_REDIRECT -n -v 2>/dev/null
## Output: Chain CAPTIVE_HTTP_REDIRECT (0 references)

## Check DNS overrides
cat /tmp/dnsmasq.d/captive_intercept.conf 2>/dev/null
## Output: cat: can't open '/tmp/dnsmasq.d/captive_intercept.conf': No such file or directory
```

---

## 🚪 Step 2: Captive Portal Detection

### Simulating Captive Portal

When the router connects to a network with a captive portal:

```bash
## Monitor detects connectivity issues
logread -f | grep captive-monitor

## Expected log sequence:
## captive-monitor: Starting connectivity check
## captive-monitor: Gateway reachable, but internet connectivity failed
## captive-monitor: Testing captive portal detection URLs
## captive-monitor: Captive portal detected: http://portal.example.com/login
## captive-monitor: Activating captive portal interception mode
```

### Detection Process

The service performs these checks:

1. **Gateway Reachability**: Can we reach the network gateway?
2. **Internet Connectivity**: Can we ping external servers?
3. **HTTP Probes**: Do captive detection URLs return redirects?
4. **Portal URL Extraction**: Extract the actual portal URL

### Captive Portal Indicators

```bash
## HTTP probe results (example)
curl -I http://connectivitycheck.gstatic.com/generate_204
## Expected: HTTP/1.1 302 Found
##          Location: http://portal.example.com/login

curl -I http://detectportal.firefox.com/success.txt
## Expected: HTTP/1.1 302 Found  
##          Location: http://portal.example.com/auth
```

---

## 🔄 Step 3: Interception Mode Activation

### DNS Hijacking

```bash
## Check DNS configuration
cat /tmp/dnsmasq.d/captive_intercept.conf

## Expected content:
## address=/#/192.168.1.1
## local-ttl=0
## min-cache-ttl=0
## max-cache-ttl=0
## no-negcache

## Test DNS resolution
nslookup google.com
## Expected: 192.168.1.1 (router's IP)
nslookup portal.example.com
## Expected: real portal IP (if not overridden)
```

### HTTP Redirection

```bash
## Check firewall rules
iptables -t nat -L CAPTIVE_HTTP_REDIRECT -n -v

## Expected rules:
## Chain CAPTIVE_HTTP_REDIRECT (1 references)
## pkts bytes target     prot opt in     out     source               destination
##    0     0 DNAT       tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:80 to:192.168.1.1:8080

## Check PREROUTING chain
iptables -t nat -L PREROUTING -n -v | grep CAPTIVE
## Expected: DNAT rule in PREROUTING chain
```

### HTTP Server

```bash
## Check if HTTP server is running
ps aux | grep httpd

## Check HTTP server content
curl http://192.168.1.1:8080/
## Expected: HTML page with redirect to portal

## Check HTTP server logs
logread | grep httpd
```

---

## 📱 Step 4: Client Experience

### Connecting a Client Device

When a client device connects to the router's LAN:

```bash
## From client device
ping 8.8.8.8
## Expected: No response (DNS resolves to router)

nslookup google.com
## Expected: 192.168.1.1 (router's IP)

## Open browser and navigate to any website
## Expected: Redirect to captive portal login page
```

### Client Traffic Flow

1. **Client tries to access** `http://google.com`
2. **DNS query** resolves `google.com` → `192.168.1.1` (router)
3. **HTTP request** goes to router port 80
4. **NAT rule** redirects to router port 8080
5. **HTTP server** serves redirect page to portal
6. **Browser redirects** to captive portal URL

### Verification

```bash
## Monitor client traffic on router
tcpdump -i br-lan port 80 -n

## Check DNS queries
tcpdump -i br-lan port 53 -n

## Check NAT rule usage
iptables -t nat -L CAPTIVE_HTTP_REDIRECT -n -v --zero
## Wait for some traffic, then check again
iptables -t nat -L CAPTIVE_HTTP_REDIRECT -n -v
```

---

## 🔐 Step 5: User Authentication

### Portal Login Process

1. **User opens browser** → redirected to portal
2. **User enters credentials** → submits form
3. **Portal authenticates** → grants internet access
4. **Network state changes** → internet becomes available

### Monitoring Authentication

```bash
## Watch logs during authentication
logread -f | grep captive-monitor

## Expected sequence:
## captive-monitor: Checking internet connectivity...
## captive-monitor: Internet connectivity restored
## captive-monitor: Deactivating captive portal interception
## captive-monitor: Cleaning up DNS overrides
## captive-monitor: Cleaning up firewall rules
## captive-monitor: Captive portal session completed
```

### Post-Authentication State

```bash
## Check DNS overrides (should be removed)
cat /tmp/dnsmasq.d/captive_intercept.conf 2>/dev/null
## Expected: No such file or directory

## Check firewall rules (should be removed)
iptables -t nat -L CAPTIVE_HTTP_REDIRECT -n -v 2>/dev/null
## Expected: Chain CAPTIVE_HTTP_REDIRECT (0 references)

## Test internet connectivity
ping -c 2 8.8.8.8
## Expected: Successful ping

nslookup google.com
## Expected: Real Google IP addresses
```

---

## 🧹 Step 6: Automatic Cleanup

### Cleanup Process

The service automatically performs cleanup when internet is restored:

```bash
## Cleanup sequence in logs
captive-monitor: Starting cleanup process
captive-monitor: Stopping HTTP server (PID: 1234)
captive-monitor: Removing DNS intercept configuration
captive-monitor: Removing firewall redirect rules
captive-monitor: Restarting dnsmasq service
captive-monitor: Cleanup completed successfully
```

### Manual Cleanup (if needed)

```bash
## Force cleanup
/usr/sbin/openwrt_captive_monitor --force-cleanup

## Or restart service
/etc/init.d/captive-monitor restart
```

### Verification

```bash
## Comprehensive state check
/usr/local/bin/captive-inspect.sh

## Expected state:
## - No captive portal rules active
## - No DNS overrides
## - No HTTP server running
## - Normal internet connectivity
```

---

## 🔍 Advanced Scenarios

### Multiple Portal Detection

Some networks have multiple captive portal URLs:

```bash
## Configure multiple detection URLs
uci set captive-monitor.config.captive_check_urls='http://connectivitycheck.gstatic.com/generate_204 http://detectportal.firefox.com/success.txt http://captive.apple.com/hotspot-detect.html'

## Monitor detection process
logread | grep captive-monitor

## Expected output:
## captive-monitor: Testing captive portal detection URLs
## captive-monitor: URL 1: Redirect detected - http://portal1.example.com/login
## captive-monitor: URL 2: Redirect detected - http://portal2.example.com/auth  
## captive-monitor: Selected portal URL: http://portal1.example.com/login
```

### IPv6 Captive Portals

For networks with IPv6 captive portals:

```bash
## Enable IPv6 support
uci set captive-monitor.config.lan_ipv6='fd00::1'
uci set captive-monitor.config.enable_ipv6='1'

## Monitor IPv6 traffic
tcpdump -i br-lan ip6 -n

## Check IPv6 firewall rules
ip6tables -t nat -L CAPTIVE_HTTP_REDIRECT -n -v 2>/dev/null
```

### Custom Portal Handling

For custom captive portal workflows:

```bash
## Create custom redirect page
mkdir -p /tmp/captive_httpd
cat > /tmp/captive_httpd/index.html <<'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Network Authentication Required</title>
    <meta http-equiv="refresh" content="3; url=$PORTAL_URL">
</head>
<body>
    <h1>Network Authentication Required</h1>
    <p>You will be redirected to the login page in 3 seconds...</p>
    <p>If not redirected, <a href="$PORTAL_URL">click here</a>.</p>
</body>
</html>
EOF

## Restart service to apply changes
/etc/init.d/captive-monitor restart
```

---

## 📊 Performance Analysis

### Resource Usage During Captive Mode

```bash
## Monitor resource usage
top -b -n 1 | grep -E "(CPU|Mem|openwrt_captive_monitor|httpd)"

## Check memory usage
cat /proc/$(pgrep openwrt_captive_monitor)/status | grep -E 'VmSize|VmRSS'

## Monitor network traffic
iftop -i br-lan -t -s 10
```

### Timing Analysis

```bash
## Measure detection time
time /usr/sbin/openwrt_captive_monitor --oneshot

## Expected timing breakdown:
## - Gateway check: 1-2 seconds
## - Internet check: 2-5 seconds  
## - Captive detection: 3-8 seconds
## - Intercept setup: 1-3 seconds
```

---

## 🛠️ Troubleshooting Common Issues

### Issue 1: Portal Not Detected

```bash
## Check detection URLs manually
curl -I http://connectivitycheck.gstatic.com/generate_204
curl -I http://detectportal.firefox.com/success.txt

## Add custom detection URLs
uci add_list captive-monitor.config.captive_check_urls='http://your-portal.com/detect'
uci commit captive-monitor
/etc/init.d/captive-monitor restart
```

### Issue 2: Redirection Not Working

```bash
## Check firewall rules
iptables -t nat -L PREROUTING -n -v
iptables -t nat -L CAPTIVE_HTTP_REDIRECT -n -v

## Check HTTP server
curl http://192.168.1.1:8080/

## Check DNS overrides
nslookup test.com
```

### Issue 3: Cleanup Not Working

```bash
## Force cleanup
/usr/sbin/openwrt_captive_monitor --force-cleanup

## Manual cleanup
iptables -t nat -F CAPTIVE_HTTP_REDIRECT
iptables -t nat -D PREROUTING -i br-lan -p tcp --dport 80 -j CAPTIVE_HTTP_REDIRECT
iptables -t nat -X CAPTIVE_HTTP_REDIRECT
rm -f /tmp/dnsmasq.d/captive_intercept.conf
/etc/init.d/dnsmasq restart
```

---

## 📝 Best Practices

### Configuration Recommendations

1. **Monitor Interval**: Use 30-60 seconds for balanced responsiveness
2. **Detection URLs**: Include multiple URLs for reliability
3. **Ping Servers**: Use diverse, reliable DNS servers
4. **Logging**: Enable syslog for debugging and monitoring

### Operational Guidelines

1. **Test Regularly**: Verify captive portal detection works
2. **Monitor Logs**: Watch for detection issues or cleanup failures
3. **Update Detection URLs**: Keep portal detection URLs current
4. **Resource Monitoring**: Monitor memory and CPU usage

### Security Considerations

1. **Network Isolation**: Ensure captive mode doesn't expose internal services
2. **DNS Security**: Be aware of DNS hijacking implications
3. **Certificate Handling**: HTTPS traffic is not intercepted (by design)
4. **Privacy**: Consider privacy implications of traffic interception

---

## 🎉 Conclusion

This walkthrough demonstrates the complete captive portal detection and handling process. The **openwrt-captive-monitor** service provides:

- **Automatic Detection**: Identifies captive portals without user intervention
- **Seamless Interception**: Redirects clients to authentication portals
- **Automatic Cleanup**: Restores normal operation when authenticated
- **Robust Operation**: Handles edge cases and network changes gracefully

For more advanced configuration options, see the [Advanced Configuration Guide](../configuration/advanced-config.md).
