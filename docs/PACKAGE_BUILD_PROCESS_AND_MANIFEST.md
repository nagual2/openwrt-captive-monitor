# OpenWrt Package Build Process and File Manifest

This document provides a comprehensive analysis of the OpenWrt package build process for `openwrt-captive-monitor`, detailing what files are included, excluded, and how the packaging works.

## Part 1: Build Configuration Analysis

### Makefile Structure (`package/openwrt-captive-monitor/Makefile`)

```makefile
PKG_NAME:=openwrt-captive-monitor
PKG_VERSION:=1.0.3
PKG_RELEASE:=1
PKG_ARCH:=all
```

**Key Settings:**
- **PKG_ARCH**: `all` - Universal package that works on all OpenWrt architectures
- **PKG_VERSION**: `1.0.3` - Current version (matches VERSION file in repo root)
- **PKG_RELEASE**: `1` - Package release number for this version

**Metadata:**
- **PKG_LICENSE**: MIT
- **PKG_LICENSE_FILES**: LICENSE
- **PKG_MAINTAINER**: OpenWrt Captive Monitor Team
- **PKG_SOURCE_URL**: https://github.com/nagual2/openwrt-captive-monitor
- **PKG_SOURCE_PROTO**: git
- **PKG_SOURCE_VERSION**: v$(PKG_VERSION)

### Build Script (`scripts/build_ipk.sh`)

The build script is a comprehensive 536-line shell script that:

**How it works:**
1. **Parses Makefile variables** using awk to extract PKG_* variables
2. **Creates temporary build directory** with data/ and control/ subdirectories
3. **Copies payload files** from `package/openwrt-captive-monitor/files/` to data/
4. **Sets correct permissions** on executable files
5. **Generates control files** (control, postinst, prerm, postrm, conffiles)
6. **Creates tar archives** (data.tar.gz, control.tar.gz)
7. **Builds .ipk package** using `ar` command
8. **Updates opkg feed** with Packages and Packages.gz indexes

**Commands it runs:**
- `cp -a` - Copy files preserving permissions
- `chmod 0755` - Set executable permissions
- `tar --numeric-owner --owner=0 --group=0 -czf` - Create tar archives
- `ar r` - Create .ipk archive
- `opkg-make-index` - Generate package index (if available)
- `md5sum`, `sha256sum` - Calculate checksums

**Output:**
- `.ipk` package file
- `Packages` index file
- `Packages.gz` compressed index
- Optional JSON metadata in release mode

## Part 2: File Manifest - What Gets Included

### openwrt-captive-monitor_1.0.3-1_all.ipk contains:

**Payload Files (data.tar.gz):**
- `./etc/config/captive-monitor` (type: UCI config file, 519 bytes, 644)
- `./etc/uci-defaults/99-captive-monitor` (type: setup script, 1,002 bytes, 755)
- `./etc/init.d/captive-monitor` (type: init script, 3,548 bytes, 755)
- `./usr/share/licenses/openwrt-captive-monitor/LICENSE` (type: license file, 1,076 bytes, 644)
- `./usr/sbin/openwrt_captive_monitor` (type: main executable, 58,409 bytes, 755)

**Control Files (control.tar.gz):**
- `./control` (type: package metadata, 587 bytes, 644)
- `./postinst` (type: post-install script, 295 bytes, 755)
- `./prerm` (type: pre-remove script, 178 bytes, 755)
- `./postrm` (type: post-remove script, 114 bytes, 755)
- `./conffiles` (type: config file list, 28 bytes, 644)

**Package Metadata (debian-binary):**
- `./debian-binary` (type: format version, 4 bytes, 644)

**Total Package Size:** 14,206 bytes (13.9 KB)
**Installed Size:** 116 KB

## Part 3: File Manifest - What Gets Excluded

### NOT included in package:

**Version Control:**
- `.git/` (reason: version control metadata, not needed at runtime)
- `.gitignore` (reason: development file, not needed at runtime)

**CI/CD and Development:**
- `.github/` (reason: CI/CD workflows, not needed at runtime)
- `.ci_trigger` (reason: CI trigger file, not needed at runtime)
- `.editorconfig` (reason: editor configuration, not needed at runtime)
- `.shellcheckrc` (reason: linting configuration, not needed at runtime)
- `.shfmt.conf` (reason: formatting configuration, not needed at runtime)
- `.markdownlint.json` (reason: documentation linting, not needed at runtime)

**Project Management:**
- `.release-please-manifest.json` (reason: release automation, not needed at runtime)
- `release-please-config.json` (reason: release automation, not needed at runtime)
- `VERSION` (reason: build-time version reference, not needed at runtime)

**Documentation:**
- `README.md` (reason: documentation, not needed at runtime)
- `README.md.backup` (reason: backup documentation, not needed at runtime)
- `CHANGELOG.md` (reason: documentation, not needed at runtime)
- `CONTRIBUTING.md` (reason: documentation, not needed at runtime)
- `CODE_OF_CONDUCT.md` (reason: documentation, not needed at runtime)
- `docs/` (reason: documentation directory, not needed at runtime)
- `MARKDOWN_AUDIT_REPORT.md` (reason: documentation, not needed at runtime)
- `README_LINKS_REPORT.md` (reason: documentation, not needed at runtime)
- `README_RESTORATION_REPORT.md` (reason: documentation, not needed at runtime)
- `RELEASE_SUMMARY_v1.0.3.md` (reason: documentation, not needed at runtime)
- `BRANCH_AUDIT_SUMMARY.txt` (reason: documentation, not needed at runtime)

**Development Artifacts:**
- `tests/` (reason: test files, not needed at runtime)
- `scripts/` (reason: build scripts, not needed at runtime)
- `patches/` (reason: patch files, not needed at runtime)
- `package/` (reason: build definition, not needed at runtime)

**Development Files:**
- `openwrt_captive_monitor.sh` (reason: development script, not needed at runtime)
- `setup_captive_monitor.sh` (reason: setup script, not needed at runtime)
- `local/` (reason: local development files, not needed at runtime)
- `init.d/` (reason: development init scripts, not needed at runtime)

**Build Output:**
- `dist/` (reason: build output directory, not needed at runtime)

**Root Level Files (not packaged):**
- Root `etc/`, `usr/` directories (reason: development copies, packaged versions are in `package/openwrt-captive-monitor/files/`)
- Root `LICENSE` (reason: development copy, packaged version is in `files/usr/share/licenses/openwrt-captive-monitor/LICENSE`)

## Part 4: Build Process Flow

### Complete Build Flow:

1. **Prerequisites/Dependencies:**
   - Required tools: `ar`, `tar`, `gzip`, `md5sum`, `sha256sum`, `stat`
   - Optional tools: `opkg-make-index`, `pigz` (for faster compression)
   - Source files in `package/openwrt-captive-monitor/files/`

2. **OpenWrt SDK Setup:**
   - Script doesn't require full OpenWrt SDK
   - Uses standard Unix tools only
   - Parses Makefile directly without OpenWrt build system

3. **File Selection/Filtering:**
   - Only files from `package/openwrt-captive-monitor/files/` are included
   - All other repository directories are excluded
   - Files are copied with `cp -a` to preserve permissions

4. **Shell Script Packaging:**
   - Executable scripts get `chmod 0755` applied explicitly
   - Ensures correct permissions regardless of build environment umask
   - Scripts: `openwrt_captive_monitor`, `captive-monitor`, `99-captive-monitor`

5. **Config File Handling:**
   - UCI config file `/etc/config/captive-monitor` marked as conffile
   - Listed in `conffiles` control file to preserve user modifications during upgrades
   - Configuration applied via UCI defaults script during first install

6. **Metadata Generation:**
   - Control file generated from Makefile variables
   - Package metadata includes dependencies: `dnsmasq`, `curl`
   - Scripts for install/remove lifecycle management
   - Checksums calculated for all artifacts

7. **Final .ipk File Creation:**
   - Three components: `debian-binary`, `control.tar.gz`, `data.tar.gz`
   - Assembled using `ar r` command
   - Output: `openwrt-captive-monitor_1.0.3-1_all.ipk`

## Part 5: Directory Structure in .ipk

```
openwrt-captive-monitor_1.0.3-1_all.ipk/
├── debian-binary                    (format version: "2.0")
├── control.tar.gz                   (control metadata)
│   ├── ./control                    (package metadata)
│   ├── ./postinst                   (post-install script)
│   ├── ./prerm                      (pre-remove script)
│   ├── ./postrm                     (post-remove script)
│   └── ./conffiles                  (list of config files)
└── data.tar.gz                      (actual files)
    ├── ./etc/
    │   ├── config/
    │   │   └── captive-monitor      (UCI configuration)
    │   ├── init.d/
    │   │   └── captive-monitor      (init script)
    │   └── uci-defaults/
    │       └── 99-captive-monitor   (first-time setup)
    └── ./usr/
        ├── sbin/
        │   └── openwrt_captive_monitor (main executable)
        └── share/
            └── licenses/
                └── openwrt-captive-monitor/
                    └── LICENSE      (license file)
```

**File Type Summary:**
- **Shell Scripts (755):** 3 files (main executable, init script, UCI defaults)
- **Config Files (644):** 2 files (UCI config, license)
- **Control Scripts (755):** 3 files (postinst, prerm, postrm)
- **Control Files (644):** 2 files (control, conffiles)

## Part 6: Makefile Explanation

### Key Makefile Sections:

**PKG_SOURCE_DATE_EPOCH:**
- Not explicitly set in this Makefile
- Would normally be used for reproducible builds
- OpenWrt uses this to ensure consistent timestamps across builds

**define Package/openwrt-captive-monitor:**
- Defines package metadata
- SECTION: net (network category)
- CATEGORY: Network (main category)
- SUBMENU: Captive Portals (subcategory)
- TITLE: Brief description
- DEPENDS: +dnsmasq +curl (runtime dependencies)
- URL: Project homepage

**define Package/openwrt-captive-monitor/install:**
- Defines which files get installed and where
- Uses OpenWrt install macros:
  - `INSTALL_DIR` - Create directory
  - `INSTALL_BIN` - Install executable (755)
  - `INSTALL_CONF` - Install config file (644)
  - `INSTALL_DATA` - Install data file (644)
- Maps source files to target filesystem locations

**define Package/openwrt-captive-monitor/postinst:**
- Post-installation script
- Runs UCI defaults on first install
- Disables service by default
- Stops service if running
- Only runs on actual system (not in build root)

**Build targets and rules:**
- `Build/Prepare`: Creates build directory (minimal)
- `Build/Compile`: No-op (shell scripts don't need compilation)
- `BuildPackage`: Final package creation rule

### OpenWrt Packaging Concepts:

**Architecture Handling:**
- `PKG_ARCH:=all` means package works on all architectures
- Contains only shell scripts and config files (no compiled binaries)
- Single universal package instead of architecture-specific builds

**Dependency Management:**
- Runtime dependencies declared in DEPENDS
- Uses + prefix for opkg dependency syntax
- Dependencies: dnsmasq (DNS server), curl (HTTP client)

**Configuration Management:**
- UCI config file for user settings
- UCI defaults script for initial configuration
- Service disabled by default for security

**Lifecycle Scripts:**
- postinst: Runs after installation
- prerm: Runs before removal  
- postrm: Runs after removal
- All scripts handle both install and upgrade scenarios

## Summary

The OpenWrt package build process creates a compact, universal package containing only the essential runtime files:

**What's in the .ipk:**
- 5 payload files (1 main executable, 1 init script, 1 UCI defaults script, 1 config file, 1 license)
- 5 control files (metadata and lifecycle scripts)
- Total size: 13.9 KB compressed, 116 KB installed

**How it got there:**
- Files sourced from `package/openwrt-captive-monitor/files/` only
- Build script creates proper OpenWrt package structure
- Permissions and metadata handled automatically
- Dependencies and configuration properly declared

**What's excluded:**
- All development, documentation, and build files
- Version control and CI/CD artifacts  
- Test files and build scripts
- Duplicate files (only packaged versions included)

The result is a clean, production-ready OpenWrt package that follows OpenWrt packaging conventions and provides a complete captive portal monitoring solution.