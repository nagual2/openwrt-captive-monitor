# Virtualization Testing

This directory contains documentation and wrappers for VM-based testing of the openwrt-captive-monitor package.

## Quick Start

The VM test harness provides automated end-to-end testing in a virtualized OpenWrt environment:

```bash
# From repository root
./scripts/run_openwrt_vm.sh
```

## Manual Testing

For manual testing and debugging:

```bash
# Run with custom settings
./scripts/run_openwrt_vm.sh \
    --openwrt-version 24.02 \
    --workdir /tmp/openwrt-test \
    --reuse-vm

# CI environment (no KVM acceleration)
./scripts/run_openwrt_vm.sh --reuse-vm --no-kvm
```

## Test Scenarios

The VM harness automatically executes these test scenarios:

1. **Baseline Test** - Normal operation with internet connectivity
2. **Captive Portal Simulation** - Blocked traffic with HTTP server
3. **Monitor Mode Test** - Continuous monitoring with short interval

## Artifacts

Test results and logs are collected in the working directory:

```
dist/vm-tests/artifacts/
├── vm_console.log       # VM boot and console output
├── test_*.log           # Individual test results
├── iptables.log         # Firewall rules state
├── nftables.log         # nftables ruleset
└── *.log                # Additional system logs
```

## Troubleshooting

For troubleshooting and advanced usage, see the [Virtualization Guide](../../docs/guides/virtualization.md).

## Prerequisites

Ensure the following tools are installed:

```bash
# Ubuntu/Debian
sudo apt-get install -y curl xz-utils qemu-system-x86 qemu-utils expect openssh-client

# Optional: KVM acceleration
sudo usermod -a -G kvm $USER
```

## Integration

The VM test harness is designed to integrate with CI/CD systems:

- **GitHub Actions**: Use `--reuse-vm --no-kvm` for consistent testing
- **Jenkins**: Archive `dist/vm-tests/artifacts/` for test results
- **Local Development**: Use default settings for quick iteration

## Support

For issues with the VM test harness:

1. Check the [Virtualization Guide](../../docs/guides/virtualization.md)
2. Review test artifacts for detailed error information
3. Open an issue with logs and environment details
