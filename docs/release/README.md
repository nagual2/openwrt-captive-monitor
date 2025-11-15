# Release Documentation

This section contains documentation related to the release process, versioning, and deployment.

## 📋 Core Documentation

### Release Process
- [**Auto Version Tag (Active)**](AUTO_VERSION_TAG.md) - Date-based automatic versioning (vYYYY.M.D.N)
- [Release Process (Legacy)](RELEASE_PROCESS.md) - Historical semantic versioning documentation
- [Changelog](CHANGELOG.md) - Version history and release notes

## 🚀 Release Overview

### Release Types
- **Major releases** (X.0.0) - Breaking changes and major features
- **Minor releases** (X.Y.0) - New features and improvements
- **Patch releases** (X.Y.Z) - Bug fixes and security patches

### Release Cadence
- **Major**: As needed, with extensive testing
- **Minor**: Monthly or as features are ready
- **Patch**: As needed for critical fixes

## 🔄 Release Process

### Pre-Release Checklist
1. All tests passing
2. Documentation updated
3. Changelog updated
4. Security scan completed
5. Review completed

### Release Steps
1. Create release branch
2. Update version numbers
3. Run full test suite
4. Build packages
5. Create GitHub release
6. Deploy to repositories
7. Update documentation

### Post-Release
1. Monitor for issues
2. Announce release
3. Update project status
4. Plan next release

## 📦 Package Distribution

### Official Packages
- [GitHub Releases](https://github.com/nagual2/openwrt-captive-monitor/releases) - Official IPK packages
- OpenWrt packages feed (future)

### Build Artifacts
- IPK packages for all architectures
- Source tarballs
- Build logs
- Test results

## 🔍 Version Information

### Current Version
See the [VERSION](../../VERSION) file for the current version.

### Version History
See the [Changelog](CHANGELOG.md) for detailed version history.

### Semantic Versioning
This project follows [Semantic Versioning 2.0.0](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality in a backwards compatible manner
- **PATCH**: Backwards compatible bug fixes

## 🛡️ Security Releases

### Security Patch Process
1. Security vulnerability identified
2. Fix developed in private branch
3. Security advisory prepared
4. Coordinated release with maintainers
5. Public disclosure and patch release

### Security Updates
- Critical security patches released as soon as possible
- Security advisories published with each security release
- Backports provided for supported versions

## 📊 Release Metrics

### Release Statistics
- Release frequency and patterns
- Bug fix turnaround time
- Feature delivery timeline
- Security response time

### Quality Metrics
- Test coverage per release
- Bug counts and types
- Performance benchmarks
- User feedback analysis

## 🔧 Development Tools

### Release Automation
- **Release Please** - Automated versioning and changelog generation
- **GitHub Actions** - Automated build, test, and release workflows
- **Cosign** - Artifact signing and verification

### Configuration
- [Release Please Config](../../release-please-config.json) - Release automation configuration
- [GitHub Workflows](../../../.github/workflows/) - CI/CD and release workflows

## 📚 Related Documentation

### Development
- [Contributing Guide](../contributing/CONTRIBUTING.md) - Development guidelines
- [Setup Documentation](../setup/) - Development setup
- [CI/CD Documentation](../setup/CI_MODERNIZATION_2025.md) - Build and release automation

### Project Management
- [Project Management](../project/management.md) - Project planning and roadmap
- [Release Checklist](../project/release-checklist.md) - Detailed release checklist
- [Test Plan](../project/test-plan.md) - Testing procedures

### Security
- [Security Documentation](../security/) - Security policies and procedures
- [Security Scanning](../SECURITY_SCANNING.md) - Automated security scanning

## 📞 Support

### Getting Help
- [Support Documentation](../../../.github/SUPPORT.md) - Getting help and support
- [GitHub Issues](https://github.com/nagual2/openwrt-captive-monitor/issues) - Bug reports and feature requests
- [GitHub Discussions](https://github.com/nagual2/openwrt-captive-monitor/discussions) - Community support

### Release Issues
- Report release-specific issues via GitHub Issues
- Use the "release" label for release-related problems
- Include version information in all reports

---

**Last updated:** 2025-11-14