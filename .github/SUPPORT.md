# Support

## Getting Help

The openwrt-captive-monitor project provides several channels for getting support, reporting bugs, and asking
questions. Choose the most appropriate channel for your needs.

## 🐛 Bug Reports

**Where to file**: [GitHub
Issues](https://github.com/nagual2/openwrt-captive-monitor/issues/new?assignees=&labels=bug&template=bug_report.md)

**Before reporting**:
1. Check existing [open
issues](https://github.com/nagual2/openwrt-captive-monitor/issues?q=is%3Aissue+is%3Aopen+label%3Abug) to avoid
duplicates
2. Ensure you're using the latest version
3. Test on a clean installation if possible
4. Gather relevant logs and configuration details

**What to include**:
* OpenWrt version and device model
* openwrt-captive-monitor version
* Complete error messages and logs
* Steps to reproduce the issue
* Current configuration (sanitized)

## 💬 Questions and General Discussion

**GitHub Discussions**: [Start a discussion](https://github.com/nagual2/openwrt-captive-monitor/discussions/new)
* Use this for "how-to" questions, configuration help, and general discussion
* Perfect for troubleshooting that isn't clearly a bug
* Community-driven support from other users and maintainers

**GitHub Issues with "question" label**: [Create an
issue](https://github.com/nagual2/openwrt-captive-monitor/issues/new?assignees=&labels=question&template=---)
* Use when you have a specific question that might benefit from future users finding it
* Good for clarifications about features or behavior

## 📚 Documentation

**Primary documentation**:
* [README.md](https://github.com/nagual2/openwrt-captive-monitor/blob/main/README.md) - Installation, configuration,
and basic usage
* [Extended documentation](docs/) - Advanced troubleshooting and deployment guides
* [CHANGELOG.md](https://github.com/nagual2/openwrt-captive-monitor/blob/main/CHANGELOG.md) - Version history and
release notes

**Configuration reference**:
* Default configuration in `/etc/config/captive-monitor` after installation
* Command-line help: `openwrt_captive_monitor --help`

## 🆘 Troubleshooting Common Issues

### Service won't start
```bash
## Check service status
/etc/init.d/captive-monitor status

## View logs
logread | grep captive-monitor

## Test configuration
uci show captive-monitor
```

### Package installation issues
```bash
## Check package dependencies
opkg depends openwrt-captive-monitor

## Verify package integrity
opkg verify openwrt-captive-monitor
```

### Network connectivity problems
```bash
## Test manually in oneshot mode
openwrt_captive_monitor --mode oneshot --verbose

## Check DNS resolution
nslookup google.com
```

## 🏗️ Contributing

Found a bug you want to fix or have a feature idea? Check out our [Contributing
Guide](https://github.com/nagual2/openwrt-captive-monitor/blob/main/CONTRIBUTING.md) for:

* Development setup instructions
* Code style and testing requirements
* Pull request process
* Branch protection and review policies

## 🔒 Security Issues

**Do NOT report security vulnerabilities in public issues or discussions.**

Use our private disclosure channels:
* [GitHub Security Advisory](https://github.com/nagual2/openwrt-captive-monitor/security/advisories/new) (preferred)
* Email: [security@nagual2.com](mailto:security@nagual2.com)

See our [Security Policy](https://github.com/nagual2/openwrt-captive-monitor/blob/main/.github/SECURITY.md) for details
on responsible disclosure.

## 📋 Feature Requests

**Where to file**: [GitHub
Issues](https://github.com/nagual2/openwrt-captive-monitor/issues/new?assignees=&labels=enhancement&template=feature_request.md)

**Before requesting**:
1. Search existing [feature
requests](https://github.com/nagual2/openwrt-captive-monitor/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement)
2. Consider if this is a core feature that benefits all users
3. Think about edge cases and implementation complexity

**What to include**:
* Clear problem statement
* Proposed solution or approach
* Use case and benefits
* Alternative approaches considered

## 🤝 Community Support

This project is maintained by volunteers and community contributors. Response times vary based on maintainers'
availability:

* **Bug reports**: Typically reviewed within 1-2 weeks
* **Feature requests**: Evaluated during roadmap planning
* **Questions**: Community-driven, response times vary

For urgent production issues, consider:
* Rolling back to a previous stable version
* Consulting the OpenWrt community forums
* Seeking professional OpenWrt support services

## 📞 Contact Information

**Project maintainers**: See
[CODEOWNERS](https://github.com/nagual2/openwrt-captive-monitor/blob/main/.github/CODEOWNERS)

**Email**: For security issues only, use [security@nagual2.com](mailto:security@nagual2.com)

**Repository**: https://github.com/nagual2/openwrt-captive-monitor

---

Thank you for using openwrt-captive-monitor! Your feedback and contributions help make this project better for everyone.
