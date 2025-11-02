# Security Policy

## Supported Versions

Only the latest released version of openwrt-captive-monitor receives security updates and patches. Users are strongly
encouraged to upgrade to the most recent version to ensure they have the latest security fixes.

| Version | Supported |
|---------|------------------|
| Latest release | ✅ |
| Previous versions | ❌ |

## Reporting a Vulnerability

The openwrt-captive-monitor team takes security vulnerabilities seriously. We appreciate your efforts to responsibly
disclose your findings.

If you discover a security vulnerability, please report it privately before disclosing it publicly.

### Reporting Channels

**Preferred method**: Use [GitHub's private vulnerability
reporting](https://github.com/nagual2/openwrt-captive-monitor/security/advisories/new)

**Alternative**: Email the maintainers directly at [security@nagual2.com](mailto:security@nagual2.com)

### What to Include in Your Report

Please include as much of the following information as possible to help us better understand and assess your report:

* **Type of issue** (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
* **Full paths of source file(s) related to the manifestation of the issue**
* **Location of the affected source code** (tag/branch/commit or direct URL)
* **Any special configuration required to reproduce the issue**
* **Step-by-step instructions to reproduce the issue**
* **Proof-of-concept or exploit code** (if possible)
* **Impact of the issue, including how an attacker might exploit it**

### Response Timeline

We aim to respond to security reports within **7 business days** and provide a detailed analysis and timeline for
addressing the vulnerability.

### Remediation Expectations

* **Critical vulnerabilities**: Aim to release a patch within 30 days of disclosure
* **High severity vulnerabilities**: Aim to release a patch within 60 days of disclosure
* **Medium/Low severity vulnerabilities**: Will be addressed in the next scheduled release

### Disclosure Policy

* We will coordinate disclosure with you to ensure your report is addressed before public disclosure
* Once a fix is available, we will publicly disclose the vulnerability (with credit to you, if desired)
* We may request additional time if the vulnerability requires complex coordination with OpenWrt upstream projects

### Security Best Practices for Users

* Keep your openwrt-captive-monitor installation updated to the latest version
* Follow OpenWrt security best practices for router hardening
* Regularly review and update router firmware and dependencies
* Monitor the [GitHub releases](https://github.com/nagual2/openwrt-captive-monitor/releases) for security announcements

### Security Acknowledgments

We thank all researchers who help us keep openwrt-captive-monitor secure. Your responsible disclosure helps protect the
entire OpenWrt community.
