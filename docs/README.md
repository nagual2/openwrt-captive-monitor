# Documentation Index

Welcome to the openwrt-captive-monitor documentation! This index provides quick access to the most important documents, organized by topic.

**For a comprehensive narrative overview, see [index.md](index.md).**

---

## 🚀 Getting Started

### For End Users
- [Quick Start Guide](usage/quick-start.md) - Get up and running in minutes
- [Installation Guide](usage/installation.md) - Choose between prebuilt packages or SDK builds
- [Basic Configuration](configuration/basic-config.md) - Essential UCI settings to get started

### For Developers
- [Contributing Guide](contributing/CONTRIBUTING.md) - Development guidelines and workflow
- [Development Setup](setup/CI_MODERNIZATION_2025.md) - Setting up your development environment

---

## 📚 User Documentation

### Configuration and Setup
- [Configuration Reference](configuration/reference.md) - Complete UCI options, environment variables, and CLI flags
- [Advanced Configuration](configuration/advanced-config.md) - Environment variables and CLI flags
- [Captive Portal Walkthrough](guides/captive-portal-walkthrough.md) - End-to-end deployment example

### Usage and Troubleshooting
- [Troubleshooting Guide](guides/troubleshooting.md) - Common issues and solutions
- [Oneshot Recovery Mode](guides/oneshot-recovery.md) - Manual connectivity recovery
- [FAQ](project/faq.md) - Frequently asked questions

### Architecture and Design
- [Architecture Overview](guides/architecture.md) - System design and components
- [Virtualization Guide](guides/virtualization.md) - VM-based testing
- [Virtualized Testing Guide](guides/virtualized-testing.md) - Comprehensive testing strategy

---

## 🏗️ Development Documentation

### Build and Packaging
- [Packaging Overview](packaging.md) - Complete packaging workflow and automation
- [Package Details](PACKAGES.md) - Package structure and components
- [Package Build Process](PACKAGE_BUILD_PROCESS_AND_MANIFEST.md) - Build process details
- [Quick Build Summary](PACKAGE_BUILD_QUICK_SUMMARY.md) - Quick reference for builds
- [SDK Build Workflow](guides/sdk-build-workflow.md) - OpenWrt SDK-based CI/CD pipeline
- [Build System Analysis](BUILD_SYSTEM_ROOT_CAUSES_AND_TARGET_FLOW.md) - Root causes and target flow

### Testing and Quality
- [Test Plan](project/test-plan.md) - Testing procedures and validation
- [Release Checklist](project/release-checklist.md) - Step-by-step release process

### Project Management
- [Project Management](project/management.md) - Semantic versioning and release cadence
- [Branches and Merge Policy](project/BRANCHES_AND_MERGE_POLICY.md) - Git workflow and branch strategy
- [Backlog](project/backlog.md) - Feature roadmap and priorities
- [Package Management](project/packages.md) - Build and distribution details

---

## 🔄 CI/CD and Workflows

### Workflow Documentation
- [CI Workflow Overview](ci/CI_WORKFLOW_SIMPLIFIED.md) - Simplified workflow reference
- [GitHub Actions Audit](ci/GITHUB_ACTIONS_WORKFLOWS_AUDIT.md) - Complete workflow audit

### OpenWrt SDK Validation
- [SDK Validation Implementation](ci/CI_SDK_VALIDATION_IMPLEMENTATION.md) - Validation strategy
- [SDK Validation Report (Russian)](ci/SDK_VALIDATION_REPORT_RU.md) - Detailed validation report
- [SDK Validation Troubleshooting (Russian)](ci/CI_SDK_VALIDATION_TROUBLESHOOTING_RU.md) - Troubleshooting guide

### Package Artifacts
- [Package Artifact Staging](ci/package-artifact-staging.md) - Artifact handling and staging
- [IPK Version Validation](ci/ipk-version-validation.md) - Version validation rules

### Implementation Details
- [Pipe Guards Implementation](ci/PIPE_GUARDS_IMPLEMENTATION.md) - Shell script safety features

---

## 🔒 Security

### Security Policy and Practices
- [Security Policy](../.github/SECURITY.md) - Security policy and vulnerability reporting
- [Support Documentation](../.github/SUPPORT.md) - Getting help and support

### Security Scanning
- [Security Scanning Overview](SECURITY_SCANNING.md) - Automated security scanning infrastructure
- [Security Scanning Implementation](security/SECURITY_SCANNING_IMPLEMENTATION.md) - Implementation details
- [Security Audit Report](security/SECURITY_AUDIT_REPORT.md) - Comprehensive security audit
- [Security Cleanup Summary](security/SECURITY_CLEANUP_SUMMARY.md) - Cleanup documentation

---

## 📦 Release and Deployment

### Release Documentation
- [Release Process](release/RELEASE_PROCESS.md) - Detailed release process (Legacy semantic versioning)
- [Auto Version Tag](release/AUTO_VERSION_TAG.md) - Date-based automatic versioning (Active)
- [Changelog](release/CHANGELOG.md) - Version history and release notes

---

## 📋 Setup and Configuration

### Development Tools
- [CI Modernization](setup/CI_MODERNIZATION_2025.md) - 2025 CI/CD modernization updates
- [Implementation Notes](setup/IMPLEMENTATION_NOTES.md) - Implementation details
- [Implementation Summary](setup/IMPLEMENTATION_SUMMARY.md) - Quick implementation summary
- [Workflow Parsing](setup/PARSE_WORKFLOWS_IMPLEMENTATION.md) - Workflow parsing scripts
- [Toolchain Initialization Fix](setup/TOOLCHAIN_INITIALIZATION_FIX.md) - Toolchain setup

---

## 🎯 Contributing

### Community and Contribution
- [Contributing Guide](contributing/CONTRIBUTING.md) - Development guidelines and pull request process
- [Code of Conduct](contributing/CODE_OF_CONDUCT.md) - Community guidelines and expectations
- [Contribution Resources](contributing/README.md) - Contribution templates and resources

### Triaging and Project Management
- [PR Triage](project/PR_TRIAGE.md) - Pull request triage process
- [Triage Documentation](triage/README.md) - Issue triage and labeling
- [Triage Templates](triage/TEMPLATES_AND_LABELS.md) - Issue and PR templates

---

## 📊 Reports and Analysis

### Reports Index
- [Reports Overview](reports/README.md) - Index of all reports and analysis
- [Analysis Index](reports/ANALYSIS_INDEX.md) - Comprehensive analysis reports
- [Diagnostics Index](reports/DIAGNOSTICS_INDEX.md) - Diagnostic reports

---

## 📖 Reference Documentation

### Additional Resources
- [Auto Version Migration](AUTO_VERSION_MIGRATION.md) - Version migration documentation
- [SDK CDN Mirror](sdk-cdn-mirror.md) - SDK mirror and CDN configuration
- [Version History](BACKLOG.md) - Historical backlog entries
- [Workflow Diagnostics](WORKFLOW_DIAGNOSTICS.md) - Diagnostic reference

### Windows Build Documentation
- [Windows Build Instructions](project/BUILD_WINDOWS.md) - Building on Windows

### Migrated Documentation
- [Release Please Troubleshooting](project/RELEASE_PLEASE_TROUBLESHOOTING.md) - Release-please specific issues

---

## 🗂️ Documentation Organization

This documentation is organized into the following directories:

| Directory | Purpose |
|-----------|---------|
| `ci/` | CI/CD workflows and automation documentation |
| `configuration/` | Configuration guides and references |
| `contributing/` | Contribution and development guidelines |
| `guides/` | How-to guides and walkthroughs |
| `project/` | Project management and planning |
| `release/` | Release process and versioning |
| `reports/` | Analysis and diagnostic reports |
| `security/` | Security policies and scanning |
| `setup/` | Development environment setup |
| `triage/` | Issue triage and management |
| `usage/` | User-facing documentation |

---

## 🔍 Quick Navigation

| I want to... | See... |
|-------------|--------|
| Get started quickly | [Quick Start](usage/quick-start.md) |
| Configure the service | [Configuration Reference](configuration/reference.md) |
| Fix an issue | [Troubleshooting](guides/troubleshooting.md) |
| Contribute code | [Contributing Guide](contributing/CONTRIBUTING.md) |
| Understand the build | [Build System](BUILD_SYSTEM_ROOT_CAUSES_AND_TARGET_FLOW.md) |
| Deploy to production | [Release Checklist](project/release-checklist.md) |
| Set up testing | [Virtualized Testing](guides/virtualized-testing.md) |
| Configure CI/CD | [CI Workflow](ci/CI_WORKFLOW_SIMPLIFIED.md) |
| Report a security issue | [Security Policy](../.github/SECURITY.md) |
| Get help | [Support](../.github/SUPPORT.md) |

---

## 📞 Getting Help

- 💬 [GitHub Discussions](https://github.com/nagual2/openwrt-captive-monitor/discussions) - Ask questions and discuss
- 🐛 [GitHub Issues](https://github.com/nagual2/openwrt-captive-monitor/issues) - Report bugs and request features
- 🔒 [Security Advisory](https://github.com/nagual2/openwrt-captive-monitor/security/advisories) - Report security issues privately
- 📚 [Support Documentation](../.github/SUPPORT.md) - Support channels and resources

---

**Last updated:** 2025-11-18
