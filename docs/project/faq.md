# Frequently Asked Questions

Common questions and answers about **openwrt-captive-monitor**.

## 🚀 General Questions

### Q: What is openwrt-captive-monitor?

**A:** openwrt-captive-monitor is a lightweight OpenWrt service that monitors WAN connectivity, detects captive
portals, and temporarily intercepts LAN DNS/HTTP traffic to help clients authenticate with the portal. Once internet
access is restored, it automatically cleans up all modifications.

### Q: Why do I need this service?

**A:** When you connect to networks that require authentication (hotels, airports, coffee shops), your devices often
can't access the internet until you authenticate through a captive portal. This service automatically detects such
portals and redirects all client devices to the authentication page, making the process seamless for all users on your
network.

### Q: Does this work with all captive portals?

**A:** The service works with most standard HTTP-based captive portals. It detects portals by analyzing HTTP responses
from known detection URLs and redirects clients to the discovered portal URL. Some specialized or HTTPS-only portals
may require manual intervention.

### Q: Is this safe to use? Does it compromise my security?

**A:** Yes, it's safe. The service only intercepts HTTP traffic and DNS queries temporarily. HTTPS traffic is never
intercepted (by design) to preserve security and HSTS compliance. All modifications are automatically reversed once
internet access is restored.

---

## ⚙️ Configuration Questions

### Q: How do I enable the service?

**A:** After installation, enable it with:
```bash
uci set captive-monitor.config.enabled='1'
uci commit captive-monitor
/etc/init.d/captive-monitor enable
/etc/init.d/captive-monitor start
```

### Q: What's the difference between "monitor" and "oneshot" modes?

**A:** 
  - **Monitor mode**: Runs continuously, checking connectivity at specified intervals (default: 60 seconds)
  - **Oneshot mode**: Performs a single check and exits, useful for cron jobs or manual execution

### Q: How often should I set the monitoring interval?

**A:** 
  - **30 seconds**: High-availability environments, frequent checks
  - **60 seconds**: Standard home/office use (recommended default)
  - **300 seconds**: Resource-constrained devices, less frequent checks
  - **900 seconds**: Minimal monitoring, very slow detection

### Q: Can I use this with multiple WiFi interfaces?

**A:** Currently, the service monitors one primary WiFi interface specified in the configuration. For multiple
interfaces, you can run multiple instances with different configurations, though this is an advanced use case.

### Q: How do I change the ping servers?

**A:** Modify the configuration:
```bash
uci set captive-monitor.config.ping_servers='1.1.1.1 8.8.8.8 208.67.222.222'
uci commit captive-monitor
/etc/init.d/captive-monitor restart
```

---

## 🔧 Technical Questions

### Q: What are the system requirements?

**A:** 
- OpenWrt 21.02 or later (22.03+ recommended)
- Root access on the router
- Required packages: `dnsmasq`, `curl`, `iptables` or `nftables`
- Minimum RAM: 64MB (recommended: 128MB+)

### Q: Does this work with IPv6?

**A:** Yes, the service supports IPv6 networks. It can intercept IPv6 DNS queries and handle dual-stack configurations.
IPv6 support can be enabled in the configuration.

### Q: Which firewall backend does it use?

**A:** The service automatically detects and uses the appropriate firewall backend:
  - **iptables**: For OpenWrt 21.02 and legacy systems
  - **nftables**: For OpenWrt 22.03+ with fw4
  - **Auto-detection**: Default, picks the available backend

### Q: Will this interfere with my existing firewall rules?

**A:** No, the service creates isolated firewall chains and rules that don't conflict with existing configurations. All
rules are properly labeled and cleaned up when no longer needed.

### Q: Can I use custom captive portal detection URLs?

**A:** Yes, you can add custom URLs:
```bash
uci add_list captive-monitor.config.captive_check_urls='http://your-portal.com/detect'
uci commit captive-monitor
/etc/init.d/captive-monitor restart
```

---

## 🌐 Network Questions

### Q: What happens to HTTPS traffic during captive mode?

**A:** HTTPS traffic is NOT intercepted and passes through normally. This is by design to preserve security and avoid
HSTS violations. Users may need to manually navigate to HTTP sites to trigger the captive portal detection.

### Q: How does DNS hijacking work? Is it safe?

**A:** During captive mode, the service temporarily overrides DNS resolution to point all domains to the router's IP
address, except for the captive portal domain. This is safe because:
- It's temporary and automatically reversed
- Only affects DNS queries, not actual traffic content
- Preserves the real portal domain resolution

### Q: Will this affect devices that are already authenticated?

**A:** No, once devices are authenticated and internet access is restored, the service detects this and automatically
disables interception, restoring normal network operation for all devices.

### Q: Can I exclude certain domains from DNS hijacking?

**A:** Yes, the service automatically preserves the captive portal domain. You can manually configure additional
exclusions if needed by modifying the DNS intercept configuration.

---

## 🔍 Troubleshooting Questions

### Q: The service isn't detecting captive portals. What should I check?

**A:** Check the following:
```bash
## Test detection URLs manually
curl -I http://connectivitycheck.gstatic.com/generate_204

## Check service logs
logread | grep captive-monitor

## Run in verbose mode
/usr/sbin/openwrt_captive_monitor --oneshot --verbose
```

### Q: DNS redirection isn't working for clients. Why?

**A:** Common causes:
- dnsmasq not reading the drop-in configuration
- Client devices using hardcoded DNS servers
- DNS cache on client devices

Solutions:
```bash
## Restart dnsmasq
/etc/init.d/dnsmasq restart

## Check dnsmasq configuration
cat /tmp/dnsmasq.d/captive_intercept.conf
```

### Q: HTTP redirection isn't working. What's wrong?

**A:** Check firewall rules and HTTP server:
```bash
## Check firewall rules
iptables -t nat -L CAPTIVE_HTTP_REDIRECT -n -v

## Check HTTP server
netstat -ln | grep :8080
curl http://127.0.0.1:8080/
```

### Q: The service leaves rules behind after cleanup. How to fix?

**A:** Force cleanup:
```bash
/usr/sbin/openwrt_captive_monitor --force-cleanup

## Or manually clean up
iptables -t nat -F CAPTIVE_HTTP_REDIRECT
iptables -t nat -D PREROUTING -i br-lan -p tcp --dport 80 -j CAPTIVE_HTTP_REDIRECT
rm -f /tmp/dnsmasq.d/captive_intercept.conf
/etc/init.d/dnsmasq restart
```

### Q: The service uses too much CPU/memory. What can I do?

**A:** Optimize configuration:
```bash
## Increase monitoring interval
uci set captive-monitor.config.monitor_interval='300'

## Reduce ping servers
uci set captive-monitor.config.ping_servers='8.8.8.8'

## Disable verbose logging
uci set captive-monitor.config.enable_syslog='0'
```

---

## 📦 Installation Questions

### Q: How do I install the service?

**A:** Choose one of these methods:

**Prebuilt package (recommended):**
```bash
wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_*.ipk
opkg install openwrt-captive-monitor_*.ipk
```

**From source:**
```bash
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor
scripts/build_ipk.sh --arch all
opkg install dist/opkg/all/openwrt-captive-monitor_*.ipk
```

### Q: Which package architecture should I use?

**A:** Use `all` architecture for most cases since this is a shell script package. Architecture-specific packages are
available if you prefer them.

### Q: How do I uninstall the service?

**A:** 
```bash
opkg remove openwrt-captive-monitor
## Optionally clean up configuration
uci delete captive-monitor
uci commit captive-monitor
```

### Q: Can I install this alongside other network services?

**A:** Yes, the service is designed to coexist with other network services. However, avoid running multiple services
that modify firewall rules or DNS configuration simultaneously.

---

## 🔄 Usage Questions

### Q: How do I test if the service is working?

**A:** 
```bash
## Run health check
/usr/local/bin/captive-health-check.sh

## Test with oneshot mode
/usr/sbin/openwrt_captive_monitor --oneshot --verbose

## Monitor logs
logread -f | grep captive-monitor
```

### Q: Can I run this periodically instead of continuously?

**A:** Yes, use oneshot mode with cron:
```bash
## Edit crontab
crontab -e

## Add line for every 15 minutes
*/15 * * * * /usr/sbin/openwrt_captive_monitor --oneshot
```

### Q: How do I integrate this with my custom scripts?

**A:** The service returns specific exit codes:
- `0`: Success/internet working
- `1`: Configuration error
- `2`: Network error
- `3`: Captive portal detected
- `4`: Timeout

Example:
```bash
#!/bin/sh
/usr/sbin/openwrt_captive_monitor --oneshot
case $? in
    0) echo "Internet is working" ;;
    3) echo "Captive portal detected" ;;
    *) echo "Network issue detected" ;;
esac
```

### Q: Can I customize the redirect page?

**A:** Yes, create a custom HTML page:
```bash
mkdir -p /tmp/captive_httpd
cat > /tmp/captive_httpd/index.html <<'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Network Authentication Required</title>
    <meta http-equiv="refresh" content="0; url=$PORTAL_URL">
</head>
<body>
    <h1>Redirecting to authentication page...</h1>
</body>
</html>
EOF
```

---

## 🛡️ Security Questions

### Q: Does this service read or modify my traffic content?

**A:** No, the service only redirects traffic flow. It doesn't inspect, modify, or store any traffic content. HTTPS
traffic is never touched.

### Q: Is DNS hijacking secure?

**A:** The temporary DNS hijacking is secure because:
- It's limited to the local network
- Only occurs during captive portal detection
- Automatically reverses after authentication
- Doesn't affect encrypted DNS (DoH/DoT)

### Q: Can this be used maliciously?

**A:** Like any network tool, it could be misused, but the service includes safeguards:
- Limited to local network interfaces
- Automatic cleanup mechanisms
- Comprehensive logging
- Requires root privileges

### Q: What happens if the service crashes?

**A:** The service includes cleanup mechanisms that run on termination. If it crashes unexpectedly, you can force
cleanup:
```bash
/usr/sbin/openwrt_captive_monitor --force-cleanup
```

---

## 📊 Performance Questions

### Q: How much resources does this service use?

**A:** Typical resource usage:
  - **CPU**: < 1% average, brief spikes during checks
  - **Memory**: 2-4 MB base, +1-2 MB when HTTP server is active
  - **Storage**: ~1 MB for package and configuration
  - **Network**: Minimal, only for connectivity checks

### Q: Will this slow down my network?

**A:** No impact during normal operation. During captive mode:
- DNS queries go to router instead of external servers (faster)
- HTTP requests are redirected locally (minimal overhead)
- No impact on other traffic types

### Q: Can this handle many client devices?

**A:** Yes, the service scales well:
- DNS hijacking works for any number of clients
- HTTP redirection limited by busybox httpd capacity (~100 concurrent connections)
- Memory usage is constant regardless of client count

---

## 🔧 Advanced Questions

### Q: Can I use this with VLANs?

**A:** Yes, configure the service for your VLAN interface:
```bash
uci set captive-monitor.config.lan_interface='br-lan.10'
uci commit captive-monitor
/etc/init.d/captive-monitor restart
```

### Q: How do I debug issues?

**A:** Enable comprehensive debugging:
```bash
export CAPTIVE_DEBUG="1"
export CAPTIVE_VERBOSE="1"
sh -x /usr/sbin/openwrt_captive_monitor --oneshot 2>&1 | tee /tmp/debug.log
```

### Q: Can I contribute to the project?

**A:** Absolutely! See the [Contributing Guide](../../CONTRIBUTING.md) for guidelines. Common contributions:
- Bug reports and fixes
- Feature suggestions and implementation
- Documentation improvements
- Testing on different hardware

### Q: Where can I get help?

**A:** Multiple support channels:
  - **GitHub Issues**: Bug reports and feature requests
  - **GitHub Discussions**: General questions and help
  - **Documentation**: Comprehensive guides and references
  - **Community**: Other users may have similar questions

---

## 📚 Related Questions

### Q: How is this different from other captive portal solutions?

**A:** Unlike full captive portal implementations, this service:
- Only detects and handles existing portals
- Doesn't create its own authentication system
- Focuses on automatic detection and redirection
- Minimal resource usage and configuration

### Q: Can this work with travel routers?

**A:** Yes, it's ideal for travel routers that frequently connect to different networks with captive portals.

### Q: Will this work with mesh networks?

**A:** It can work with mesh networks, but should be configured on the mesh gateway node that connects to the external
network.

### Q: How does this compare to commercial solutions?

**A:** This is a lightweight, open-source solution focused on detection and redirection. Commercial solutions often
include billing, user management, and advanced features that are beyond the scope of this project.

---

## 🆘 Still Need Help?

If your question isn't answered here:

1. **Check the documentation**: [Full documentation index](../index.md)
2. **Search existing issues**: [GitHub Issues](https://github.com/nagual2/openwrt-captive-monitor/issues)
3. **Ask the community**: [GitHub Discussions](https://github.com/nagual2/openwrt-captive-monitor/discussions)
4. **Create a new issue**: [Report a problem](https://github.com/nagual2/openwrt-captive-monitor/issues/new)

When creating issues, please include:
- OpenWrt version and device
- Package version
- Configuration (sanitized)
- Steps to reproduce
- Expected vs. actual behavior
