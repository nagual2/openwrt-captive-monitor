# Release Checklist

This checklist documents the release process for **openwrt-captive-monitor** and should be followed for each new version.

## 📋 Pre-Release Checklist

### 1. Code Quality and Testing

- [ ] All pull requests merged to `develop` branch
- [ ] Code review completed for all changes
- [ ] Automated tests passing (`shellcheck`, `shfmt`)
- [ ] Manual testing on target devices completed
- [ ] Documentation updated for all new features
- [ ] CHANGELOG.md updated with version notes

### 2. Version Preparation

- [ ] Version numbers updated in:
  - `package/openwrt-captive-monitor/Makefile`
  - Any version-specific constants in scripts
- [ ] Release notes prepared
- [ ] Migration guide updated (if breaking changes)

### 3. Build Verification

```bash
# Test package building
scripts/build_ipk.sh --arch all

# Verify package contents
tar -tzf dist/opkg/all/openwrt-captive-monitor_*.ipk

# Run test suite
busybox sh tests/run.sh
```

- [ ] Package builds successfully
- [ ] Package contents verified
- [ ] Test suite passes
- [ ] Installation/removal tested

---

## 🚀 Release Process

### 1. Create Release Branch

```bash
# Create release branch from develop
git checkout develop
git pull origin develop
git checkout -b release/vX.Y.Z

# Update version if needed
# Edit package/openwrt-captive-monitor/Makefile
git add package/openwrt-captive-monitor/Makefile
git commit -m "bump: version X.Y.Z"
```

### 2. Final Testing

- [ ] Smoke test on real hardware
- [ ] Configuration validation
- [ ] Service start/stop/restart testing
- [ ] Captive portal simulation testing
- [ ] Cleanup verification

### 3. Tag and Merge

```bash
# Merge to main
git checkout main
git merge --no-ff release/vX.Y.Z
git tag -a vX.Y.Z -m "Release vX.Y.Z"

# Merge back to develop
git checkout develop
git merge --no-ff release/vX.Y.Z

# Push changes
git push origin main
git push origin develop
git push origin vX.Y.Z
```

### 4. GitHub Release

- [ ] GitHub Actions workflow completes successfully
- [ ] Release artifacts generated:
  - `openwrt-captive-monitor_X.Y.Z-1_all.ipk`
  - `Packages`
  - `Packages.gz`
- [ ] GitHub Release created with:
  - Version tag
  - Release notes
  - Artifact attachments
  - Checksums

---

## 📦 Package Distribution

### 1. Automatic Build Process

The GitHub Actions workflow automatically:

1. **Provisions OpenWrt SDK**
2. **Builds package** for multiple architectures
3. **Runs test suite** to validate package
4. **Generates opkg feed** with `Packages` and `Packages.gz`
5. **Uploads artifacts** to GitHub Release

### 2. Manual Build (if needed)

```bash
# Build for specific architecture
scripts/build_ipk.sh --arch mips_24kc

# Build for all architectures
for arch in mips_24kc aarch64_cortex-a53 x86_64; do
    scripts/build_ipk.sh --arch $arch
done

# Generate checksums
cd dist/opkg
find . -type f -name "*.ipk" -exec sha256sum {} + > SHA256SUMS
find . -type f -name "Packages*" -exec sha256sum {} + >> SHA256SUMS
```

---

## 📋 Post-Release Checklist

### 1. Verification

- [ ] GitHub Release published correctly
- [ ] All artifacts attached to release
- [ ] Checksums generated and verified
- [ ] Package installs correctly on test device
- [ ] Service starts and functions properly

### 2. Documentation Updates

- [ ] Create release notes in `docs/releases/vX.Y.Z.md`
- [ ] Update main README.md with new version
- [ ] Update documentation index if needed
- [ ] Announce release in GitHub Discussions

### 3. Branch Cleanup

```bash
# Delete release branch
git branch -d release/vX.Y.Z
git push origin --delete release/vX.Y.Z
```

### 4. Community Communication

- [ ] Release announcement in GitHub Discussions
- [ ] Update any external package repositories
- [ ] Notify downstream users/maintainers
- [ ] Monitor for issues and feedback

---

## 🔍 Quality Assurance Checklist

### Package Validation

```bash
# Verify package structure
tar -tzf openwrt-captive-monitor_*.ipk

# Check control file
tar -xf openwrt-captive-monitor_*.ipk
cat ./control

# Verify conffiles
cat ./conffiles

# Check file permissions
tar -tf openwrt-captive-monitor_*.ipk | xargs -I {} tar -xf openwrt-captive-monitor_*.ipk {} --to-command=ls -l {}
```

### Installation Testing

```bash
# Test installation
opkg install openwrt-captive-monitor_*.ipk

# Verify files
opkg files openwrt-captive-monitor

# Test service
/etc/init.d/captive-monitor status
uci show captive-monitor

# Test removal
opkg remove openwrt-captive-monitor
```

### Functional Testing

- [ ] Service starts without errors
- [ ] Configuration loading works
- [ ] Network interface detection works
- [ ] Connectivity checking functions
- [ ] Captive portal detection works
- [ ] Traffic interception functions
- [ ] Cleanup process works correctly

---

## 🚨 Emergency Release Process

### Critical Security Issues

1. **Immediate Action**
   - Create `hotfix/security-X.Y.Z` branch from `main`
   - Fix the security issue
   - Minimal testing focused on security fix
   - Immediate release

2. **Follow-up Actions**
   - Full testing after release
   - Backport to other maintained versions
   - Security advisory publication
   - Community notification

### Critical Bugs

1. **Rapid Response**
   - Create `hotfix/bug-X.Y.Z` branch from `main`
   - Fix the bug
   - Focused testing on bug scenario
   - Patch release

2. **Verification**
   - Ensure fix doesn't introduce regressions
   - Update documentation if needed
   - Communicate fix to users

---

## 📊 Release Metrics

### Tracking

For each release, track:

- **Release Date**: When release was published
- **Issues Fixed**: Number and type of issues resolved
- **Features Added**: New functionality introduced
- **Breaking Changes**: Any incompatible changes
- **Downloads**: Package download statistics
- **Issues Reported**: Post-release issues and feedback

### Quality Metrics

- **Test Coverage**: Percentage of code covered by tests
- **Bug Discovery Time**: Time between release and first bug report
- **User Satisfaction**: Community feedback and issue resolution time
- **Adoption Rate**: Speed of user upgrades to new version

---

## 📝 Release Template

### Release Notes Template

```markdown
# openwrt-captive-monitor v{VERSION}

## Highlights

- **Feature**: Brief description of new feature
- **Improvement**: Description of enhancement
- **Fix**: Description of bug fix

## 🔄 Changes

### Added
- New feature 1
- New feature 2

### Changed
- Modified behavior 1
- Updated configuration 2

### Fixed
- Bug fix 1
- Bug fix 2

### Security
- Security fix 1

## 📦 Installation

### Prebuilt Packages
```bash
wget https://github.com/nagual2/openwrt-captive-monitor/releases/download/v{VERSION}/openwrt-captive-monitor_{VERSION}-1_all.ipk
opkg install openwrt-captive-monitor_{VERSION}-1_all.ipk
```

### From Source
```bash
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor
git checkout v{VERSION}
scripts/build_ipk.sh --arch all
opkg install dist/opkg/all/openwrt-captive-monitor_{VERSION}-1_all.ipk
```

## ⚙️ Configuration

No configuration changes required for this release.

## 🔄 Migration

No migration steps required for this release.

## 🐛 Known Issues

- List any known issues

## 🙏 Acknowledgments

Thanks to contributors who helped with this release:
- @contributor1
- @contributor2
```

---

## 🔧 Tools and Automation

### Release Script

```bash
#!/bin/bash
# release.sh - Automated release helper

set -e

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: $0 VERSION"
    exit 1
fi

echo "Releasing version $VERSION"

# Update version
sed -i "s/PKG_VERSION:=.*/PKG_VERSION:=$VERSION/" package/openwrt-captive-monitor/Makefile
git add package/openwrt-captive-monitor/Makefile
git commit -m "bump: version $VERSION"

# Create release branch
git checkout -b release/v$VERSION develop

# Run tests
echo "Running tests..."
busybox sh tests/run.sh

# Build package
echo "Building package..."
scripts/build_ipk.sh --arch all

# Tag and push
git checkout main
git merge --no-ff release/v$VERSION
git tag -a v$VERSION -m "Release $VERSION"

echo "Release $VERSION ready. Push with:"
echo "git push origin main"
echo "git push origin v$VERSION"
```

### Validation Script

```bash
#!/bin/bash
# validate-release.sh - Release validation

set -e

VERSION=$1
PACKAGE="openwrt-captive-monitor_${VERSION}-1_all.ipk"

echo "Validating release $VERSION"

# Check if package exists
if [ ! -f "dist/opkg/all/$PACKAGE" ]; then
    echo "ERROR: Package not found: $PACKAGE"
    exit 1
fi

# Validate package structure
echo "Validating package structure..."
tar -tzf "dist/opkg/all/$PACKAGE" | while read file; do
    echo "  $file"
done

# Check required files
REQUIRED_FILES=(
    "./control"
    "./conffiles"
    "./usr/sbin/openwrt_captive_monitor"
    "./etc/init.d/captive-monitor"
    "./etc/config/captive-monitor"
)

for file in "${REQUIRED_FILES[@]}"; do
    if ! tar -tf "dist/opkg/all/$PACKAGE" | grep -q "^$file$"; then
        echo "ERROR: Required file missing: $file"
        exit 1
    fi
done

echo "✓ Release validation passed"
```

This checklist ensures consistent, high-quality releases while maintaining project standards and community expectations.