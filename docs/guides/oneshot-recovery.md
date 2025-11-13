# Oneshot Recovery Mode

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---


Complete guide to using **openwrt-captive-monitor** in oneshot mode for manual connectivity recovery and scheduled operations.

## 🎯 What is Oneshot Mode?

Oneshot mode performs a single connectivity check and exits, making it ideal for:

- **Manual troubleshooting** and diagnostics
- **Scheduled execution** via cron or other automation
- **Integration** with custom scripts and workflows
- **Testing** configuration changes
- **Resource-constrained** environments where continuous monitoring isn't needed

---

## ⚙️ Oneshot Mode Configuration

### Basic Configuration

```uci
## /etc/config/captive-monitor
config captive_monitor 'config'
    option enabled '1'
    option mode 'oneshot'                 # Single check mode
    option wifi_interface 'phy1-sta0'
    option wifi_logical 'wwan'
    option ping_servers '1.1.1.1 8.8.8.8'
    option enable_syslog '1'
```

### Command-Line Usage

```bash
## Basic oneshot execution
/usr/sbin/openwrt_captive_monitor --oneshot

## With custom interface
/usr/sbin/openwrt_captive_monitor --oneshot --interface wlan0 --logical wan

## Verbose output for debugging
/usr/sbin/openwrt_captive_monitor --oneshot --verbose

## Dry run (no changes made)
/usr/sbin/openwrt_captive_monitor --oneshot --dry-run
```

---

## 📋 Oneshot Execution Flow

### Step-by-Step Process

1. **Initialize** configuration and interfaces
2. **Check gateway** connectivity
3. **Test internet** connectivity
4. **Detect captive portal** (if applicable)
5. **Apply fixes** (WiFi restart, captive interception)
6. **Wait for restoration** (if in captive mode)
7. **Cleanup** and exit

### Return Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | Internet is working or was restored |
| 1 | Configuration Error | Invalid configuration or missing dependencies |
| 2 | Network Error | Gateway unreachable or network configuration issue |
| 3 | Captive Portal Detected | Captive portal active (may require manual intervention) |
| 4 | Timeout | Operations timed out |

---

## 🕐 Scheduled Execution

### Cron Configuration

```bash
## Edit root crontab
crontab -e

## Add oneshot execution every 5 minutes
*/5 * * * * /usr/sbin/openwrt_captive_monitor --oneshot

## Add every 15 minutes with logging
*/15 * * * * /usr/sbin/openwrt_captive_monitor --oneshot >> /var/log/captive-oneshot.log 2>&1

## Add hourly with verbose output
0 * * * * /usr/sbin/openwrt_captive_monitor --oneshot --verbose >> /var/log/captive-oneshot.log 2>&1
```

### Systemd Timer (if available)

```bash
## Create systemd service
cat > /etc/systemd/system/captive-monitor-oneshot.service <<'EOF'
[Unit]
Description=OpenWrt Captive Monitor Oneshot
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/sbin/openwrt_captive_monitor --oneshot
StandardOutput=journal
StandardError=journal
EOF

## Create systemd timer
cat > /etc/systemd/system/captive-monitor-oneshot.timer <<'EOF'
[Unit]
Description=Run captive monitor oneshot every 10 minutes
Requires=captive-monitor-oneshot.service

[Timer]
OnCalendar=*:0/10
Persistent=true

[Install]
WantedBy=timers.target
EOF

## Enable and start timer
systemctl enable captive-monitor-oneshot.timer
systemctl start captive-monitor-oneshot.timer
```

---

## 🔧 Advanced Oneshot Scenarios

### Scenario 1: Network Interface Recovery

```bash
#!/bin/sh
## /usr/local/bin/network-recovery.sh

## Check if interface is down
if ! ip link show phy1-sta0 | grep -q "state UP"; then
    echo "Interface is down, attempting recovery"
    
    # Try to bring interface up
    ifup wwan
    sleep 5
    
    # Run oneshot check
    /usr/sbin/openwrt_captive_monitor --oneshot
    
    # Check result
    if [ $? -eq 0 ]; then
        echo "Network recovery successful"
    else
        echo "Network recovery failed"
        # Send notification or take additional action
    fi
else
    echo "Interface is up, running connectivity check"
    /usr/sbin/openwrt_captive_monitor --oneshot
fi
```

### Scenario 2: Conditional Execution

```bash
#!/bin/sh
## /usr/local/bin/conditional-check.sh

## Only run if specific conditions are met
WIFI_ENABLED=$(uci get wireless.@wifi-iface[0].disabled 2>/dev/null || echo "0")

if [ "$WIFI_ENABLED" = "0" ]; then
    echo "WiFi is enabled, running connectivity check"
    /usr/sbin/openwrt_captive_monitor --oneshot
else
    echo "WiFi is disabled, skipping connectivity check"
    exit 0
fi
```

### Scenario 3: Integration with Network Manager

```bash
#!/bin/sh
## /etc/hotplug.d/iface/99-captive-monitor

## Run oneshot when WAN interface comes up
[ "$INTERFACE" = "wan" ] && [ "$ACTION" = "ifup" ] && {
    echo "WAN interface up, running connectivity check"
    /usr/sbin/openwrt_captive_monitor --oneshot
}
```

---

## 📊 Monitoring and Logging

### Enhanced Logging

```bash
## Create comprehensive logging script
cat > /usr/local/bin/captive-oneshot-logger.sh <<'EOF'
#!/bin/sh

LOG_FILE="/var/log/captive-oneshot.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
RESULT_FILE="/tmp/captive-oneshot-result"

echo "=== Captive Monitor Oneshot - $TIMESTAMP ===" >> $LOG_FILE

## Run oneshot with verbose output
/usr/sbin/openwrt_captive_monitor --oneshot --verbose >> $LOG_FILE 2>&1
EXIT_CODE=$?

## Log result
case $EXIT_CODE in
    0)
        echo "Result: SUCCESS - Internet is working" >> $LOG_FILE
        ;;
    1)
        echo "Result: ERROR - Configuration issue" >> $LOG_FILE
        ;;
    2)
        echo "Result: ERROR - Network issue" >> $LOG_FILE
        ;;
    3)
        echo "Result: WARNING - Captive portal detected" >> $LOG_FILE
        ;;
    4)
        echo "Result: ERROR - Timeout" >> $LOG_FILE
        ;;
    *)
        echo "Result: UNKNOWN - Exit code $EXIT_CODE" >> $LOG_FILE
        ;;
esac

echo "" >> $LOG_FILE

## Store result for other scripts
echo $EXIT_CODE > $RESULT_FILE

exit $EXIT_CODE
EOF

chmod +x /usr/local/bin/captive-oneshot-logger.sh
```

### Log Analysis

```bash
## Analyze oneshot results
cat > /usr/local/bin/analyze-oneshot.sh <<'EOF'
#!/bin/sh

LOG_FILE="/var/log/captive-oneshot.log"
DAYS=7

echo "=== Oneshot Analysis (Last $DAYS days) ==="

## Count results by type
echo "Results Summary:"
grep "Result:" $LOG_FILE | tail -100 | sort | uniq -c | sort -nr

## Show recent failures
echo -e "\nRecent Failures:"
grep "Result: ERROR" $LOG_FILE | tail -10

## Show captive portal detections
echo -e "\nCaptive Portal Detections:"
grep "Result: WARNING" $LOG_FILE | tail -10

## Success rate
TOTAL=$(grep "Result:" $LOG_FILE | wc -l)
SUCCESS=$(grep "Result: SUCCESS" $LOG_FILE | wc -l)
if [ $TOTAL -gt 0 ]; then
    SUCCESS_RATE=$((SUCCESS * 100 / TOTAL))
    echo -e "\nSuccess Rate: $SUCCESS_RATE% ($SUCCESS/$TOTAL)"
else
    echo -e "\nNo results found"
fi
EOF

chmod +x /usr/local/bin/analyze-oneshot.sh
```

---

## 🔄 Integration Examples

### Python Integration

```python
#!/usr/bin/env python3
## captive_monitor_integration.py

import subprocess
import sys
import time
import logging

## Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_captive_oneshot():
    """Run captive monitor oneshot and return result"""
    try:
        result = subprocess.run(
            ['/usr/sbin/openwrt_captive_monitor', '--oneshot'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        logger.info(f"Captive monitor exit code: {result.returncode}")
        if result.stdout:
            logger.info(f"Output: {result.stdout}")
        if result.stderr:
            logger.error(f"Error: {result.stderr}")
            
        return result.returncode
        
    except subprocess.TimeoutExpired:
        logger.error("Captive monitor timed out")
        return 4
    except Exception as e:
        logger.error(f"Error running captive monitor: {e}")
        return 1

def handle_result(exit_code):
    """Handle the result from captive monitor"""
    if exit_code == 0:
        logger.info("Internet connectivity is working")
        return True
    elif exit_code == 3:
        logger.warning("Captive portal detected - manual intervention may be required")
        return False
    else:
        logger.error("Connectivity issue detected")
        return False

def main():
    """Main integration logic"""
    logger.info("Starting connectivity check")
    
    # Run captive monitor
    exit_code = run_captive_oneshot()
    
    # Handle result
    success = handle_result(exit_code)
    
    if not success:
        logger.info("Attempting additional recovery steps")
        # Add custom recovery logic here
        time.sleep(10)
        
        # Retry once
        logger.info("Retrying connectivity check")
        exit_code = run_captive_oneshot()
        success = handle_result(exit_code)
    
    if success:
        logger.info("Connectivity check passed")
        sys.exit(0)
    else:
        logger.error("Connectivity check failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Shell Script Integration

```bash
#!/bin/sh
## /usr/local/bin/network-health-check.sh

MAX_RETRIES=3
RETRY_DELAY=30
LOG_FILE="/var/log/network-health.log"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

run_check() {
    log_message "Starting connectivity check"
    
    /usr/sbin/openwrt_captive_monitor --oneshot >> $LOG_FILE 2>&1
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        log_message "Connectivity check passed"
        return 0
    else
        log_message "Connectivity check failed (exit code: $EXIT_CODE)"
        return 1
    fi
}

## Main logic
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if run_check; then
        log_message "Network is healthy"
        exit 0
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
        log_message "Retrying in $RETRY_DELAY seconds (attempt $RETRY_COUNT/$MAX_RETRIES)"
        sleep $RETRY_DELAY
    fi
done

log_message "Network health check failed after $MAX_RETRIES attempts"
exit 1
```

---

## 🛠️ Troubleshooting Oneshot Mode

### Common Issues

1. **Permission Issues**
   ```bash
   # Check executable permissions
   ls -la /usr/sbin/openwrt_captive_monitor
   
   # Fix permissions if needed
   chmod +x /usr/sbin/openwrt_captive_monitor
   ```

2. **Configuration Issues**
   ```bash
   # Validate UCI configuration
   uci show captive-monitor
   
   # Test with minimal configuration
   /usr/sbin/openwrt_captive_monitor --oneshot --help
   ```

3. **Network Interface Issues**
   ```bash
   # Check interface status
   ip link show $(uci get captive-monitor.config.wifi_interface)
   
   # Check logical interface
   ifstatus $(uci get captive-monitor.config.wifi_logical)
   ```

### Debug Mode

```bash
## Run with maximum debugging
sh -x /usr/sbin/openwrt_captive_monitor --oneshot --verbose 2>&1 | tee /tmp/captive-debug.log

## Check for missing dependencies
for cmd in curl iptables dnsmasq; do
    if ! command -v $cmd >/dev/null 2>&1; then
        echo "Missing dependency: $cmd"
    fi
done
```

### Dry Run Testing

```bash
## Test what would happen without making changes
/usr/sbin/openwrt_captive_monitor --oneshot --dry-run --verbose

## Test with custom configuration
export WIFI_INTERFACE="test-interface"
export MONITOR_INTERVAL="10"
/usr/sbin/openwrt_captive_monitor --oneshot --dry-run
```

---

## 📈 Performance Optimization

### Resource Usage

```bash
## Monitor resource usage during oneshot
time /usr/sbin/openwrt_captive_monitor --oneshot

## Check memory usage
/usr/bin/time -v /usr/sbin/openwrt_captive_monitor --oneshot
```

### Optimization Tips

1. **Reduce Timeout Values**
   ```bash
   export PING_TIMEOUT="1"
   export HTTP_PROBE_TIMEOUT="3"
   export INTERNET_CHECK_DELAY="1"
   ```

2. **Use Fewer Ping Servers**
   ```bash
   export PING_SERVERS="8.8.8.8"
   ```

3. **Disable Verbose Logging**
   ```bash
   /usr/sbin/openwrt_captive_monitor --oneshot --syslog-only
   ```

---

## 🎯 Best Practices

### Configuration Best Practices

1. **Use appropriate intervals** for scheduled execution
2. **Implement proper logging** for monitoring and debugging
3. **Handle return codes** appropriately in scripts
4. **Test thoroughly** before deploying to production

### Operational Best Practices

1. **Monitor execution logs** regularly
2. **Set up alerts** for repeated failures
3. **Document custom integrations** clearly
4. **Test network changes** with oneshot mode first

### Security Considerations

1. **Run with minimal privileges** when possible
2. **Secure log files** appropriately
3. **Validate inputs** in custom scripts
4. **Audit custom integrations** regularly

---

## 📚 Related Documentation

- [Basic Configuration](../configuration/basic-config.md) - Core configuration options
- [Advanced Configuration](../configuration/advanced-config.md) - Advanced settings and customization
- [Captive Portal Walkthrough](captive-portal-walkthrough.md) - Complete captive portal handling example
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

Oneshot mode provides flexibility for manual operations, scheduled tasks, and custom integrations while maintaining the robust connectivity checking and captive portal detection capabilities of the full monitor mode.
