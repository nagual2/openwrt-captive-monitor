# Scripts Directory

This directory contains shell scripts organized by purpose and target environment.

## Directory Structure

### prod-openwrt/
Scripts for configuring and managing prod-openwrt router (Xiaomi Mi Router AX3000T).

**Configuration Scripts:**
- `setup-doh-openwrt.sh` - Setup DNS-over-HTTPS (DoH) using https-dns-proxy
- `setup-dot-openwrt.sh` - Setup DNS-over-TLS (DoT) using stubby
- `configure-ipv6-ra-mtu.sh` - Configure IPv6 RA and DHCPv6 settings
- `switch-to-tb64.sh` - Switch IPv6 traffic to tb64 tunnel
- `wifi-airtime-keeper-fixed.sh` - WiFi airtime keeper for STA mode

**Related Documentation:**
- [prod-openwrt Configuration](../docs/PROD-OPENWRT-CONFIG.md)
- [DoH/DoT Setup Guide](../docs/DOH-DOT-SETUP.md)
- [IPv6 RA MTU Configuration](../docs/IPV6-RA-MTU-CONFIGURATION.md)

### testing/
Diagnostic and testing scripts for network and DNS functionality.

**DNS Testing:**
- `test-dns-detailed.sh` - Detailed DNS latency tests via WireGuard tunnels
- `test-dns-final.sh` - Final DNS test with multiple runs
- `test-dns-simple.sh` - Simple DNS connectivity test
- `test-dns-via-tb.sh` - DNS test via TunnelBroker interfaces

**Related Documentation:**
- [DNS Latency Test Results](../docs/DNS-LATENCY-TEST-RESULTS.md)
- [TB63 Diagnostic Report](../docs/TB63-DIAGNOSTIC-REPORT.md)

### windows/
Windows PowerShell utility scripts for diagnostics and data management.

**Utilities:**
- `bulk_load.ps1` - Bulk load documents to EchoVault memory system
- `Get-DNSConfig.ps1` - DNS configuration report for Windows system

**Related Tools:**
- `tools/Load-DocsToMemory.ps1` - Generate JSON for EchoVault document loading
- `docker/daemon/manage.ps1` - Docker daemon management (in docker directory)

## Usage

### Running Shell Scripts on prod-openwrt

From Windows/WSL:
```bash
# Copy script to router
scp scripts/prod-openwrt/setup-doh-openwrt.sh root@192.168.35.1:/tmp/

# Execute on router
wsl timeout 30 ssh -i ~/.ssh/id_ed25519_openwrt -o ConnectTimeout=5 root@192.168.35.1 "sh /tmp/setup-doh-openwrt.sh"
```

Or execute directly via SSH:
```bash
wsl timeout 30 ssh -i ~/.ssh/id_ed25519_openwrt -o ConnectTimeout=5 root@192.168.35.1 < scripts/prod-openwrt/setup-doh-openwrt.sh
```

### Running Testing Scripts

From Windows/WSL:
```bash
# Copy to router
scp scripts/testing/test-dns-simple.sh root@192.168.35.1:/tmp/

# Execute
wsl timeout 30 ssh -i ~/.ssh/id_ed25519_openwrt -o ConnectTimeout=5 root@192.168.35.1 "sh /tmp/test-dns-simple.sh"
```

### Running PowerShell Scripts on Windows

From PowerShell:
```powershell
# DNS configuration report
.\scripts\windows\Get-DNSConfig.ps1

# Bulk load documents to EchoVault
.\scripts\windows\bulk_load.ps1
```

## Script Naming Convention

**Shell Scripts (.sh):**
- `setup-*.sh` - Initial setup and configuration scripts
- `configure-*.sh` - Configuration change scripts
- `test-*.sh` - Testing and diagnostic scripts
- `switch-*.sh` - Scripts that switch between configurations
- `*-fixed.sh` - Fixed/corrected versions of scripts

**PowerShell Scripts (.ps1):**
- `Get-*.ps1` - Scripts that retrieve and display information
- `*_load.ps1` - Scripts for loading/importing data
- `manage.ps1` - Management and control scripts

## Notes

- All shell scripts should be executable: `chmod +x script.sh`
- Shell scripts use `#!/bin/sh` for POSIX compatibility or `#!/bin/bash` for bash-specific features
- PowerShell scripts use `.ps1` extension and run on Windows
- Always test scripts in a safe environment before production use
- Create backups before running configuration scripts
- Check script documentation and comments for prerequisites

## Related Directories

- `Minisforum/Scripts/` - Scripts specific to Minisforum device (Debian/Linux Mint)
- `tools/` - Python tools and utilities
- `docker/` - Docker-related scripts and configurations

## Migration Notes

**2026-03-10:** Reorganized scripts from project root into structured directories:
- Created `scripts/prod-openwrt/` for router configuration scripts
- Created `scripts/testing/` for diagnostic scripts
- Moved 9 scripts from root to appropriate subdirectories
- Updated documentation references
