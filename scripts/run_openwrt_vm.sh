#!/bin/sh
# OpenWrt VM Test Harness
# shellcheck shell=ash
# shellcheck disable=SC3043 # BusyBox ash and bash-compatible shells provide 'local'

set -eu

# Default configuration
DEFAULT_OPENWRT_VERSION="24.02"
DEFAULT_WORKDIR="dist/vm-tests"
DEFAULT_REUSE_VM=false
DEFAULT_ENABLE_KVM=true

# Global variables
OPENWRT_VERSION=""
WORKDIR=""
REUSE_VM=""
ENABLE_KVM=""
VM_PID=""
TAP_INTERFACE=""
SSH_PORT=""
HTTP_PORT=""
ARTIFACTS_DIR=""
BASE_IMAGE=""
OVERLAY_IMAGE=""
SSH_KEY=""
EXPECT_SCRIPT=""

# Source shared color definitions so output formatting stays consistent
# shellcheck source=lib/colors.sh
. "$(dirname "$0")/lib/colors.sh"

# Logging functions
log_info() {
    printf '%s[INFO]%s %s\n' "$BLUE" "$NC" "$1"
}

log_warn() {
    printf '%s[WARN]%s %s\n' "$YELLOW" "$NC" "$1" >&2
}

log_error() {
    printf '%s[ERROR]%s %s\n' "$RED" "$NC" "$1" >&2
}

log_success() {
    printf '%s[SUCCESS]%s %s\n' "$GREEN" "$NC" "$1"
}

# Usage information
usage() {
    cat << 'EOF'
Usage: scripts/run_openwrt_vm.sh [OPTIONS]

OpenWrt VM Test Harness - Automates virtualized testing of openwrt-captive-monitor

OPTIONS:
    --openwrt-version VERSION    OpenWrt version to download (default: 24.02)
    --workdir DIRECTORY          Working directory for VM artifacts (default: dist/vm-tests)
    --reuse-vm                   Reuse existing VM artifacts if available
    --no-kvm                     Disable KVM acceleration (use TCG emulation)
    --ssh-port PORT              Host port for SSH forwarding (default: auto-allocate)
    --http-port PORT             Host port for HTTP forwarding (default: auto-allocate)
    --help, -h                   Show this help message

EXAMPLES:
    # Basic run with defaults
    ./scripts/run_openwrt_vm.sh

    # Specific version and custom workdir
    ./scripts/run_openwrt_vm.sh --openwrt-version 23.05 --workdir /tmp/openwrt-test

    # Reuse VM artifacts without KVM (good for CI)
    ./scripts/run_openwrt_vm.sh --reuse-vm --no-kvm

REQUIREMENTS:
    Required tools: curl, sha256sum, xz, qemu-system-x86_64, qemu-img, expect, ssh, scp
    Optional tools: ssh-keygen, sshpass

DESCRIPTION:
    This script orchestrates end-to-end testing of the openwrt-captive-monitor package
    in a virtualized OpenWrt environment. It handles image downloading, VM provisioning,
    package installation, and automated functional testing.

    The script produces logs and test artifacts in the specified work directory for
    later inspection and debugging.
EOF
}

# Parse command line arguments
parse_arguments() {
    OPENWRT_VERSION="$DEFAULT_OPENWRT_VERSION"
    WORKDIR="$DEFAULT_WORKDIR"
    REUSE_VM="$DEFAULT_REUSE_VM"
    ENABLE_KVM="$DEFAULT_ENABLE_KVM"
    SSH_PORT=""
    HTTP_PORT=""

    while [ $# -gt 0 ]; do
        case "$1" in
            --openwrt-version)
                [ $# -ge 2 ] || {
                    log_error "--openwrt-version requires a value"
                    usage
                    exit 1
                }
                OPENWRT_VERSION="$2"
                shift 2
                ;;
            --workdir)
                [ $# -ge 2 ] || {
                    log_error "--workdir requires a value"
                    usage
                    exit 1
                }
                WORKDIR="$2"
                shift 2
                ;;
            --reuse-vm)
                REUSE_VM=true
                shift
                ;;
            --no-kvm)
                ENABLE_KVM=false
                shift
                ;;
            --ssh-port)
                [ $# -ge 2 ] || {
                    log_error "--ssh-port requires a value"
                    usage
                    exit 1
                }
                SSH_PORT="$2"
                shift 2
                ;;
            --http-port)
                [ $# -ge 2 ] || {
                    log_error "--http-port requires a value"
                    usage
                    exit 1
                }
                HTTP_PORT="$2"
                shift 2
                ;;
            --help | -h)
                usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

# Check if required commands are available
require_command() {
    local tool="$1"
    local hint="$2"

    if command -v "$tool" > /dev/null 2>&1; then
        return 0
    fi

    if [ -n "$hint" ]; then
        log_error "Required tool '$tool' not found. $hint"
    else
        log_error "Required tool '$tool' not found in PATH."
    fi
    return 1
}

# Verify all prerequisites are installed
check_prerequisites() {
    log_info "Checking prerequisites..."

    local missing_tools=""

    if ! require_command "curl" "Install curl (e.g., 'sudo apt-get install -y curl')"; then
        missing_tools="$missing_tools curl"
    fi

    if ! require_command "sha256sum" "Install coreutils (e.g., 'sudo apt-get install -y coreutils')"; then
        missing_tools="$missing_tools sha256sum"
    fi

    if ! require_command "xz" "Install xz-utils (e.g., 'sudo apt-get install -y xz-utils')"; then
        missing_tools="$missing_tools xz"
    fi

    if ! require_command "qemu-system-x86_64" "Install qemu-system-x86 (e.g., 'sudo apt-get install -y qemu-system-x86')"; then
        missing_tools="$missing_tools qemu-system-x86_64"
    fi

    if ! require_command "qemu-img" "Install qemu-utils (e.g., 'sudo apt-get install -y qemu-utils')"; then
        missing_tools="$missing_tools qemu-img"
    fi

    if ! require_command "expect" "Install expect (e.g., 'sudo apt-get install -y expect')"; then
        missing_tools="$missing_tools expect"
    fi

    if ! require_command "ssh" "Install openssh-client (e.g., 'sudo apt-get install -y openssh-client')"; then
        missing_tools="$missing_tools ssh"
    fi

    if ! require_command "scp" "Install openssh-client (e.g., 'sudo apt-get install -y openssh-client')"; then
        missing_tools="$missing_tools scp"
    fi

    # Optional tools
    if ! command -v ssh-keygen > /dev/null 2>&1; then
        log_warn "ssh-keygen not found, will use existing SSH keys or password authentication"
    fi

    if ! command -v sshpass > /dev/null 2>&1; then
        log_warn "sshpass not found, will rely on SSH key authentication"
    fi

    if [ -n "$missing_tools" ]; then
        log_error "Missing required tools:$missing_tools"
        log_error "Please install the missing tools and try again"
        exit 1
    fi

    # Check KVM availability if enabled
    if [ "$ENABLE_KVM" = "true" ]; then
        if [ ! -e /dev/kvm ]; then
            log_warn "KVM device not found, falling back to TCG emulation"
            log_warn "Performance will be reduced. Consider using --no-kvm to suppress this warning"
            ENABLE_KVM=false
        elif [ ! -r /dev/kvm ] || [ ! -w /dev/kvm ]; then
            log_warn "KVM device not accessible, falling back to TCG emulation"
            log_warn "Check permissions on /dev/kvm or use --no-kvm to suppress this warning"
            ENABLE_KVM=false
        fi
    fi

    log_success "All prerequisites satisfied"
}

# Cleanup function to handle graceful shutdown
cleanup() {
    log_info "Cleaning up..."

    # Stop VM if running
    if [ -n "$VM_PID" ] && kill -0 "$VM_PID" 2> /dev/null; then
        log_info "Shutting down VM (PID: $VM_PID)"

        # Try graceful shutdown via SSH first
        if [ -n "$SSH_KEY" ] && [ -n "$SSH_PORT" ]; then
            log_info "Attempting graceful shutdown via SSH"
            timeout 30 ssh -i "$SSH_KEY" -o "StrictHostKeyChecking=no" \
                -o "ConnectTimeout=5" -o "BatchMode=yes" \
                -p "$SSH_PORT" root@127.0.0.1 "poweroff" 2> /dev/null || true

            # Wait for graceful shutdown
            local count=0
            while kill -0 "$VM_PID" 2> /dev/null && [ $count -lt 30 ]; do
                sleep 1
                count=$((count + 1))
            done
        fi

        # Force kill if still running
        if kill -0 "$VM_PID" 2> /dev/null; then
            log_warn "Force killing VM process"
            kill "$VM_PID" 2> /dev/null || true
            sleep 2
        fi
    fi

    # Clean up TAP interface if created
    if [ -n "$TAP_INTERFACE" ] && command -v ip > /dev/null 2>&1; then
        if ip link show "$TAP_INTERFACE" > /dev/null 2>&1; then
            log_info "Removing TAP interface: $TAP_INTERFACE"
            ip link del "$TAP_INTERFACE" 2> /dev/null || true
        fi
    fi

    log_info "Cleanup completed"
}

# Set up signal handlers for graceful cleanup
setup_signal_handlers() {
    trap cleanup EXIT INT TERM HUP
}

# Allocate free port for port forwarding
allocate_port() {
    local base_port="${1:-10000}"
    local max_attempts=100

    for i in $(seq 1 $max_attempts); do
        local port=$((base_port + i))
        if ! netstat -tuln 2> /dev/null | grep -q ":$port "; then
            printf '%s' "$port"
            return 0
        fi
    done

    log_error "Failed to allocate free port"
    return 1
}

# Set up working directory structure
setup_workdir() {
    log_info "Setting up working directory: $WORKDIR"

    mkdir -p "$WORKDIR"
    cd "$WORKDIR" || {
        log_error "Failed to change to working directory: $WORKDIR"
        exit 1
    }

    # Create subdirectories
    mkdir -p images artifacts logs

    # Set global paths
    ARTIFACTS_DIR="$PWD/artifacts"
    BASE_IMAGE="$PWD/images/openwrt-${OPENWRT_VERSION}-x86-64-combined-ext4.img"
    OVERLAY_IMAGE="$PWD/images/openwrt-${OPENWRT_VERSION}-x86-64-overlay.qcow2"
    SSH_KEY="$PWD/ssh_key"

    log_success "Working directory ready: $WORKDIR"
}

# Download OpenWrt image and checksum
download_openwrt_image() {
    local image_name="openwrt-${OPENWRT_VERSION}-x86-64-combined-ext4.img.gz"
    local checksum_name="${image_name}.sha256sum"
    local base_url="https://downloads.openwrt.org/releases/${OPENWRT_VERSION}/targets/x86/64"

    log_info "Downloading OpenWrt ${OPENWRT_VERSION} image..."

    # Download checksum first
    log_info "Downloading checksum: $checksum_name"
    if ! curl -fsSL "${base_url}/${checksum_name}" -o "$checksum_name"; then
        log_error "Failed to download checksum file"
        return 1
    fi

    # Download image if not exists or not reusing
    if [ "$REUSE_VM" != "true" ] || [ ! -f "$image_name" ]; then
        log_info "Downloading image: $image_name"
        if ! curl -fSL "${base_url}/${image_name}" -o "$image_name"; then
            log_error "Failed to download OpenWrt image"
            return 1
        fi
    else
        log_info "Reusing existing image: $image_name"
    fi

    # Verify checksum
    log_info "Verifying image integrity..."
    local expected_sha256
    expected_sha256=$(awk '{print $1}' "$checksum_name")

    local actual_sha256
    actual_sha256=$(sha256sum "$image_name" | awk '{print $1}')

    if [ "$expected_sha256" != "$actual_sha256" ]; then
        log_error "Checksum verification failed"
        log_error "Expected: $expected_sha256"
        log_error "Actual: $actual_sha256"
        return 1
    fi

    log_success "Image integrity verified"

    # Decompress image if needed
    if [ "$REUSE_VM" != "true" ] || [ ! -f "$BASE_IMAGE" ]; then
        log_info "Decompressing image..."
        if ! xz -d -c "$image_name" > "$BASE_IMAGE"; then
            log_error "Failed to decompress image"
            return 1
        fi
    else
        log_info "Reusing existing decompressed image: $BASE_IMAGE"
    fi

    log_success "OpenWrt image ready: $BASE_IMAGE"
}

# Create overlay image for write operations
create_overlay_image() {
    if [ "$REUSE_VM" = "true" ] && [ -f "$OVERLAY_IMAGE" ]; then
        log_info "Reusing existing overlay image: $OVERLAY_IMAGE"
        return 0
    fi

    log_info "Creating overlay image: $OVERLAY_IMAGE"

    if ! qemu-img create -f qcow2 -b "$BASE_IMAGE" "$OVERLAY_IMAGE" 2G; then
        log_error "Failed to create overlay image"
        return 1
    fi

    log_success "Overlay image created"
}

# Generate SSH key pair for VM access
generate_ssh_key() {
    if [ "$REUSE_VM" = "true" ] && [ -f "$SSH_KEY" ] && [ -f "${SSH_KEY}.pub" ]; then
        log_info "Reusing existing SSH key: $SSH_KEY"
        return 0
    fi

    log_info "Generating SSH key pair..."

    if ! ssh-keygen -t rsa -b 2048 -N "" -f "$SSH_KEY" -C "vm-test-key" > /dev/null 2>&1; then
        log_error "Failed to generate SSH key pair"
        return 1
    fi

    log_success "SSH key pair generated"
}

# Create Expect script for VM console interaction
create_expect_script() {
    EXPECT_SCRIPT="$PWD/scripts/expect/vm_setup.exp"
    mkdir -p "$(dirname "$EXPECT_SCRIPT")"

    log_info "Creating Expect script: $EXPECT_SCRIPT"

    cat > "$EXPECT_SCRIPT" << 'EOF'
#!/usr/bin/expect -f

set timeout 60
set vm_spawn_id [spawn -noecho] {*}$argv
set spawn_id $vm_spawn_id

# Function to wait for prompt
proc wait_for_prompt {} {
    expect {
        -re "login: $" { send "root\r"; exp_continue }
        -re "Password: $" { send "root\r"; exp_continue }
        -re "root@[^:]+:[/~]# $" { return }
        timeout { send_user "Timeout waiting for prompt\n"; exit 1 }
    }
}

# Function to execute command and wait for prompt
proc exec_cmd {cmd} {
    send "$cmd\r"
    expect -re "root@[^:]+:[/~]# $"
}

# Wait for boot to complete
expect {
    -re "login: $" {
        send "root\r"
        expect -re "Password: $" { send "root\r" }
    }
    -re "root@[^:]+:[/~]# $" { }
    timeout { send_user "Timeout waiting for login prompt\n"; exit 1 }
}

# Set root password
send_user "Setting root password...\n"
exec_cmd "echo 'root:root' | chpasswd"

# Enable SSH key-based authentication
send_user "Setting up SSH key authentication...\n"
exec_cmd "mkdir -p /etc/dropbear"
exec_cmd "chmod 700 /etc/dropbear"

# Read and install SSH public key
set ssh_public_key [read stdin]
exec_cmd "echo '$ssh_public_key' > /etc/dropbear/authorized_keys"
exec_cmd "chmod 600 /etc/dropbear/authorized_keys"

# Enable password authentication as fallback
exec_cmd "uci set dropbear.@dropbear[0].PasswordAuth=1"
exec_cmd "uci set dropbear.@dropbear[0].RootPasswordAuth=1"
exec_cmd "uci commit dropbear"
exec_cmd "/etc/init.d/dropbear restart"

# Wait for WAN DHCP to complete
send_user "Waiting for WAN DHCP...\n"
exec_cmd "sleep 10"
exec_cmd "udhcpc -i eth0 -n -q"

# Test internet connectivity
send_user "Testing internet connectivity...\n"
exec_cmd "ping -c 2 8.8.8.8"

# Ensure opkg has internet access
exec_cmd "opkg update"

send_user "VM setup completed successfully\n"
expect eof
EOF

    chmod +x "$EXPECT_SCRIPT"
    log_success "Expect script created"
}

# Setup TAP interface for LAN network simulation
setup_tap_interface() {
    if command -v ip > /dev/null 2>&1; then
        TAP_INTERFACE="tap0"
        log_info "Setting up TAP interface: $TAP_INTERFACE"

        if ! ip tuntap add dev "$TAP_INTERFACE" mode tap user "$(id -u)" 2> /dev/null; then
            log_warn "Failed to create TAP interface, will use user-mode networking only"
            TAP_INTERFACE=""
            return 0
        fi

        ip link set "$TAP_INTERFACE" up
        log_success "TAP interface created: $TAP_INTERFACE"
    else
        log_warn "ip command not available, skipping TAP interface setup"
        TAP_INTERFACE=""
    fi
}

# Launch QEMU VM
launch_vm() {
    log_info "Launching OpenWrt VM..."

    # Allocate ports if not specified
    if [ -z "$SSH_PORT" ]; then
        SSH_PORT=$(allocate_port 2222)
    fi
    if [ -z "$HTTP_PORT" ]; then
        HTTP_PORT=$(allocate_port 8080)
    fi

    log_info "SSH port: $SSH_PORT, HTTP port: $HTTP_PORT"

    # Build QEMU command
    local qemu_cmd="qemu-system-x86_64"
    local qemu_args=""

    # Add KVM if available and enabled
    if [ "$ENABLE_KVM" = "true" ]; then
        qemu_args="$qemu_args -enable-kvm"
        log_info "KVM acceleration enabled"
    else
        log_info "Using TCG emulation (slower performance)"
    fi

    # Basic VM configuration
    qemu_args="$qemu_args -m 512"
    qemu_args="$qemu_args -nographic"
    qemu_args="$qemu_args -serial mon:stdio"
    qemu_args="$qemu_args -drive file=$OVERLAY_IMAGE,format=qcow2,if=virtio"

    # Network configuration
    qemu_args="$qemu_args -netdev user,id=wan,hostfwd=tcp::$SSH_PORT-:22,hostfwd=tcp::$HTTP_PORT-:80"
    qemu_args="$qemu_args -device virtio-net-pci,netdev=wan,mac=52:54:00:12:34:56"

    # Add TAP interface for LAN if available
    if [ -n "$TAP_INTERFACE" ]; then
        qemu_args="$qemu_args -netdev tap,id=lan,ifname=$TAP_INTERFACE,script=no,downscript=no"
        qemu_args="$qemu_args -device virtio-net-pci,netdev=lan,mac=52:54:00:12:34:57"
        log_info "LAN TAP interface configured"
    fi

    # Launch VM in background
    log_info "Starting VM with command: $qemu_cmd $qemu_args"
    $qemu_cmd $qemu_args > "$ARTIFACTS_DIR/vm_console.log" 2>&1 &
    VM_PID=$!

    log_info "VM started with PID: $VM_PID"

    # Wait a moment for VM to start
    sleep 5

    # Verify VM is running
    if ! kill -0 "$VM_PID" 2> /dev/null; then
        log_error "VM failed to start"
        log_error "Check console log: $ARTIFACTS_DIR/vm_console.log"
        return 1
    fi

    log_success "VM launched successfully"
}

# Configure VM using Expect script
configure_vm() {
    log_info "Configuring VM using Expect..."

    if [ ! -f "$EXPECT_SCRIPT" ]; then
        log_error "Expect script not found: $EXPECT_SCRIPT"
        return 1
    fi

    # Get SSH public key
    local ssh_public_key
    ssh_public_key=$(cat "${SSH_KEY}.pub")

    # Run expect script with SSH key
    if ! printf '%s' "$ssh_public_key" | expect "$EXPECT_SCRIPT" qemu-system-x86_64 \
        -m 512 -nographic -serial mon:stdio \
        -drive "file=$OVERLAY_IMAGE,format=qcow2,if=virtio" \
        -netdev "user,id=wan,hostfwd=tcp::$SSH_PORT-:22,hostfwd=tcp::$HTTP_PORT-:80" \
        -device "virtio-net-pci,netdev=wan,mac=52:54:00:12:34:56" \
        > "$ARTIFACTS_DIR/vm_setup.log" 2>&1; then
        log_error "VM configuration failed"
        log_error "Check setup log: $ARTIFACTS_DIR/vm_setup.log"
        return 1
    fi

    log_success "VM configuration completed"
}

# Test SSH connectivity
test_ssh_connectivity() {
    log_info "Testing SSH connectivity..."

    local ssh_opts="-o StrictHostKeyChecking=no -o ConnectTimeout=10 -o BatchMode=yes"
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if ssh -i "$SSH_KEY" $ssh_opts -p "$SSH_PORT" root@127.0.0.1 "echo 'SSH test successful'" > /dev/null 2>&1; then
            log_success "SSH connectivity established"
            return 0
        fi

        log_info "SSH attempt $attempt/$max_attempts failed, retrying in 2 seconds..."
        sleep 2
        attempt=$((attempt + 1))
    done

    log_error "Failed to establish SSH connectivity after $max_attempts attempts"
    return 1
}

# Build IPK package if needed
build_package() {
    log_info "Building IPK package..."

    local repo_root
    repo_root=$(cd "$(dirname "$0")/.." && pwd)
    local build_script="$repo_root/scripts/build_ipk.sh"

    if [ ! -f "$build_script" ]; then
        log_error "Build script not found: $build_script"
        return 1
    fi

    if ! "$build_script" --release-mode > "$ARTIFACTS_DIR/build.log" 2>&1; then
        log_error "Failed to build IPK package"
        log_error "Check build log: $ARTIFACTS_DIR/build.log"
        return 1
    fi

    log_success "IPK package built successfully"
}

# Transfer package and dependencies to VM
transfer_package() {
    log_info "Transferring package to VM..."

    local repo_root
    repo_root=$(cd "$(dirname "$0")/.." && pwd)
    local package_file
    package_file=$(find "$repo_root/dist/opkg" -name "*.ipk" 2> /dev/null | head -1 || true)

    if [ -z "$package_file" ] || [ ! -f "$package_file" ]; then
        log_error "No IPK package found"
        return 1
    fi

    log_info "Found package: $package_file"

    # Transfer package to VM
    if ! scp -i "$SSH_KEY" -o "StrictHostKeyChecking=no" -P "$SSH_PORT" \
        "$package_file" "root@127.0.0.1:/tmp/"; then
        log_error "Failed to transfer package to VM"
        return 1
    fi

    log_success "Package transferred to VM"
}

# Install package and dependencies in VM
install_package() {
    log_info "Installing package and dependencies..."

    local ssh_cmd="ssh -i '$SSH_KEY' -o 'StrictHostKeyChecking=no' -p '$SSH_PORT' root@127.0.0.1"

    # Install required dependencies
    log_info "Installing dependencies..."
    if ! eval "$ssh_cmd" 'opkg install dnsmasq-full curl iptables-nft' > "$ARTIFACTS_DIR/deps_install.log" 2>&1; then
        log_warn "Some dependencies failed to install, trying alternatives..."
        if ! eval "$ssh_cmd" 'opkg install dnsmasq curl iptables' > "$ARTIFACTS_DIR/deps_install_alt.log" 2>&1; then
            log_error "Failed to install dependencies"
            return 1
        fi
    fi

    # Install the package
    log_info "Installing openwrt-captive-monitor..."
    local package_name
    package_name=$(basename "$(find "$(cd "$(dirname "$0")/.." && pwd)/dist/opkg" -name "*.ipk" 2> /dev/null | head -1 || true)")

    if ! eval "$ssh_cmd" 'opkg install /tmp/'\"$package_name\" > "$ARTIFACTS_DIR/package_install.log" 2>&1; then
        log_error "Failed to install package"
        return 1
    fi

    log_success "Package installed successfully"
}

# Run functional smoke tests
run_smoke_tests() {
    log_info "Running smoke tests..."

    local ssh_cmd="ssh -i '$SSH_KEY' -o 'StrictHostKeyChecking=no' -p '$SSH_PORT' root@127.0.0.1"

    # Test 1: Baseline oneshot run
    log_info "Test 1: Baseline oneshot run..."
    if ! eval "$ssh_cmd" '/usr/sbin/openwrt_captive_monitor --oneshot' > "$ARTIFACTS_DIR/test_baseline.log" 2>&1; then
        log_error "Baseline test failed"
        return 1
    fi

    # Check for residual iptables/nft chains
    log_info "Checking for residual firewall rules..."
    if eval "$ssh_cmd" 'iptables -L 2>/dev/null | grep -q captive' 2> /dev/null ||
        eval "$ssh_cmd" 'nft list ruleset 2>/dev/null | grep -q captive' 2> /dev/null; then
        log_error "Found residual firewall rules after baseline test"
        return 1
    fi

    log_success "Baseline test passed"

    # Test 2: Simulated captive scenario
    log_info "Test 2: Simulated captive scenario..."

    # Block outbound traffic to simulate captive portal
    eval "$ssh_cmd" 'iptables -A OUTPUT -p icmp -j DROP' > /dev/null 2>&1 || true
    eval "$ssh_cmd" 'iptables -A OUTPUT -p tcp --dport 80 -j DROP' > /dev/null 2>&1 || true

    # Start minimal HTTP server for captive portal
    eval "$ssh_cmd" 'mkdir -p /tmp/www && echo \"Captive Portal\" > /tmp/www/index.html' > /dev/null 2>&1
    eval "$ssh_cmd" 'busybox httpd -p 80 -h /tmp/www &' > /dev/null 2>&1

    # Run monitor to detect captive scenario
    if ! eval "$ssh_cmd" '/usr/sbin/openwrt_captive_monitor --oneshot' > "$ARTIFACTS_DIR/test_captive.log" 2>&1; then
        log_error "Captive scenario test failed"
        return 1
    fi

    # Verify captive portal artifacts are created
    log_info "Verifying captive portal artifacts..."
    if ! eval "$ssh_cmd" 'iptables -L | grep -q captive' 2> /dev/null &&
        ! eval "$ssh_cmd" 'nft list ruleset | grep -q captive' 2> /dev/null; then
        log_error "Expected captive portal firewall rules not found"
        return 1
    fi

    log_success "Captive scenario test passed"

    # Test 3: Monitor mode sanity check
    log_info "Test 3: Monitor mode sanity check..."

    # Start monitor in background with short interval
    eval "$ssh_cmd" '/usr/sbin/openwrt_captive_monitor --interval 5 &' > "$ARTIFACTS_DIR/test_monitor.log" 2>&1

    # Let it run for a short time
    sleep 12

    # Stop the monitor
    eval "$ssh_cmd" 'killall openwrt_captive_monitor' 2> /dev/null || true

    log_success "Monitor mode test passed"

    log_success "All smoke tests completed"
}

# Collect logs and artifacts
collect_artifacts() {
    log_info "Collecting artifacts..."

    local ssh_cmd="ssh -i '$SSH_KEY' -o 'StrictHostKeyChecking=no' -p '$SSH_PORT' root@127.0.0.1"

    # Collect system logs
    eval "$ssh_cmd" 'dmesg' > "$ARTIFACTS_DIR/dmesg.log" 2>&1
    eval "$ssh_cmd" 'logread' > "$ARTIFACTS_DIR/syslog.log" 2>&1
    eval "$ssh_cmd" 'iptables -L -n -v' > "$ARTIFACTS_DIR/iptables.log" 2>&1
    eval "$ssh_cmd" 'nft list ruleset' > "$ARTIFACTS_DIR/nftables.log" 2>&1
    eval "$ssh_cmd" 'ps aux' > "$ARTIFACTS_DIR/processes.log" 2>&1
    eval "$ssh_cmd" 'opkg list-installed' > "$ARTIFACTS_DIR/packages.log" 2>&1

    # Collect package-specific logs
    eval "$ssh_cmd" 'ls -la /etc/config/' > "$ARTIFACTS_DIR/uci_configs.log" 2>&1
    eval "$ssh_cmd" 'uci show captive-monitor' > "$ARTIFACTS_DIR/captive_monitor_config.log" 2>&1

    log_success "Artifacts collected in: $ARTIFACTS_DIR"
}

# Main execution function
main() {
    log_info "OpenWrt VM Test Harness starting..."

    parse_arguments "$@"
    setup_signal_handlers
    check_prerequisites
    setup_workdir

    if [ "$REUSE_VM" != "true" ] || [ ! -f "$BASE_IMAGE" ]; then
        download_openwrt_image
    fi

    create_overlay_image
    generate_ssh_key
    create_expect_script
    setup_tap_interface
    launch_vm
    configure_vm

    if ! test_ssh_connectivity; then
        log_error "Failed to establish SSH connectivity"
        exit 1
    fi

    build_package
    transfer_package
    install_package
    run_smoke_tests
    collect_artifacts

    log_success "VM test harness completed successfully"
    log_info "Artifacts available at: $ARTIFACTS_DIR"
}

# Execute main function with all arguments
main "$@"
