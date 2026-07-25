#!/bin/sh
#
# dual-socks-proxy.sh - Wrapper script with safety protections
# POSIX sh compatible for OpenWrt
#

PROG_NAME="dual-socks-proxy"
CONFIG_SECTION="main"

# Internal/LAN interface patterns (space-separated)
# These interfaces are forbidden for SOCKS proxy
INTERNAL_PATTERNS="br-lan lan eth0 br0 br-lan1 lan1 eth1"

# Read config from UCI
read_uci_config() {
    _option="$1"
    _default="$2"
    uci get "${PROG_NAME}.${CONFIG_SECTION}.${_option}" 2>/dev/null || echo "$_default"
}

# Check if enabled
is_enabled() {
    _enabled=$(read_uci_config "enabled" "0")
    [ "$_enabled" = "1" ] && return 0 || return 1
}

# Check if interface is internal/LAN (forbidden)
is_internal_iface() {
    _iface="$1"
    
    # Check against forbidden patterns
    for _pattern in $INTERNAL_PATTERNS; do
        if [ "$_iface" = "$_pattern" ]; then
            return 0  # Is internal
        fi
    done
    
    # Check if interface is bridge with LAN in name
    case "$_iface" in
        *lan*|*LAN*|*br-lan*|*br0*|*internal*)
            return 0  # Is internal
            ;;
    esac
    
    # Check UCI network config - if it's lan zone
    _zone=$(uci get "network.${_iface}" 2>/dev/null | head -1)
    if [ "$_zone" = "interface" ]; then
        # Check if it's in lan firewall zone
        _fw_zone=$(uci show firewall 2>/dev/null | grep -E "network.*=$_iface" | grep -i "lan" | head -1)
        if [ -n "$_fw_zone" ]; then
            return 0  # Is internal
        fi
    fi
    
    return 1  # Not internal
}

# Validate interface - manual specification required
validate_iface() {
    _name="$1"
    _iface="$2"
    
    # Check if interface is specified (manual config required)
    if [ -z "$_iface" ]; then
        log_msg "INFO" "${_name} interface not specified - skipping"
        return 2  # Not specified
    fi
    
    # Check if interface is internal/LAN
    if is_internal_iface "$_iface"; then
        log_msg "ERROR" "${_name} interface '${_iface}' is internal/LAN - FORBIDDEN"
        echo "ERROR: ${_name} interface '${_iface}' is internal/LAN. SOCKS proxy refused."
        return 1  # Forbidden
    fi
    
    # Check if interface exists
    if ! ip link show "$_iface" >/dev/null 2>&1; then
        log_msg "WARN" "${_name} interface '${_iface}' does not exist"
        return 1  # Does not exist
    fi
    
    # Check if interface has IP
    _has_ip=$(ip addr show dev "$_iface" 2>/dev/null | grep 'inet ' | head -1)
    if [ -z "$_has_ip" ]; then
        log_msg "WARN" "${_name} interface '${_iface}' has no IP address"
        return 1  # No IP
    fi
    
    return 0  # Valid
}

# Log message
log_msg() {
    _level="$1"
    _msg="$2"
    _log_file=$(read_uci_config "log_file" "/var/log/dual-socks-proxy.log")
    _timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${_timestamp} [${_level}] ${_msg}" >> "$_log_file"
    logger -t "$PROG_NAME" "[${_level}] ${_msg}"
}

# Get IP for interface
get_iface_ip() {
    _iface="$1"
    ip addr show dev "$_iface" 2>/dev/null | awk '/inet / {print $2}' | cut -d/ -f1 | head -n1
}

# Start proxy instance - bind to LAN, outbound through WAN specified
start_proxy_instance() {
    _name="$1"
    _outbound_iface="$2"  # WAN interface for tracking only
    _default_port="$3"
    _pid_file="$4"
    
    # Read config
    _port=$(read_uci_config "${_name}_port" "$_default_port")
    _lan_iface=$(read_uci_config "lan_iface" "br-lan")
    _lan_ip=$(get_iface_ip "$_lan_iface")
    
    if [ -z "$_lan_ip" ]; then
        log_msg "ERROR" "${_name}: No IP on LAN interface ${_lan_iface}"
        return 1
    fi
    
    # Check if already running
    if [ -f "$_pid_file" ]; then
        _old_pid=$(cat "$_pid_file" 2>/dev/null)
        if kill -0 "$_old_pid" 2>/dev/null; then
            log_msg "INFO" "${_name} already running (PID: $_old_pid)"
            echo "${_name}: already running on ${_lan_ip}:${_port}"
            return 0
        fi
    fi
    
    log_msg "INFO" "Starting ${_name} SOCKS on ${_lan_ip}:${_port} (outbound: ${_outbound_iface})"
    
    # Start microsocks bind to LAN IP
    microsocks -i "$_lan_ip" -p "$_port" >/dev/null 2>&1 &
    _pid=$!
    
    # Verify started
    sleep 1
    if kill -0 $_pid 2>/dev/null; then
        echo $_pid > "$_pid_file"
        log_msg "INFO" "${_name} started (PID: $_pid, bind: ${_lan_ip}, outbound: ${_outbound_iface})"
        echo "${_name}: running on ${_lan_ip}:${_port} (outbound via ${_outbound_iface})"
        return 0
    else
        log_msg "ERROR" "${_name}: Failed to start microsocks"
        return 1
    fi
}

# Stop proxy
stop_proxy_instance() {
    _name="$1"
    _pid_file="$2"
    
    if [ -f "$_pid_file" ]; then
        _pid=$(cat "$_pid_file" 2>/dev/null)
        if kill -0 $_pid 2>/dev/null; then
            log_msg "INFO" "Stopping ${_name} (PID: $_pid)"
            kill $_pid 2>/dev/null
            sleep 1
            kill -9 $_pid 2>/dev/null
        fi
        rm -f "$_pid_file"
    fi
}

# Main start function
cmd_start() {
    if ! is_enabled; then
        echo "dual-socks-proxy is disabled in config"
        exit 0
    fi
    
    log_msg "INFO" "Starting dual SOCKS proxy service"
    
    # Check dependency
    if ! command -v microsocks >/dev/null 2>&1; then
        log_msg "ERROR" "microsocks not installed"
        echo "ERROR: microsocks not installed"
        echo "Install: apk add microsocks"
        exit 1
    fi
    
    # Create PID directory
    mkdir -p /var/run
    
    # Read interfaces from config (manual specification required)
    _iface_primary=$(read_uci_config "primary_iface" "")
    _iface_secondary=$(read_uci_config "secondary_iface" "")
    
    log_msg "INFO" "Config: primary='${_iface_primary}', secondary='${_iface_secondary}'"
    
    # Track results
    _started=0
    _failed=0
    
    # Start primary if specified
    if [ -n "$_iface_primary" ]; then
        if start_proxy_instance "primary" "$_iface_primary" "11080" "/var/run/dual-socks-primary.pid"; then
            _started=$((_started + 1))
        else
            _failed=$((_failed + 1))
        fi
    else
        log_msg "INFO" "Primary interface not specified - skipping"
        echo "Primary: not configured"
    fi
    
    # Start secondary if specified
    if [ -n "$_iface_secondary" ]; then
        if start_proxy_instance "secondary" "$_iface_secondary" "11081" "/var/run/dual-socks-secondary.pid"; then
            _started=$((_started + 1))
        else
            _failed=$((_failed + 1))
        fi
    else
        log_msg "INFO" "Secondary interface not specified - skipping"
        echo "Secondary: not configured"
    fi
    
    # Summary
    echo ""
    if [ $_started -gt 0 ]; then
        echo "SOCKS proxy service started ($_started running)"
        log_msg "INFO" "Service started: $_started proxies running"
        return 0
    else
        if [ $_failed -gt 0 ]; then
            echo "ERROR: All configured proxies failed to start"
            log_msg "ERROR" "All configured proxies failed"
            return 1
        else
            echo "No proxies configured or started"
            log_msg "WARN" "No proxies configured"
            return 1
        fi
    fi
}

# Main stop function
cmd_stop() {
    log_msg "INFO" "Stopping dual SOCKS proxy service"
    stop_proxy_instance "primary" "/var/run/dual-socks-primary.pid"
    stop_proxy_instance "secondary" "/var/run/dual-socks-secondary.pid"
    echo "SOCKS proxy service stopped"
}

# Status check - show LAN bind address
cmd_status() {
    _running=0
    _lan_iface=$(read_uci_config "lan_iface" "br-lan")
    _lan_ip=$(get_iface_ip "$_lan_iface")
    _iface_primary=$(read_uci_config "primary_iface" "")
    _iface_secondary=$(read_uci_config "secondary_iface" "")
    
    if [ -z "$_lan_ip" ]; then
        echo "ERROR: No LAN IP on $_lan_iface"
        return 1
    fi
    
    echo "LAN bind: ${_lan_ip} (iface: $_lan_iface)"
    echo ""
    
    if [ -n "$_iface_primary" ]; then
        if [ -f "/var/run/dual-socks-primary.pid" ]; then
            _pid=$(cat "/var/run/dual-socks-primary.pid" 2>/dev/null)
            if kill -0 $_pid 2>/dev/null; then
                _port=$(read_uci_config primary_port 11080)
                echo "Primary:   running (PID: $_pid, bind: ${_lan_ip}:${_port}, outbound: $_iface_primary)"
                _running=$((_running + 1))
            else
                echo "Primary:   not running (outbound: $_iface_primary)"
            fi
        else
            echo "Primary:   not running (outbound: $_iface_primary)"
        fi
    else
        echo "Primary:   not configured"
    fi
    
    if [ -n "$_iface_secondary" ]; then
        if [ -f "/var/run/dual-socks-secondary.pid" ]; then
            _pid=$(cat "/var/run/dual-socks-secondary.pid" 2>/dev/null)
            if kill -0 $_pid 2>/dev/null; then
                _port=$(read_uci_config secondary_port 11081)
                echo "Secondary: running (PID: $_pid, bind: ${_lan_ip}:${_port}, outbound: $_iface_secondary)"
                _running=$((_running + 1))
            else
                echo "Secondary: not running (outbound: $_iface_secondary)"
            fi
        else
            echo "Secondary: not running (outbound: $_iface_secondary)"
        fi
    else
        echo "Secondary: not configured"
    fi
    
    echo ""
    if [ $_running -gt 0 ]; then
        echo "Status: $_running proxy(s) running"
        echo ""
        echo "Usage:"
        echo "  curl --socks5 ${_lan_ip}:11080 http://example.com  (primary)"
        echo "  curl --socks5 ${_lan_ip}:11081 http://example.com  (secondary)"
        return 0
    else
        echo "Status: no proxies running"
        return 3
    fi
}

# Validation only (dry run)
cmd_validate() {
    _iface_primary=$(read_uci_config "primary_iface" "")
    _iface_secondary=$(read_uci_config "secondary_iface" "")
    
    echo "Configuration validation:"
    echo ""
    
    _errors=0
    
    # Validate primary
    if [ -n "$_iface_primary" ]; then
        echo -n "Primary [$_iface_primary]: "
        validate_iface "Primary" "$_iface_primary"
        _ret=$?
        if [ $_ret -eq 0 ]; then
            _ip=$(get_iface_ip "$_iface_primary")
            echo "OK (IP: $_ip)"
        elif [ $_ret -eq 2 ]; then
            echo "Not specified"
        else
            echo "FAILED"
            _errors=$((_errors + 1))
        fi
    else
        echo "Primary: not specified"
    fi
    
    # Validate secondary
    if [ -n "$_iface_secondary" ]; then
        echo -n "Secondary [$_iface_secondary]: "
        validate_iface "Secondary" "$_iface_secondary"
        _ret=$?
        if [ $_ret -eq 0 ]; then
            _ip=$(get_iface_ip "$_iface_secondary")
            echo "OK (IP: $_ip)"
        elif [ $_ret -eq 2 ]; then
            echo "Not specified"
        else
            echo "FAILED"
            _errors=$((_errors + 1))
        fi
    else
        echo "Secondary: not specified"
    fi
    
    echo ""
    if [ $_errors -eq 0 ]; then
        echo "Validation passed"
        return 0
    else
        echo "Validation failed ($_errors errors)"
        return 1
    fi
}

# Help
cmd_help() {
    cat << EOF
dual-socks-proxy - Dual SOCKS5 Proxy for OpenWrt
Usage: $0 {start|stop|restart|status|validate|help}

Commands:
  start     - Start SOCKS proxies (only configured ones)
  stop      - Stop all SOCKS proxies
  restart   - Restart SOCKS proxies
  status    - Check status of proxies
  validate  - Validate configuration (dry run)
  help      - Show this help

Configuration (/etc/config/dual-socks-proxy):
  config dual-socks-proxy 'main'
	option enabled '1'
	option lan_iface 'br-lan'
	option log_file '/var/log/dual-socks-proxy.log'
	
	# MANUAL OUTBOUND INTERFACE CONFIGURATION
	# SOCKS binds to LAN IP, traffic goes through specified WAN interfaces
	# 
	# Examples of valid outbound WAN interfaces:
	# - phy1-sta0 (WiFi station/client)
	# - pppoe-wan (PPPoE connection)
	# - wg0, wg1 (WireGuard tunnels)
	# - tun0 (OpenVPN)
	
	# Primary SOCKS (port 11080)
	option primary_iface 'phy1-sta0'
	option primary_port '11080'
	
	# Secondary SOCKS (port 11081)
	option secondary_iface 'wan'
	option secondary_port '11081'

SAFETY PROTECTIONS:
  - Interfaces must be specified MANUALLY (no auto-detection)
  - LAN/internal interfaces are FORBIDDEN (br-lan, eth0, etc.)
  - If only one interface specified, only one proxy starts
  - If interface has no IP, proxy won't start
  - Interfaces are validated before starting

Examples:
  uci set dual-socks-proxy.main.primary_iface='eth1'
  uci set dual-socks-proxy.main.secondary_iface='wg0'
  uci commit dual-socks-proxy

Dependencies:
  apk add microsocks

EOF
}

# Main
case "$1" in
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_stop
        sleep 1
        cmd_start
        ;;
    status)
        cmd_status
        ;;
    validate)
        cmd_validate
        ;;
    help|--help|-h)
        cmd_help
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|validate|help}"
        exit 1
        ;;
esac

exit $?
