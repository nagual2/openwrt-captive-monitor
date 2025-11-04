# Available OpenWrt Packages

## Repository Files
❌ No .ipk files found in repository

**Explanation**: `.ipk` files are intentionally excluded from version control via `.gitignore` to keep the repository clean. Packages are built on-demand via CI/CD or locally using the build script.

### Local Build Information
- **Current Version**: 1.0.1-1 (from `package/openwrt-captive-monitor/Makefile`)
- **Architecture**: all
- **Build Script**: `./scripts/build_ipk.sh`
- **Output Location**: `dist/opkg/all/openwrt-captive-monitor_1.0.1-1_all.ipk`
- **Package Size**: 13,250 bytes (local build)
- **Dependencies**: `dnsmasq`, `curl`

### How to Build Locally
```bash
## Build the package
./scripts/build_ipk.sh

## Output will be in:
## dist/opkg/all/openwrt-captive-monitor_1.0.1-1_all.ipk
## dist/opkg/all/Packages
## dist/opkg/all/Packages.gz
```

## GitHub Actions Artifacts
✅ Artifacts available

### Latest Build Information
- **Workflow**: "Build OpenWrt packages"
- **Latest Successful Run**: #18941818953 (2025-10-30T13:13:37Z)
- **Branch**: main
- **Status**: ✅ Success
- **Artifact**: `openwrt-captive-monitor_1.0.1-1_all`
- **Size**: 14,496 bytes
- **Created**: 2025-10-30T13:14:14Z
- **Expires**: 2026-01-28T13:13:38Z

### Download Instructions
1. **Via GitHub Web Interface**:
   - Go to: https://github.com/nagual2/openwrt-captive-monitor/actions
   - Click on "Build OpenWrt packages" workflow
   - Select the latest successful run (Run #18941818953)
   - Download the "openwrt-captive-monitor_1.0.1-1_all" artifact

2. **Via API** (requires authentication):
   ```bash
   curl -H "Authorization: token YOUR_TOKEN" \
        -L https://api.github.com/repos/nagual2/openwrt-captive-monitor/actions/artifacts/4417725839/zip \
        -o openwrt-captive-monitor_1.0.1-1_all.zip
   ```

### Recent Build History
| Run ID | Date | Status | Artifact Size |
|--------|------|--------|---------------|
| 18941818953 | 2025-10-30 13:13:37Z | ✅ Success | 14,496 bytes |
| 18941783175 | 2025-10-30 13:12:21Z | ✅ Success | 14,502 bytes |
| 18925153078 | 2025-10-29 23:38:58Z | ✅ Success | 14,501 bytes |

## GitHub Releases
❌ No package assets in releases

### Available Releases
- **v0.1.0** (2025-10-23T12:26:42Z)
  - ❌ No package assets attached
  - Release notes: Initial release

### Missing Release Assets
- **v0.1.2**: Tag exists but no release created
- **v0.1.0**: Release exists but no package assets

**Note**: The workflow is configured to publish release assets when tags are pushed, but it appears this hasn't been working or the assets weren't properly attached.

## Package Metadata

### Current Version (1.0.1-1)
```
Package: openwrt-captive-monitor
Version: 1.0.1-1
Architecture: all
Maintainer: Kombai AI Assistant
License: MIT
Section: net
Category: Network
Priority: optional
Depends: dnsmasq, curl
Source: https://github.com/nagual2/openwrt-captive-monitor
Installed-Size: 96
Description: Captive portal connectivity monitor and auto-redirect helper
```

### Version History
| Version | Tag Date | Build Status | Package Available |
|---------|----------|--------------|-------------------|
| 1.0.1 | Current | ✅ Available via CI artifacts | Yes |
| 0.1.2 | 2025-10-26 | ❌ CI ran but no artifacts preserved | No |
| 0.1.0 | 2025-10-23 | ❌ Release exists but no assets | No |

## Summary
- **Total .ipk files found**: 1 (current version via CI artifacts)
- **Latest version**: v1.0.1-1
- **Recommended download**: GitHub Actions artifacts (most recent)
- **Repository status**: No packages stored (intentionally)
- **Release status**: No package assets in releases

## How to Download

### Recommended Method: GitHub Actions Artifacts
1. **Latest Version (Recommended)**:
   - URL: https://github.com/nagual2/openwrt-captive-monitor/actions
   - Click "Build OpenWrt packages" workflow
   - Select latest successful run
   - Download "openwrt-captive-monitor_1.0.1-1_all" artifact

2. **Direct Download** (requires GitHub login):
   ```
   https://api.github.com/repos/nagual2/openwrt-captive-monitor/actions/artifacts/4417725839/zip
   ```

### Alternative Method: Local Build
```bash
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor
./scripts/build_ipk.sh
## Package will be in: dist/opkg/all/openwrt-captive-monitor_1.0.1-1_all.ipk
```

### Package Installation on OpenWrt
```bash
## Transfer the .ipk file to your OpenWrt device
scp openwrt-captive-monitor_1.0.1-1_all.ipk root@192.168.1.1:/tmp/

## Install the package
opkg install /tmp/openwrt-captive-monitor_1.0.1-1_all.ipk

## Configure and enable
uci set captive-monitor.@monitor[0].enabled='1'
uci commit captive-monitor
/etc/init.d/captive-monitor enable
/etc/init.d/captive-monitor start
```

## Troubleshooting

### If GitHub Actions Artifacts Expire
GitHub Actions artifacts expire after 90 days. If the download links don't work:

1. **Trigger a new build**:
   ```bash
   # Make any small change and push to main
   echo "update" > README.md
   git add README.md
   git commit -m "trigger build"
   git push origin main
   ```

2. **Build locally** using the instructions above

### If Package Installation Fails
- **Check dependencies**: Ensure `dnsmasq` and `curl` are installed
- **Check architecture**: Package is built for `all` architectures
- **Check OpenWrt version**: Compatible with modern OpenWrt releases
- **Check disk space**: Package requires ~96KB installed space

---

*Last updated: 2025-10-30*
*Report generated by checking repository files, GitHub releases, and GitHub Actions artifacts*
