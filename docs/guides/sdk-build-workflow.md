# OpenWrt SDK-based CI/CD Workflow

This guide explains the simplified OpenWrt SDK-based CI/CD workflow implemented for building the openwrt-captive-monitor package.

## Overview

The project uses the official OpenWrt SDK for building IPK packages following the documented SDK workflow. This ensures better compatibility, proper dependency resolution, and alignment with OpenWrt standards.

## Workflow Files

### Main CI/CD Pipeline
- **File**: `.github/workflows/ci.yml`
- **Pipeline**: lint → test → SDK build → artifact upload
- **Triggers**: 
  - Push to main and feature branches
  - Pull requests to main
  - Tag pushes (for releases)
  - Manual workflow dispatch

### Supporting Workflows
- **`.github/workflows/release-please.yml`**: Automated version management
- **`.github/workflows/cleanup.yml`**: Artifact and run cleanup
- **`.github/workflows/upload-sdk-to-release.yml`**: SDK mirror management

## Build Process

### 1. Environment Setup
- Downloads OpenWrt SDK version 23.05.3 for x86_64 architecture
- Caches SDK for faster subsequent builds
- Installs required build dependencies

### 2. Package Preparation
- Copies the package to SDK structure
- Updates OpenWrt feeds (`./scripts/feeds update -a`)
- Installs feed dependencies (`./scripts/feeds install -a`)

### 3. Compilation
- Uses official OpenWrt make system
- Builds with `make package/openwrt-captive-monitor/compile V=s`
- Produces standard OpenWrt IPK package

### 4. Validation
- Runs `scripts/validate_ipk.sh` to verify package integrity
- Checks package structure and metadata
- Validates file permissions and dependencies

### 5. Artifact Management
- Uploads build artifacts to GitHub Actions
- Creates releases automatically on tag pushes
- Provides detailed build logs and metadata

## Caching Strategy

### SDK Cache
- **Key**: `{runner.os}-openwrt-sdk-{version}-{arch}-{cache-version}`
- **Content**: Downloaded SDK tarball and extracted directory
- **Duration**: Persistent until SDK version changes

### Feeds Cache
- **Key**: `{runner.os}-openwrt-feeds-{version}-{arch}-{hash}`
- **Content**: Downloaded feeds and package sources
- **Duration**: Rebuilt when package Makefiles change

## Quality Assurance

### Pre-build Checks
- Shell script formatting with `shfmt`
- Shell script linting with `shellcheck`
- Markdown linting
- GitHub Actions workflow linting

### Testing
- Comprehensive test suite in `tests/run.sh`
- BusyBox compatibility testing
- Mock environment testing

### Post-build Validation
- IPK package structure verification
- Control file validation
- Dependency checking
- File permission verification

## Release Process

### Automated Releases
1. **Version Update**: `release-please` workflow creates release PR
2. **Version Bump**: VERSION file and Makefile updated
3. **Tag Creation**: Release tag is created
4. **SDK Build**: New workflow builds package with SDK
5. **Release Publish**: Artifacts attached to GitHub release

### Manual Releases
1. Create and push a version tag: `git tag v1.0.0 && git push origin v1.0.0`
2. Workflow automatically triggers and builds the package
3. Release is created with build artifacts

## Build Environment

### OpenWrt Version
- **Version**: 23.05.3 (current stable)
- **Architecture**: x86_64 (universal compatibility)
- **GCC Version**: 12.3.0
- **Libc**: musl

### Build Tools
- **Compiler**: GCC 12.3.0
- **Package Builder**: OpenWrt SDK make system
- **Dependency Manager**: OpenWrt feeds system

## Package Information

### Package Metadata
- **Name**: openwrt-captive-monitor
- **Category**: Network → Captive Portals
- **Dependencies**: dnsmasq, curl
- **Architecture**: all (compatible with all OpenWrt architectures)

### Package Contents
- `/usr/sbin/openwrt_captive_monitor` - Main executable
- `/etc/init.d/captive-monitor` - Init script
- `/etc/config/captive-monitor` - UCI configuration
- `/etc/uci-defaults/99-captive-monitor` - Default settings

## Troubleshooting

### Common Issues

#### SDK Download Failures
- Check network connectivity
- Verify OpenWrt download server status
- Check available disk space

#### Build Failures
- Review build logs for specific errors
- Check dependency availability in feeds
- Verify package Makefile syntax

#### Test Failures
- Ensure test environment is properly set up
- Check mock binaries in `tests/mocks/`
- Verify BusyBox compatibility

### Debug Information

#### Build Logs
- Full build output available in GitHub Actions logs
- Verbose mode enabled with `V=s` flag
- Individual package build logs preserved

#### Package Inspection
```bash
# Extract and examine IPK contents
ar x package.ipk
tar -xzf data.tar.gz
tar -xzf control.tar.gz

# Check package information
opkg info package.ipk
opkg depends package.ipk
```

## Migration from Old Build System

### Changes
- **Old**: Custom `scripts/build_ipk.sh` script
- **New**: Official OpenWrt SDK build system

### Benefits
1. **Standard Compliance**: Uses official OpenWrt build tools
2. **Better Dependency Management**: Leverages OpenWrt feeds
3. **Cross-platform Compatibility**: SDK supports multiple architectures
4. **Future-proofing**: Aligned with OpenWrt development practices

### Compatibility
- Package structure remains unchanged
- Installation process identical
- Runtime behavior consistent
- Configuration format preserved

## Performance Considerations

### Build Time
- **Initial Build**: 15-20 minutes (includes SDK download)
- **Cached Build**: 5-10 minutes
- **Incremental Build**: 2-5 minutes (package-only changes)

### Resource Usage
- **Memory**: 2-4GB RAM recommended
- **Disk**: 5-10GB temporary space
- **Network**: 500MB-1GB for SDK download

## Future Enhancements

### Multi-architecture Support
- Add support for ARM, MIPS, and other architectures
- Matrix builds for different target platforms
- Architecture-specific optimization

### Advanced Caching
- Docker layer caching for faster builds
- Incremental feed updates
- Package-specific caching strategies

### Integration Testing
- VM-based testing with built packages
- Automated installation testing
- Runtime behavior validation
