#!/bin/bash
#
# Setup script for captive-portal-dual on TrueNAS-dev
# This script configures the environment for dual-channel captive portal authorization
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="/opt/captive-portal-dual"
LOG_DIR="/var/log/captive-portal-dual"
RUNTIME_DIR="/run/captive-portal-dual"
CONFIG_DIR="/etc/captive-portal-dual"
VENV_DIR="$SCRIPT_DIR/venv"

# Network configuration for TrueNAS-dev
PRIMARY_WAN="enp1s0"
SECONDARY_WAN="enp2s0"
PRIMARY_GATEWAY="192.168.1.1"
SECONDARY_GATEWAY="192.168.45.1"

# Function to print status
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

# Install system dependencies
install_dependencies() {
    print_status "Installing system dependencies..."
    
    # Update package list
    apt-get update
    
    # Install required packages
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        curl \
        wget \
        iproute2 \
        iptables \
        net-tools \
        chromium \
        chromium-driver \
        git \
        tmux \
        vim
    
    print_status "System dependencies installed"
}

# Create directories
setup_directories() {
    print_status "Creating directories..."
    
    mkdir -p "$SCRIPT_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$RUNTIME_DIR"
    mkdir -p "$CONFIG_DIR"
    
    # Set permissions
    chown -R root:root "$SCRIPT_DIR"
    chmod 755 "$SCRIPT_DIR"
    chmod 755 "$LOG_DIR"
    chmod 755 "$RUNTIME_DIR"
    chmod 755 "$CONFIG_DIR"
    
    print_status "Directories created"
}

# Setup Python virtual environment
setup_venv() {
    print_status "Setting up Python virtual environment..."
    
    cd "$SCRIPT_DIR"
    
    # Create virtual environment
    python3 -m venv "$VENV_DIR"
    
    # Activate and install packages
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install required packages
    pip install \
        selenium \
        pysocks \
        requests \
        schedule \
        psutil \
        python-dotenv
    
    print_status "Virtual environment configured"
}

# Download scripts
download_scripts() {
    print_status "Downloading captive-portal-dual scripts..."
    
    cd "$SCRIPT_DIR"
    
    # Clone or copy scripts (adjust path as needed)
    if [[ -d "/mnt/c/Git/openwrt-captive-monitor" ]]; then
        print_status "Copying from Windows shared directory..."
        cp -r /mnt/c/Git/openwrt-captive-monitor/tools/captive-portal-dual.py .
        cp -r /mnt/c/Git/openwrt-captive-monitor/tools/conn4_auth_lib.py .
        cp -r /mnt/c/Git/openwrt-captive-monitor/tools/conn4_utils.py .
    else
        print_warning "Local copy not found, using git..."
        git clone https://github.com/user/openwrt-captive-monitor.git /tmp/captive-monitor
        cp /tmp/captive-monitor/tools/captive-portal-dual.py .
        cp /tmp/captive-monitor/tools/conn4_auth_lib.py .
        rm -rf /tmp/captive-monitor
    fi
    
    # Make scripts executable
    chmod +x captive-portal-dual.py
    
    print_status "Scripts downloaded"
}

# Create configuration file
create_config() {
    print_status "Creating configuration file..."
    
    cat > "$CONFIG_DIR/config.json" <<EOF
{
    "primary": {
        "name": "wan",
        "interface": "$PRIMARY_WAN",
        "gateway": "$PRIMARY_GATEWAY",
        "check_url": "http://www.msftconnecttest.com/connecttest.txt",
        "priority": 1
    },
    "secondary": {
        "name": "wan2",
        "interface": "$SECONDARY_WAN",
        "gateway": "$SECONDARY_GATEWAY",
        "check_url": "http://www.msftconnecttest.com/connecttest.txt",
        "priority": 2
    },
    "socks_proxy": {
        "host": "127.0.0.1",
        "port": 1080
    },
    "cookie_ttl": 3600,
    "check_interval": 60
}
EOF
    
    print_status "Configuration created at $CONFIG_DIR/config.json"
}

# Create systemd service
create_service() {
    print_status "Creating systemd service..."
    
    cat > /etc/systemd/system/captive-portal-dual.service <<EOF
[Unit]
Description=Dual-channel Captive Portal Authorization
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$SCRIPT_DIR
Environment=RUNTIME_DIR=$RUNTIME_DIR
Environment=LOG_FILE=$LOG_DIR/captive_dual.log
Environment=COOKIES_FILE=$RUNTIME_DIR/captive_dual_cookies.pkl
Environment=COOKIES_META_FILE=$RUNTIME_DIR/captive_dual_cookies_meta.json
Environment=PATH=$VENV_DIR/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin
ExecStart=$VENV_DIR/bin/python $SCRIPT_DIR/captive-portal-dual.py --daemon
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=captive-portal-dual

[Install]
WantedBy=multi-user.target
EOF
    
    # Create SOCKS proxy service
    cat > /etc/systemd/system/captive-portal-dual-proxy.service <<EOF
[Unit]
Description=SOCKS Proxy for Captive Portal Dual
After=captive-portal-dual.service
Wants=captive-portal-dual.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$SCRIPT_DIR
Environment=PATH=$VENV_DIR/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin
ExecStart=$VENV_DIR/bin/python $SCRIPT_DIR/captive-portal-dual.py --proxy-channel secondary
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    
    print_status "Systemd services created"
}

# Setup network interfaces
setup_network() {
    print_status "Configuring network interfaces..."
    
    # Check if interfaces exist
    if ! ip link show "$PRIMARY_WAN" &>/dev/null; then
        print_warning "Primary interface $PRIMARY_WAN not found"
        print_warning "Available interfaces:"
        ip link show | grep "^[0-9]" | awk '{print $2}' | sed 's/://'
    fi
    
    if ! ip link show "$SECONDARY_WAN" &>/dev/null; then
        print_warning "Secondary interface $SECONDARY_WAN not found"
    fi
    
    # Create network configuration script
    cat > "$SCRIPT_DIR/setup-routing.sh" <<'SCRIPT'
#!/bin/bash
# Setup policy-based routing for dual WAN

# Create routing tables
echo "100 primary" >> /etc/iproute2/rt_tables
echo "101 secondary" >> /etc/iproute2/rt_tables

# Add routes
ip route add default via 192.168.1.1 dev enp1s0 table primary
ip route add default via 192.168.45.1 dev enp2s0 table secondary

# Add rules
ip rule add from 192.168.1.0/24 lookup primary priority 1000
ip rule add from 192.168.45.0/24 lookup secondary priority 1001

echo "Routing configured"
SCRIPT
    
    chmod +x "$SCRIPT_DIR/setup-routing.sh"
    
    print_status "Network configuration script created"
}

# Create helper scripts
create_helpers() {
    print_status "Creating helper scripts..."
    
    # Check status script
    cat > "$SCRIPT_DIR/check-status.sh" <<'SCRIPT'
#!/bin/bash
# Check connectivity status for both channels

cd /opt/captive-portal-dual
source venv/bin/activate
python3 captive-portal-dual.py --check-only
SCRIPT
    chmod +x "$SCRIPT_DIR/check-status.sh"
    
    # Manual auth script
    cat > "$SCRIPT_DIR/auth-now.sh" <<'SCRIPT'
#!/bin/bash
# Run authorization immediately

cd /opt/captive-portal-dual
source venv/bin/activate
python3 captive-portal-dual.py
SCRIPT
    chmod +x "$SCRIPT_DIR/auth-now.sh"
    
    # Start proxy script
    cat > "$SCRIPT_DIR/start-proxy.sh" <<'SCRIPT'
#!/bin/bash
# Start SOCKS proxy

if [ -z "$1" ]; then
    echo "Usage: $0 <primary|secondary>"
    exit 1
fi

cd /opt/captive-portal-dual
source venv/bin/activate
python3 captive-portal-dual.py --proxy-channel "$1"
SCRIPT
    chmod +x "$SCRIPT_DIR/start-proxy.sh"
    
    print_status "Helper scripts created"
}

# Create log rotation
setup_logrotate() {
    print_status "Setting up log rotation..."
    
    cat > /etc/logrotate.d/captive-portal-dual <<EOF
$LOG_DIR/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
    postrotate
        /bin/kill -HUP \$(cat /var/run/syslogd.pid 2> /dev/null) 2> /dev/null || true
    endscript
}
EOF
    
    print_status "Log rotation configured"
}

# Create environment file
create_env() {
    print_status "Creating environment file..."
    
    cat > "$CONFIG_DIR/.env" <<EOF
# Captive Portal Dual Environment Configuration
RUNTIME_DIR=$RUNTIME_DIR
LOG_FILE=$LOG_DIR/captive_dual.log
LOCK_FILE=$RUNTIME_DIR/captive_dual.lock
COOKIES_FILE=$RUNTIME_DIR/captive_dual_cookies.pkl
COOKIES_META_FILE=$RUNTIME_DIR/captive_dual_cookies_meta.json

# Chrome settings
CHROME_BIN=/usr/bin/chromium
CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Network interfaces
PRIMARY_WAN=$PRIMARY_WAN
SECONDARY_WAN=$SECONDARY_WAN
PRIMARY_GATEWAY=$PRIMARY_GATEWAY
SECONDARY_GATEWAY=$SECONDARY_GATEWAY
EOF
    
    chmod 600 "$CONFIG_DIR/.env"
    print_status "Environment file created"
}

# Main installation
main() {
    print_status "Starting setup for captive-portal-dual on TrueNAS-dev..."
    
    check_root
    install_dependencies
    setup_directories
    setup_venv
    download_scripts
    create_config
    create_service
    setup_network
    create_helpers
    setup_logrotate
    create_env
    
    print_status "========================================"
    print_status "Setup completed successfully!"
    print_status "========================================"
    print_status ""
    print_status "Next steps:"
    print_status "1. Edit configuration: $CONFIG_DIR/config.json"
    print_status "2. Configure network interfaces: $SCRIPT_DIR/setup-routing.sh"
    print_status "3. Start service: systemctl start captive-portal-dual"
    print_status "4. Enable auto-start: systemctl enable captive-portal-dual"
    print_status ""
    print_status "Helper commands:"
    print_status "  - Check status: $SCRIPT_DIR/check-status.sh"
    print_status "  - Auth now: $SCRIPT_DIR/auth-now.sh"
    print_status "  - Start proxy: $SCRIPT_DIR/start-proxy.sh <primary|secondary>"
    print_status ""
    print_status "Logs: tail -f $LOG_DIR/captive_dual.log"
    print_status ""
}

# Run main function
main "$@"
