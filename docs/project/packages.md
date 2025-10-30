# Package Management

Complete guide to building, distributing, and managing **openwrt-captive-monitor** packages.

## 📦 Package Overview

### Package Structure

```
openwrt-captive-monitor_X.Y.Z-N_arch.ipk
├── control              # Package metadata
├── conffiles           # Configuration files to preserve
├── data.tar.gz        # Package contents
│   ├── etc/
│   │   ├── config/
│   │   │   └── captive-monitor        # UCI configuration
│   │   └── init.d/
│   │       └── captive-monitor        # Init script
│   ├── usr/
│   │   └── sbin/
│   │       └── openwrt_captive_monitor  # Main executable
│   └── www/
│       └── captive-monitor/            # Web interface files (future)
└── debian-binary        # Package format version
```

### Package Metadata

**Control File:**
```
Package: openwrt-captive-monitor
Version: X.Y.Z-N
Depends: dnsmasq, curl, iptables, busybox
Conflicts: captive-portal-autologin
Provides: captive-portal-detector
Section: net
Priority: optional
Maintainer: OpenWrt Captive Monitor Team
License: MIT
Description: Lightweight OpenWrt captive portal detection and traffic interception
Architecture: all
Installed-Size: 12345
```

---

## 🔧 Building Packages

### Development Build

```bash
# Clone repository
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor

# Install build dependencies
sudo apt-get install -y binutils busybox gzip pigz tar xz-utils

# Build package
scripts/build_ipk.sh --arch all

# Verify package
ls -la dist/opkg/all/
```

### OpenWrt SDK Build

```bash
# Download and extract OpenWrt SDK
wget https://downloads.openwrt.org/releases/22.03.5/targets/ath79/generic/openwrt-sdk-22.03.5-ath79-generic_gcc-11.2.0_musl.Linux-x86_64.tar.xz
tar -xf openwrt-sdk-*.tar.xz
cd openwrt-sdk-*

# Add package source
git clone https://github.com/nagual2/openwrt-captive-monitor.git package/openwrt-captive-monitor

# Build package
./scripts/feeds update -a
./scripts/feeds install openwrt-captive-monitor
make package/openwrt-captive-monitor/compile V=s

# Locate built package
find bin/packages -name "*openwrt-captive-monitor*.ipk"
```

### Multi-Architecture Build

```bash
#!/bin/bash
# build-all-arch.sh - Build for all supported architectures

ARCHITECTURES=(
    "all"
    "mips_24kc"
    "mipsel_24kc"
    "aarch64_cortex-a53"
    "x86_64"
    "arm_cortex-a7"
)

for arch in "${ARCHITECTURES[@]}"; do
    echo "Building for architecture: $arch"
    scripts/build_ipk.sh --arch "$arch"
    
    if [ $? -eq 0 ]; then
        echo "✓ Build successful for $arch"
    else
        echo "✗ Build failed for $arch"
        exit 1
    fi
done

echo "All builds completed successfully!"
```

---

## 📋 Package Configuration

### Makefile Structure

```makefile
# package/openwrt-captive-monitor/Makefile

include $(TOPDIR)/rules.mk

PKG_NAME:=openwrt-captive-monitor
PKG_VERSION:=1.0.0
PKG_RELEASE:=1
PKG_LICENSE:=MIT
PKG_MAINTAINER:=OpenWrt Captive Monitor Team

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)

include $(INCLUDE_DIR)/package.mk

define Package/openwrt-captive-monitor
  SECTION:=net
  CATEGORY:=Network
  TITLE:=OpenWrt Captive Portal Monitor
  URL:=https://github.com/nagual2/openwrt-captive-monitor
  DEPENDS:=+dnsmasq +curl +iptables +busybox
  PKGARCH:=all
endef

define Package/openwrt-captive-monitor/description
  A lightweight OpenWrt helper that monitors WAN connectivity,
  detects captive portals, and temporarily intercepts LAN
  DNS/HTTP traffic to facilitate client authentication.
endef

define Package/openwrt-captive-monitor/conffiles
/etc/config/captive-monitor
endef

define Build/Prepare
	mkdir -p $(PKG_BUILD_DIR)
	$(CP) ./src/* $(PKG_BUILD_DIR)/
endef

define Package/openwrt-captive-monitor/install
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_CONF) $(PKG_BUILD_DIR)/captive-monitor.conf $(1)/etc/config/captive-monitor
	
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/captive-monitor.init $(1)/etc/init.d/captive-monitor
	
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/openwrt_captive_monitor $(1)/usr/sbin/
endef

$(eval $(call BuildPackage,openwrt-captive-monitor))
```

### Configuration Files

**UCI Configuration (`etc/config/captive-monitor`):**
```
config captive_monitor 'config'
    option enabled '0'
    option mode 'monitor'
    option wifi_interface 'phy1-sta0'
    option wifi_logical 'wwan'
    option monitor_interval '60'
    option ping_servers '1.1.1.1 8.8.8.8 9.9.9.9'
    option captive_check_urls 'http://connectivitycheck.gstatic.com/generate_204 http://detectportal.firefox.com/success.txt'
    option enable_syslog '1'
```

**Init Script (`etc/init.d/captive-monitor`):**
```bash
#!/bin/sh /etc/rc.common

START=99
STOP=10
USE_PROCD=1

PROG="/usr/sbin/openwrt_captive_monitor"
PID_FILE="/var/run/captive-monitor.pid"

start_service() {
    procd_open_instance
    procd_set_param command "$PROG"
    procd_set_param pidfile "$PID_FILE"
    procd_set_param respawn
    procd_set_param stdout 1
    procd_set_param stderr 1
    
    # Load UCI configuration
    config_load 'captive-monitor'
    config_get ENABLED config enabled '0'
    config_get MODE config mode 'monitor'
    
    if [ "$ENABLED" = "1" ]; then
        procd_append_param command "--$MODE"
    else
        echo "Service is disabled in UCI configuration"
        return 1
    fi
    
    procd_close_instance
}

stop_service() {
    if [ -f "$PID_FILE" ]; then
        kill $(cat "$PID_FILE")
        rm -f "$PID_FILE"
    fi
}

service_running() {
    [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null
}
```

---

## 📦 Distribution

### Repository Structure

```
openwrt-captive-monitor-feed/
├── packages/
│   ├── base/
│   │   └── openwrt-captive-monitor_1.0.0-1_all.ipk
│   ├── mips_24kc/
│   │   └── openwrt-captive-monitor_1.0.0-1_mips_24kc.ipk
│   └── x86_64/
│       └── openwrt-captive-monitor_1.0.0-1_x86_64.ipk
├── Packages
├── Packages.gz
└── Packages.manifest
```

### Feed Generation

```bash
#!/bin/bash
# generate-feed.sh - Generate opkg feed

FEED_DIR="dist/opkg"
PACKAGES_DIR="$FEED_DIR/packages"

# Create package directories
mkdir -p "$PACKAGES_DIR"/{base,mips_24kc,x86_64,aarch64_cortex-a53}

# Move packages to appropriate directories
for pkg in "$FEED_DIR"/*/*.ipk; do
    if [ -f "$pkg" ]; then
        arch=$(basename "$pkg" | sed -n 's/.*_\([^_]*\)\.ipk/\1/p')
        mkdir -p "$PACKAGES_DIR/$arch"
        mv "$pkg" "$PACKAGES_DIR/$arch/"
    fi
done

# Generate Packages files
for arch_dir in "$PACKAGES_DIR"/*; do
    if [ -d "$arch_dir" ]; then
        arch=$(basename "$arch_dir")
        echo "Generating Packages file for $arch"
        
        # Create Packages file
        {
            for pkg in "$arch_dir"/*.ipk; do
                if [ -f "$pkg" ]; then
                    echo "Package: $(basename "$pkg" | sed 's/_.*//')"
                    # Extract control information
                    tar -xOf "$pkg" ./control | sed '/^$/d'
                    echo "Filename: $(basename "$pkg")"
                    echo "Size: $(stat -c%s "$pkg")"
                    echo "MD5Sum: $(md5sum "$pkg" | cut -d' ' -f1)"
                    echo "SHA256sum: $(sha256sum "$pkg" | cut -d' ' -f1)"
                    echo ""
                fi
            done
        } > "$arch_dir/Packages"
        
        # Compress Packages file
        gzip -c "$arch_dir/Packages" > "$arch_dir/Packages.gz"
        
        # Create manifest (optional)
        ls -la "$arch_dir"/*.ipk > "$arch_dir/Packages.manifest"
    fi
done

echo "Feed generation complete!"
```

### GitHub Pages Hosting

```bash
#!/bin/bash
# deploy-gh-pages.sh - Deploy feed to GitHub Pages

# Checkout gh-pages branch
git checkout --orphan gh-pages
rm -rf *

# Copy feed content
cp -r dist/opkg/* .

# Create index.html
cat > index.html <<'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>OpenWrt Captive Monitor Feed</title>
</head>
<body>
    <h1>OpenWrt Captive Monitor Package Feed</h1>
    <p>Add this feed to your OpenWrt device:</p>
    <pre>src/gz captive_monitor https://[username].github.io/openwrt-captive-monitor</pre>
    <h2>Available Packages</h2>
    <ul>
EOF

# List packages
find . -name "*.ipk" | while read pkg; do
    pkg_name=$(basename "$pkg")
    echo "        <li><a href=\"$pkg_name\">$pkg_name</a></li>" >> index.html
done

cat >> index.html <<'EOF'
    </ul>
</body>
</html>
EOF

# Commit and push
git add .
git commit -m "Update package feed"
git push -f origin gh-pages

echo "Feed deployed to GitHub Pages!"
```

---

## 🔄 Package Management

### Version Management

```bash
#!/bin/bash
# update-version.sh - Update package version

NEW_VERSION=$1
if [ -z "$NEW_VERSION" ]; then
    echo "Usage: $0 VERSION"
    exit 1
fi

echo "Updating version to $NEW_VERSION"

# Update Makefile
sed -i "s/PKG_VERSION:=.*/PKG_VERSION:=$NEW_VERSION/" package/openwrt-captive-monitor/Makefile

# Update main script
sed -i "s/VERSION=.*/VERSION=\"$NEW_VERSION\"/" openwrt_captive_monitor.sh

# Update documentation
sed -i "s/v[0-9]\+\.[0-9]\+\.[0-9]\+/v$NEW_VERSION/g" README.md docs/*.md

# Create release notes template
cat > "docs/releases/v$NEW_VERSION.md" <<EOF
# openwrt-captive-monitor v$NEW_VERSION

## Highlights

## 🔄 Changes

### Added
- 

### Changed
- 

### Fixed
- 

### Security
- 

## 📦 Installation

### Prebuilt Packages
\`\`\`bash
wget https://github.com/nagual2/openwrt-captive-monitor/releases/download/v$NEW_VERSION/openwrt-captive-monitor_$NEW_VERSION-1_all.ipk
opkg install openwrt-captive-monitor_$NEW_VERSION-1_all.ipk
\`\`\`

## 🙏 Acknowledgments

Thanks to contributors who helped with this release:
EOF

git add .
git commit -m "bump: version $NEW_VERSION"
git tag -a "v$NEW_VERSION" -m "Release $NEW_VERSION"

echo "Version updated to $NEW_VERSION"
echo "Don't forget to push with: git push && git push --tags"
```

### Dependency Management

```bash
#!/bin/bash
# check-dependencies.sh - Verify package dependencies

PACKAGES_DIR="dist/opkg"
REQUIRED_DEPS="dnsmasq curl iptables busybox"

check_dependency() {
    local dep=$1
    local pkg_info=$(opkg info "$dep" 2>/dev/null)
    
    if [ -n "$pkg_info" ]; then
        echo "✓ $dep is available"
        return 0
    else
        echo "✗ $dep is NOT available"
        return 1
    fi
}

echo "Checking package dependencies..."

missing_deps=""
for dep in $REQUIRED_DEPS; do
    if ! check_dependency "$dep"; then
        missing_deps="$missing_deps $dep"
    fi
done

if [ -n "$missing_deps" ]; then
    echo ""
    echo "Missing dependencies:$missing_deps"
    echo "These dependencies must be installed before using openwrt-captive-monitor"
    exit 1
else
    echo ""
    echo "All dependencies are available ✓"
fi
```

---

## 📊 Package Analytics

### Download Tracking

```bash
#!/bin/bash
# track-downloads.sh - Track package downloads

GITHUB_API="https://api.github.com/repos/nagual2/openwrt-captive-monitor/releases"
DOWNLOADS_FILE="downloads.json"

# Get release information
curl -s "$GITHUB_API" > releases.json

# Process downloads
echo "{" > "$DOWNLOADS_FILE"
echo "  \"total_downloads\": 0," >> "$DOWNLOADS_FILE"
echo "  \"releases\": [" >> "$DOWNLOADS_FILE"

first=true
total=0

while IFS= read -r release; do
    tag=$(echo "$release" | jq -r '.tag_name')
    downloads=$(echo "$release" | jq -r '.assets | map(.download_count) | add')
    
    total=$((total + downloads))
    
    if [ "$first" = true ]; then
        first=false
    else
        echo "," >> "$DOWNLOADS_FILE"
    fi
    
    echo "    {" >> "$DOWNLOADS_FILE"
    echo "      \"tag\": \"$tag\"," >> "$DOWNLOADS_FILE"
    echo "      \"downloads\": $downloads" >> "$DOWNLOADS_FILE"
    echo "    }" >> "$DOWNLOADS_FILE"
done < <(jq -c '.[]' releases.json)

echo "  ]," >> "$DOWNLOADS_FILE"
echo "  \"total_downloads\": $total" >> "$DOWNLOADS_FILE"
echo "}" >> "$DOWNLOADS_FILE"

echo "Download statistics updated:"
jq '.' "$DOWNLOADS_FILE"
```

### Usage Analytics

```bash
#!/bin/bash
# generate-usage-report.sh - Generate usage analytics

REPORT_FILE="usage-report-$(date +%Y%m%d).md"

cat > "$REPORT_FILE" <<EOF
# OpenWrt Captive Monitor Usage Report

Generated: $(date)

## Installation Statistics

### Total Downloads
$(jq '.total_downloads' downloads.json)

### Downloads by Version
$(jq -r '.releases[] | "- \(.tag): \(.downloads) downloads"' downloads.json)

### Recent Activity

#### GitHub Stars
$(curl -s https://api.github.com/repos/nagual2/openwrt-captive-monitor | jq '.stargazers_count')

#### GitHub Forks
$(curl -s https://api.github.com/repos/nagual2/openwrt-captive-monitor | jq '.forks_count')

#### Open Issues
$(curl -s https://api.github.com/repos/nagual2/openwrt-captive-monitor | jq '.open_issues_count')

#### Closed Issues (Last 30 days)
$(curl -s "https://api.github.com/repos/nagual2/openwrt-captive-monitor/issues?state=closed&since=$(date -d '30 days ago' -Iseconds | cut -d' ' -f2 | tr -d 'Z')" | jq 'length')

## Community Engagement

### Recent Contributors
$(curl -s https://api.github.com/repos/nagual2/openwrt-captive-monitor/contributors | jq -r '.[] | "- \(.login)" | head -10)

### Recent Issues
$(curl -s https://api.github.com/repos/nagual2/openwrt-captive-monitor/issues?state=open | jq -r '.[] | "- #[\(.number)]: \(.title)" | head -5')

## Recommendations

Based on usage patterns and community feedback:

1. **Most Requested Features**
   - Multi-interface support
   - Web interface
   - Advanced logging

2. **Common Issues**
   - IPv6 compatibility
   - Firewall backend detection
   - Configuration complexity

3. **Improvement Areas**
   - Documentation completeness
   - Error handling clarity
   - Performance optimization
EOF

echo "Usage report generated: $REPORT_FILE"
```

---

## 🔍 Quality Assurance

### Package Validation

```bash
#!/bin/bash
# validate-package.sh - Comprehensive package validation

PACKAGE=$1
if [ -z "$PACKAGE" ]; then
    echo "Usage: $0 PACKAGE.ipk"
    exit 1
fi

echo "Validating package: $PACKAGE"

# Check file format
if ! file "$PACKAGE" | grep -q "gzip compressed"; then
    echo "✗ Package is not a valid gzip file"
    exit 1
fi

# Extract and validate structure
TEMP_DIR=$(mktemp -d)
tar -xzf "$PACKAGE" -C "$TEMP_DIR"

# Required files
REQUIRED_FILES=(
    "./control"
    "./data.tar.gz"
    "./debian-binary"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$TEMP_DIR/$file" ]; then
        echo "✗ Missing required file: $file"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
done

# Validate control file
CONTROL_FILE="$TEMP_DIR/control"
if ! grep -q "^Package: openwrt-captive-monitor" "$CONTROL_FILE"; then
    echo "✗ Invalid package name in control file"
    rm -rf "$TEMP_DIR"
    exit 1
fi

if ! grep -q "^Version:" "$CONTROL_FILE"; then
    echo "✗ Missing version in control file"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Validate data contents
tar -tzf "$TEMP_DIR/data.tar.gz" > "$TEMP_DIR/files.txt"

REQUIRED_DATA_FILES=(
    "./usr/sbin/openwrt_captive_monitor"
    "./etc/config/captive-monitor"
    "./etc/init.d/captive-monitor"
)

for file in "${REQUIRED_DATA_FILES[@]}"; do
    if ! grep -q "^$file$" "$TEMP_DIR/files.txt"; then
        echo "✗ Missing required data file: $file"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
done

# Check executable permissions
tar -xf "$TEMP_DIR/data.tar.gz" -C "$TEMP_DIR"

if [ ! -x "$TEMP_DIR/usr/sbin/openwrt_captive_monitor" ]; then
    echo "✗ Main executable is not executable"
    rm -rf "$TEMP_DIR"
    exit 1
fi

if [ ! -x "$TEMP_DIR/etc/init.d/captive-monitor" ]; then
    echo "✗ Init script is not executable"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Cleanup
rm -rf "$TEMP_DIR"

echo "✓ Package validation passed"
```

### Installation Testing

```bash
#!/bin/bash
# test-installation.sh - Test package installation and removal

PACKAGE=$1
TEST_DEVICE=$2

if [ -z "$PACKAGE" ] || [ -z "$TEST_DEVICE" ]; then
    echo "Usage: $0 PACKAGE.ipk root@device-ip"
    exit 1
fi

echo "Testing package installation on $TEST_DEVICE"

# Copy package to device
scp "$PACKAGE" "$TEST_DEVICE:/tmp/test-package.ipk"

# Test installation
ssh "$TEST_DEVICE" <<'EOSSH'
# Remove existing installation
opkg remove openwrt-captive-monitor 2>/dev/null || true

# Install package
echo "Installing package..."
if opkg install /tmp/test-package.ipk; then
    echo "✓ Package installed successfully"
else
    echo "✗ Package installation failed"
    exit 1
fi

# Verify files
echo "Verifying installation..."
if [ -f "/usr/sbin/openwrt_captive_monitor" ]; then
    echo "✓ Main executable present"
else
    echo "✗ Main executable missing"
    exit 1
fi

if [ -f "/etc/config/captive-monitor" ]; then
    echo "✓ Configuration file present"
else
    echo "✗ Configuration file missing"
    exit 1
fi

if [ -x "/etc/init.d/captive-monitor" ]; then
    echo "✓ Init script present and executable"
else
    echo "✗ Init script missing or not executable"
    exit 1
fi

# Test service
echo "Testing service..."
if /etc/init.d/captive-monitor status; then
    echo "✓ Service status check works"
else
    echo "✗ Service status check failed"
fi

# Test configuration
if uci show captive-monitor >/dev/null 2>&1; then
    echo "✓ UCI configuration works"
else
    echo "✗ UCI configuration failed"
    exit 1
fi

# Test removal
echo "Testing removal..."
if opkg remove openwrt-captive-monitor; then
    echo "✓ Package removed successfully"
else
    echo "✗ Package removal failed"
    exit 1
fi

# Verify cleanup
if [ ! -f "/usr/sbin/openwrt_captive_monitor" ]; then
    echo "✓ Files cleaned up on removal"
else
    echo "✗ Files not cleaned up on removal"
    exit 1
fi

echo "✓ All installation tests passed"
EOSSH

if [ $? -eq 0 ]; then
    echo "✓ Installation test completed successfully"
else
    echo "✗ Installation test failed"
    exit 1
fi
```

This comprehensive package management guide ensures high-quality, reliable packages for the openwrt-captive-monitor project.