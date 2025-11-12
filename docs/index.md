# openwrt-captive-monitor Documentation

Welcome to the comprehensive documentation for **openwrt-captive-monitor**, a lightweight OpenWrt helper that monitors WAN connectivity, detects captive portals, and temporarily intercepts LAN DNS/HTTP traffic to facilitate client authentication.

## 📚 Documentation Structure

### 🚀 Getting Started
- [Quick Start Guide](usage/quick-start.md) - Get up and running in minutes
- [Installation Guide](usage/installation.md) - Prebuilt packages vs SDK builds
- [Basic Configuration](configuration/basic-config.md) - Essential UCI settings

### 📖 User Guides
- [Captive Portal Walkthrough](guides/captive-portal-walkthrough.md) - End-to-end example
- [Oneshot Recovery Mode](guides/oneshot-recovery.md) - Manual connectivity recovery
- [Advanced Configuration](configuration/advanced-config.md) - Environment variables and CLI flags
- [Troubleshooting](guides/troubleshooting.md) - Common issues and solutions

### ⚙️ Reference
- [Configuration Reference](configuration/reference.md) - Complete UCI options, environment variables, and CLI flags
- [FAQ](project/faq.md) - Frequently asked questions
- [Architecture Overview](guides/architecture.md) - System design and components

### 🏗️ Project
- [Project Management](project/management.md) - Semantic versioning, release cadence, and project boards
- [Contributing](../CONTRIBUTING.md) - Development guidelines and pull request process
- [Security](../.github/SECURITY.md) - Security policy and vulnerability reporting
- [Support](../.github/SUPPORT.md) - Get help and community resources

### 📋 Development
- [Release Checklist](project/release-checklist.md) - Step-by-step release process
- [Test Plan](project/test-plan.md) - Testing procedures and validation
- [Virtualization Guide](guides/virtualization.md) - VM-based end-to-end testing
- [Virtualized Testing Guide](guides/virtualized-testing.md) - VM-based testing strategy and automation
- [SDK Build Workflow](guides/sdk-build-workflow.md) - OpenWrt SDK-based CI/CD pipeline
- [Build System Root Causes and Target Flow](BUILD_SYSTEM_ROOT_CAUSES_AND_TARGET_FLOW.md) - Historical failures, root causes, and future workflow
- [Backlog](project/backlog.md) - Feature roadmap and priorities
- [Package Management](project/packages.md) - Build and distribution details
- [Packaging and Distribution](packaging.md) - Complete packaging workflow and automation

## 🔗 Quick Links

- **Latest Release**: [GitHub Releases](https://github.com/nagual2/openwrt-captive-monitor/releases)
- **Package Repository**: [OpenWrt Feed](https://github.com/nagual2/openwrt-captive-monitor/releases)
- **Issue Tracker**: [GitHub Issues](https://github.com/nagual2/openwrt-captive-monitor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/nagual2/openwrt-captive-monitor/discussions)

## 📖 About This Documentation

This documentation is organized to serve both end-users who want to deploy and configure the captive monitor, as well as developers who want to contribute to the project. The markdown files can be viewed directly on GitHub or any markdown viewer.

For the most up-to-date information, always refer to the [main repository](https://github.com/nagual2/openwrt-captive-monitor).
