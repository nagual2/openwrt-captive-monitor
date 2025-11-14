# Security Documentation

This section contains all security-related documentation for the openwrt-captive-monitor project.

## 🔒 Security Reports and Analysis

### Security Audits
- [Security Audit Report](SECURITY_AUDIT_REPORT.md) - Comprehensive security audit findings
- [Security Audit Removal Summary](SECURITY_AUDIT_REMOVAL_SUMMARY.md) - Security audit cleanup documentation
- [Security Cleanup Summary](SECURITY_CLEANUP_SUMMARY.md) - Security cleanup procedures and results

### Security Scanning
- [Security Scanning Implementation](SECURITY_SCANNING_IMPLEMENTATION.md) - Implementation of automated security scanning

### Sensitive Information
- [Sensitive Info Removal Report](SENSITIVE_INFO_REMOVAL_REPORT.md) - Documentation of sensitive information removal

## 🛡️ Security Policies and Procedures

### Security Policy
- [Security Policy](../../.github/SECURITY.md) - Official security policy and vulnerability reporting guidelines

### Security Scanning Infrastructure
- [Security Scanning Documentation](../SECURITY_SCANNING.md) - Comprehensive security scanning infrastructure documentation

## 🚨 Reporting Security Issues

**Do NOT report security vulnerabilities in public issues or discussions.**

Use our private disclosure channels:
- [GitHub Security Advisory](https://github.com/nagual2/openwrt-captive-monitor/security/advisories/new) (preferred)
- Email: [security@nagual2.com](mailto:security@nagual2.com)

## 📋 Security SLA

- **Response time**: 7 business days
- **Critical vulnerabilities**: Patch within 30 days
- **High severity**: Patch within 60 days
- **Medium/Low**: Addressed in next scheduled release

## 🔍 Security Features

The project implements multiple security measures:

- **Automated Security Scanning** - ShellCheck, Trivy, Dependency Review
- **Dependency Management** - Automated dependency updates and vulnerability scanning
- **Secret Scanning** - GitHub secret scanning with push protection
- **Branch Protection** - Enforced policies for main branch protection
- **Code Review** - Required PR reviews for all changes

## 📚 Related Documentation

- [Contributing Guide](../contributing/CONTRIBUTING.md) - Development security guidelines
- [Release Process](../release/RELEASE_PROCESS.md) - Security considerations in releases
- [Support Documentation](../../.github/SUPPORT.md) - Security support channels

---

**Last updated:** 2025-11-14