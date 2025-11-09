# OpenWrt VM Test Harness Guide

## Overview

The OpenWrt VM Test Harness provides automated end-to-end testing of the openwrt-captive-monitor package in a virtualized environment. This guide explains how to use the VM harness for development, testing, and continuous integration.

## Prerequisites

### Required Tools

The VM harness requires the following tools to be installed:

- **curl** - For downloading OpenWrt images
- **sha256sum** - For verifying image integrity
- **xz** - For decompressing OpenWrt images
- **qemu-system-x86_64** - For running the virtual machine
- **qemu-img** - For managing disk images
- **expect** - For automated console interaction
- **ssh** - For secure VM access
- **scp** - For file transfer to/from VM

### Installation (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install -y curl xz-utils qemu-system-x86 qemu-utils expect openssh-client
```

### Optional Tools

- **ssh-keygen** - For generating SSH key pairs (usually included with openssh-client)
- **sshpass** - For password-based SSH authentication fallback
- **netstat** - For port allocation checks

### KVM Acceleration (Optional)

For better performance, KVM acceleration is recommended:

```bash
# Check if KVM is available
lsmod | grep kvm

# Add user to kvm group (if needed)
sudo usermod -a -G kvm $USER
# Log out and back in for changes to take effect
```

## Quick Start

### Basic Usage

Run the VM harness with default settings:

```bash
./scripts/run_openwrt_vm.sh
```

This will:
1. Download OpenWrt 24.02 x86-64 image
2. Create a VM with network access
3. Build and install the openwrt-captive-monitor package
4. Run automated smoke tests
5. Collect logs and artifacts in `dist/vm-tests/artifacts/`

### Custom Configuration

Specify OpenWrt version and working directory:

```bash
./scripts/run_openwrt_vm.sh --openwrt-version 23.05 --workdir /tmp/openwrt-test
```

### CI/CD Usage

For CI environments without KVM support:

```bash
./scripts/run_openwrt_vm.sh --reuse-vm --no-kvm
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--openwrt-version VERSION` | OpenWrt version to download | `24.02` |
| `--workdir DIRECTORY` | Working directory for VM artifacts | `dist/vm-tests` |
| `--reuse-vm` | Reuse existing VM artifacts if available | `false` |
| `--no-kvm` | Disable KVM acceleration (use TCG emulation) | `false` |
| `--ssh-port PORT` | Host port for SSH forwarding | auto-allocate |
| `--http-port PORT` | Host port for HTTP forwarding | auto-allocate |
| `--help, -h` | Show help message | - |

## VM Architecture

The VM harness creates a virtualized OpenWrt environment with the following configuration:

### Network Topology

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Host          │    │   VM (OpenWrt)  │    │   Internet      │
│                 │    │                 │    │                 │
│ SSH: 127.0.0.1:│◄──►│ eth0 (WAN)      │◄──►│                 │
│ 2222 → 22       │    │  DHCP, NAT      │    │                 │
│                 │    │                 │    │                 │
│ HTTP: 127.0.0.1:│◄──►│ eth1 (LAN)      │    │                 │
│ 8080 → 80       │    │  Isolated       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Virtual Machine Configuration

- **Memory**: 512MB RAM
- **Storage**: 2GB overlay image (base image remains pristine)
- **CPU**: QEMU x86-64 with optional KVM acceleration
- **Network**: Two virtio NICs (WAN via user-mode networking, LAN via TAP)
- **Console**: Serial console for Expect automation

## Test Scenarios

The VM harness executes three main test scenarios:

### 1. Baseline Test

Verifies normal operation with internet connectivity:

```bash
/usr/sbin/openwrt_captive_monitor --oneshot
```

**Expected Results:**
- Exit status 0
- No residual firewall rules
- Clean system state

### 2. Captive Portal Simulation

Simulates a captive portal environment:

1. Block outbound traffic (ICMP/HTTP)
2. Start minimal HTTP server on LAN
3. Run monitor in captive detection mode
4. Verify firewall rules are created
5. Confirm cleanup after recovery

**Verification Points:**
- iptables/nftables chains created
- DNS hijacking rules active
- HTTP redirection functional
- Proper cleanup on recovery

### 3. Monitor Mode Test

Tests continuous monitoring with shortened interval:

```bash
/usr/sbin/openwrt_captive_monitor --interval 5 &
```

**Verification Points:**
- Monitor starts successfully
- Runs for specified duration
- Terminates cleanly

## Artifacts and Logs

The VM harness produces comprehensive logs and artifacts in the working directory:

### Directory Structure

```
dist/vm-tests/
├── images/                  # OpenWrt images
│   ├── openwrt-24.02-x86-64-combined-ext4.img
│   └── openwrt-24.02-x86-64-overlay.qcow2
├── artifacts/               # Test results and logs
│   ├── vm_console.log       # VM boot/console output
│   ├── vm_setup.log         # Expect script execution
│   ├── build.log            # Package build output
│   ├── deps_install.log     # Dependency installation
│   ├── package_install.log  # Package installation
│   ├── test_baseline.log    # Baseline test results
│   ├── test_captive.log     # Captive portal test
│   ├── test_monitor.log     # Monitor mode test
│   ├── dmesg.log            # Kernel messages
│   ├── syslog.log           # System logs
│   ├── iptables.log         # Firewall rules
│   ├── nftables.log         # nftables ruleset
│   ├── processes.log        # Running processes
│   ├── packages.log         # Installed packages
│   ├── uci_configs.log      # UCI configuration files
│   └── captive_monitor_config.log
├── logs/                    # Additional logs
└── ssh_key                  # SSH private key for VM access
```

### Key Log Files

- **vm_console.log**: Complete VM boot sequence and kernel messages
- **test_*.log**: Individual test execution results
- **iptables.log/nftables.log**: Firewall state for verification
- **captive_monitor_config.log**: Package configuration state

## Troubleshooting

### Common Issues

#### VM Fails to Start

**Symptoms**: VM process exits immediately, console shows errors

**Solutions**:
1. Check QEMU installation: `qemu-system-x86_64 --version`
2. Verify image integrity: `sha256sum images/*.img`
3. Check KVM availability: `ls -la /dev/kvm`
4. Try without KVM: `--no-kvm`

#### SSH Connection Fails

**Symptoms**: Timeout during SSH connectivity test

**Solutions**:
1. Check VM console: `cat artifacts/vm_console.log`
2. Verify SSH service: Look for dropbear startup messages
3. Check port allocation: Ensure SSH port is not in use
4. Manual SSH test: `ssh -i ssh_key -p 2222 root@127.0.0.1`

#### Package Installation Fails

**Symptoms**: opkg install errors during dependency resolution

**Solutions**:
1. Check internet connectivity: `ping 8.8.8.8` from VM
2. Update package lists: `opkg update`
3. Verify package architecture: Check build target matches VM
4. Check disk space: `df -h` in VM

#### Test Failures

**Symptoms**: Smoke tests return non-zero exit status

**Solutions**:
1. Review specific test logs in artifacts/
2. Check package installation: `opkg list-installed | grep captive`
3. Verify service status: `/etc/init.d/captive-monitor status`
4. Manual testing: Run commands directly in VM

### Debug Mode

For detailed debugging, modify the script to enable verbose logging:

```bash
# Add to script or export before running
export DEBUG=1
./scripts/run_openwrt_vm.sh
```

### Manual VM Access

Connect to the VM manually for debugging:

```bash
# SSH access
ssh -i dist/vm-tests/ssh_key -p 2222 root@127.0.0.1

# View console in real-time
tail -f dist/vm-tests/artifacts/vm_console.log
```

## Performance Considerations

### KVM vs TCG

- **KVM**: Near-native performance, requires hardware virtualization
- **TCG**: Software emulation, slower but works in all environments

### Resource Usage

- **Memory**: 512MB minimum, 1GB recommended for development
- **Disk**: 2GB overlay image, base image ~200MB
- **CPU**: Minimal load during testing, moderate during package building

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Run VM Tests
  run: |
    sudo apt-get update
    sudo apt-get install -y curl xz-utils qemu-system-x86 qemu-utils expect openssh-client
    ./scripts/run_openwrt_vm.sh --reuse-vm --no-kvm
```

### Jenkins Pipeline Example

```groovy
stage('VM Tests') {
    steps {
        sh '''
            ./scripts/run_openwrt_vm.sh \
                --openwrt-version ${OPENWRT_VERSION} \
                --workdir ${WORKSPACE}/vm-tests \
                --reuse-vm \
                --no-kvm
        '''
    }
    post {
        always {
            archiveArtifacts artifacts: 'dist/vm-tests/artifacts/**/*', fingerprint: true
        }
    }
}
```

## Advanced Usage

### Custom Network Configuration

For complex network scenarios, modify the `launch_vm()` function:

```bash
# Additional network interfaces
qemu_args="$qemu_args -netdev socket,id=lan2,listen=:1234"
qemu_args="$qemu_args -device virtio-net-pci,netdev=lan2,mac=52:54:00:12:34:58"
```

### Custom Test Scenarios

Extend the `run_smoke_tests()` function for additional tests:

```bash
custom_test() {
    log_info "Running custom test..."
    local ssh_cmd="ssh -i '$SSH_KEY' -o 'StrictHostKeyChecking=no' -p '$SSH_PORT' root@127.0.0.1"
    
    # Custom test logic here
    eval "$ssh_cmd" 'custom_command_here' > "$ARTIFACTS_DIR/test_custom.log" 2>&1
    
    log_success "Custom test completed"
}
```

## Security Considerations

### SSH Key Management

- Generated SSH keys are stored in the working directory
- Keys are not password-protected for automation
- Ensure working directory has appropriate permissions
- Clean up working directory after use in production environments

### Network Isolation

- VM uses user-mode networking for WAN (isolated from host)
- TAP interface for LAN requires appropriate permissions
- No host port exposure except configured forwards
- Consider firewall rules for additional security

## Contributing

When contributing to the VM harness:

1. Follow existing shell scripting conventions
2. Test with both KVM and TCG modes
3. Update documentation for new features
4. Ensure backward compatibility with existing tests
5. Run shellcheck and shfmt before submitting

## Support

For issues or questions:

1. Check existing documentation and troubleshooting guides
2. Review log files in the artifacts directory
3. Test with minimal configuration to isolate issues
4. Report issues with detailed logs and environment information
