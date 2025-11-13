# Packaging and Distribution Guide

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---


This guide covers the complete workflow for building, packaging, and distributing the OpenWrt Captive Monitor package.

## Overview

The project uses OpenWrt's native packaging system with custom tooling to simplify local builds and release automation. The packaging structure follows OpenWrt conventions and supports both development and production workflows.

## Package Structure

```
package/
├── Makefile.template           # Template for new packages
└── openwrt-captive-monitor/    # Main package definition
    ├── Makefile                # OpenWrt package metadata
    └── files/                  # Package payload
        ├── etc/
        │   ├── config/
        │   ├── init.d/
        │   └── uci-defaults/
        └── usr/
            └── sbin/
```

## Local Development Builds

### Quick Build

```bash
## Build package using defaults
./scripts/build_ipk.sh

## Output: dist/opkg/all/openwrt-captive-monitor_1.0.3-1_all.ipk
```

### Custom Builds

```bash
## Override maintainer information
./scripts/build_ipk.sh \
  --maintainer "Your Name" \
  --maintainer-email "your.email@example.com"

## Use custom SPDX license identifier
./scripts/build_ipk.sh --spdx-id "MIT"

## Build for specific architecture
./scripts/build_ipk.sh --arch "mips_24kc"

## Custom output directory
./scripts/build_ipk.sh --feed-root "./my-feed"
```

### Release Mode

Release mode generates publication-ready artifacts with checksums and metadata:

```bash
./scripts/build_ipk.sh --release-mode
```

Release mode provides:
- Detailed checksum tables (MD5, SHA256)
- JSON metadata for automation
- Feed setup instructions
- Semantic version-based naming

## Package Metadata

### OpenWrt Makefile Fields

| Field | Value | Description |
|-------|-------|-------------|
| `PKG_NAME` | `openwrt-captive-monitor` | Package identifier |
| `PKG_VERSION` | `1.0.3` | Semantic version |
| `PKG_RELEASE` | `1` | Package release number |
| `PKG_LICENSE` | `MIT` | SPDX license identifier |
| `PKG_LICENSE_FILES` | `LICENSE` | License file reference |
| `PKG_MAINTAINER` | `OpenWrt Captive Monitor Team` | Maintainer contact |
| `PKG_SOURCE_URL` | GitHub repository URL | Source location |
| `PKG_SOURCE_PROTO` | `git` | Source protocol |
| `PKG_SOURCE_VERSION` | `v$(PKG_VERSION)` | Source version tag |

### Package Definition Fields

| Field | Value | Description |
|-------|-------|-------------|
| `SECTION` | `net` | Package section |
| `CATEGORY` | `Network` | OpenWrt category |
| `SUBMENU` | `Captive Portals` | Submenu classification |
| `TITLE` | Package title | Short description |
| `DEPENDS` | `+dnsmasq +curl` | Required packages |
| `URL` | GitHub repository URL | Project homepage |

## CI/CD Integration

### GitHub Actions Workflow

The project includes automated validation and packaging via GitHub Actions:

```yaml
## .github/workflows/ci.yml
- Runs linting and tests
- Builds the package with the OpenWrt SDK
- Uploads `.ipk` and feed metadata
- Attaches release assets on tag pushes
```

### Build Output

| Artifact | Description |
|----------|-------------|
| `.ipk` | Installable OpenWrt package |
| `Packages` | Feed index |
| `Packages.gz` | Compressed feed index |
| `build.log` | Verbose SDK build log |

## Release Workflow

### 1. Version Bump

Update version in `package/openwrt-captive-monitor/Makefile`:

```makefile
PKG_VERSION:=1.0.2
PKG_RELEASE:=1
```

### 2. Build Release Artifacts

```bash
## Build with release mode
./scripts/build_ipk.sh --release-mode

## This creates:
## - dist/opkg/all/openwrt-captive-monitor_1.0.2-1_all.ipk
## - dist/opkg/all/Packages
## - dist/opkg/all/Packages.gz
## - dist/opkg/all/release-metadata.json
```

### 3. Tag and Push

```bash
git tag -a v1.0.2 -m "Release v1.0.2"
git push origin v1.0.2
```

### 4. GitHub Release

1. Go to GitHub Releases page
2. Create new release from tag `v1.0.2`
3. Upload artifacts from `dist/opkg/all/`
4. Use release metadata for description

## Custom OPKG Feed

### Local Feed Setup

1. **Create feed directory structure**:
   ```bash
   mkdir -p /path/to/feed/all
   cp dist/opkg/all/* /path/to/feed/all/
   ```

2. **Configure OpenWrt device**:
   ```bash
   # Add to /etc/opkg/customfeeds.conf
   echo "src/gz captive-monitor file:///path/to/feed" >> /etc/opkg/customfeeds.conf
   
   # Update package lists
   opkg update
   
   # Install package
   opkg install openwrt-captive-monitor
   ```

### GitHub Pages Feed

1. **Create `gh-pages` branch**:
   ```bash
   git checkout --orphan gh-pages
   git reset --hard
   ```

2. **Add package files**:
   ```bash
   mkdir -p all
   cp dist/opkg/all/* all/
   git add all/
   git commit -m "Add package v1.0.2"
   git push origin gh-pages
   ```

3. **Configure devices**:
   ```bash
   echo "src/gz captive-monitor https://username.github.io/openwrt-captive-monitor" >> /etc/opkg/customfeeds.conf
   opkg update
   ```

## Automated Distribution

### Release Script Example

```bash
#!/bin/bash
## release.sh - Automated release script

set -eu

VERSION=${1:-"1.0.2"}
MAINTAINER=${2:-"OpenWrt Captive Monitor Team"}
EMAIL=${3:-"team@example.com"}

## Update version in Makefile
sed -i "s/PKG_VERSION:=.*/PKG_VERSION:=$VERSION/" package/openwrt-captive-monitor/Makefile

## Build release artifacts
./scripts/build_ipk.sh \
  --release-mode \
  --maintainer "$MAINTAINER" \
  --maintainer-email "$EMAIL"

## Create GitHub release
gh release create "v$VERSION" \
  --title "Release v$VERSION" \
  --notes "Automated release v$VERSION" \
  dist/opkg/all/*.ipk \
  dist/opkg/all/Packages* \
  dist/opkg/all/release-metadata.json
```

### CI/CD Release Automation

The GitHub Actions workflow can be extended to:

1. **Auto-create releases** when tags are pushed
2. **Upload artifacts** to GitHub Releases
3. **Update GitHub Pages** feed
4. **Notify downstream systems**

```yaml
## Example release job
- name: Create Release
  if: startsWith(github.ref, 'refs/tags/')
  uses: actions/create-release@v1
  with:
    tag_name: ${{ github.ref }}
    release_name: Release ${{ github.ref }}
    draft: false
    prerelease: false
```

## Package Signing (Optional)

For production feeds, consider package signing:

```bash
## Generate signing key
openssl genrsa -out opkg.key 2048
openssl rsa -in opkg.key -pubout > opkg.pub

## Sign packages
opkg-sign key opkg.key dist/opkg/all/*.ipk

## Update feed with signatures
opkg-make-index -s opkg.pub -p dist/opkg/all/Packages dist/opkg/all/
```

## Quality Assurance

### Package Validation

```bash
## Verify package structure
tar -tzf dist/opkg/all/openwrt-captive-monitor_*.ipk

## Check control file
ar p dist/opkg/all/openwrt-captive-monitor_*.ipk control.tar.gz | tar -Oxz ./control

## Validate dependencies
opkg info ./dist/opkg/all/openwrt-captive-monitor_*.ipk
```

### Linting

```bash
## Check OpenWrt package compliance
openwrt-package-lint package/openwrt-captive-monitor/Makefile

## Verify file permissions
find package/openwrt-captive-monitor/files -type f -exec ls -la {} \;
```

## Troubleshooting

### Common Issues

1. **Missing dependencies**: Ensure `dnsmasq` and `curl` are available
2. **Architecture mismatch**: Use correct `--arch` parameter
3. **Permission denied**: Check executable permissions in `files/`
4. **Feed not updating**: Verify `Packages.gz` integrity

### Debug Commands

```bash
## Debug package build
./scripts/build_ipk.sh --arch all 2>&1 | tee build.log

## Test feed locally
python3 -m http.server 8080 --directory dist/opkg/all/
## Then: echo "src/gz test http://localhost:8080" >> /etc/opkg/customfeeds.conf
```

## References

- [OpenWrt Package Development Guide](https://openwrt.org/docs/guide-developer/packages)
- [OPKG Package Manager](https://openwrt.org/docs/techref/opkg)
- [SPDX License List](https://spdx.org/licenses/)
- [GitHub Actions for OpenWrt](https://github.com/openwrt/packages)

---

*Last updated: 2025-10-30*
