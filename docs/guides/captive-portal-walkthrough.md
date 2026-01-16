# Captive Portal Walkthrough

---

## 🌐 Language / Язык

**English** | [Русский](README.ru.md)

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

---

## 🧩 NoJS план доработок (conn4.com)

> Этот план носит ориентировочный характер и не является строгой спецификацией. Конкретные шаги и приоритеты могут меняться по мере эволюции портала и скриптов.

Основная цель: приблизить `test_conn4_portal_nojs.py` по возможностям к `captive_portal_wsl_selenium.py`, максимально используя артефакты Selenium и при этом оставаясь «без JS» на стороне клиента.

### 1. Усиление сбора токенов в nojs

- В `_collect_tokens` дополнительно разбирать query текущего URL (`page_url/portal_url`) и подмешивать параметры:
  - `client_ip`, `client_mac`, `site_id`, `signature`, `loggedin`, `remembered_mac`, `cookie-challenge`.
- Для совместимости с Selenium добавлять camelCase-версии:
  - `client_ip → clientIp`, `client_mac → clientMac`, `site_id → siteId`.
- При объединении HTML/JS-токенов с `dynamic_tokens` отдавать приоритет значениям из `dynamic_tokens` (особенно когда они приходят из артефактов Selenium).

### 2. Более плотная интеграция с артефактами Selenium

- Воспринимать `conn4_debug_*.json` и `conn4_compare*.json` как основной источник «эталонного» поведения:
  - поднимать оттуда `computedTokens` и сохранять в `dynamic_tokens`;
  - если в сравнении есть `network`/`networkSummary`, использовать их в `apply_captured_flow` как основной сценарий воспроизведения.
- В `apply_captured_flow` проигрывать события в приоритете:
  - `/_time`, `/ident`, `/wbs/api/v1/create-session/`, `/wbs/api/v1/login/free/`,
  - затем остальные `conn4.com`‑запросы.

### 3. Улучшение `/ident` и работы с куками

- После `detect_portal_via_redirect` и `sync_time`:
  - если `himalaya-site-ident` отсутствует, но есть токены `site_id/client_ip/client_mac/signature` (из URL,cookie или артефакта), делать явный вызов `/ident`:
    - либо по схеме `https://<site_id>.rdr.conn4.com/ident?...`, как в Selenium,
    - либо через `/admon-assets/ident.php` как fallback.
- После удачного `/ident`:
  - обновлять `dynamic_tokens` и `initial_query` на основе новых cookie/URL,
  - повторно вызывать `_detect_client_ip_mac`, чтобы все последующие шаги опирались на актуальные IP/MAC.

### 4. Сближение WBS API flow с Selenium

- В `_call_create_session_api` и `_run_api_flow`:
  - логировать используемый `authorization=token=...`/`session=...` так, чтобы его можно было сравнивать с браузерным (через `networkSummary`).
- При наличии артефакта Selenium:
  - проверять, совпадают ли `locationId/siteId`, `clientIp/client_ip`, `clientMac/client_mac` и формат `authorization` с тем, что видно в сетевых событиях браузера.
- При отсутствии артефакта:
  - использовать локально сгенерированный `WBSApiAuthToken` на основе `himalaya-site-ident` (как делает Selenium), но с расширенной диагностикой ошибок.

### 5. Пост-авторизационный connectivity check

- После успешного `run_flow()` и/или `apply_captured_flow()`:
  - выполнять короткий HTTP‑проверочный цикл через SOCKS (аналог `check_internet_via_socks`);
  - подтверждать успех, если:
    - `generate_204`/`canonical.html` возвращают 2xx без редиректа,
    - `detect_portal_via_redirect` больше не ведет на `conn4.com`.
- Логировать этот шаг как явное подтверждение того, что «интернет есть и captive portal пройден».

### 6. Диагностический «план nojs»

- Использовать уже формируемый `nojs_plan` в master‑отчете Selenium как ориентир:
  - логировать его в nojs‑скрипте при наличии соответствующего JSON рядом;
  - по возможности отмечать, какие шаги плана реально выполнены (`login free`, `cookie-challenge`, `/ident`, `create-session`, `login/free` и т.д.).
- Подчеркнуть в документации, что этот план — ориентир, а не жесткий контракт: реальные порталы и их версии могут требовать адаптации шагов.
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
