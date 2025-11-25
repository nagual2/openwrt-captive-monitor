# Requirements Document

## Introduction

This document specifies requirements for fixing GitHub Actions CI/CD pipeline failures in the openwrt-captive-monitor project. The failures occur during package building with OpenWrt SDK due to shell script formatting checks and IPK package verification issues.

## Glossary

- **OpenWrt SDK**: Software Development Kit for building OpenWrt packages
- **IPK Package**: OpenWrt package format (similar to Debian's .deb)
- **shfmt**: Shell script formatter tool
- **GitHub Actions**: CI/CD platform integrated with GitHub
- **SDK Action**: GitHub Action (openwrt/gh-action-sdk) that builds packages using OpenWrt SDK in Docker containers

## Requirements

### Requirement 1

**User Story:** As a developer, I want the CI pipeline to successfully build packages, so that I can verify my changes don't break the build.

#### Acceptance Criteria

1. WHEN the CI workflow runs THEN the system SHALL complete package builds without formatting check errors
2. WHEN building inside the SDK Docker container THEN the system SHALL skip shell script format validation for init scripts
3. WHEN the build completes THEN the system SHALL produce valid IPK packages
4. WHEN format checks are disabled THEN the system SHALL still build packages correctly
5. WHEN the SDK action runs THEN the system SHALL handle the absence of git repository gracefully

### Requirement 2

**User Story:** As a developer, I want the package verification script to work with modern IPK formats, so that I can validate built packages.

#### Acceptance Criteria

1. WHEN verifying an IPK package THEN the system SHALL detect whether it uses tar.gz or ar archive format
2. WHEN the IPK uses tar.gz format THEN the system SHALL extract it as a tar.gz archive
3. WHEN the IPK uses ar format THEN the system SHALL extract it as an ar archive
4. WHEN extraction succeeds THEN the system SHALL validate the package contents
5. WHEN the package format is unexpected THEN the system SHALL report a clear error message

### Requirement 3

**User Story:** As a developer, I want clear error messages when builds fail, so that I can quickly identify and fix issues.

#### Acceptance Criteria

1. WHEN a build fails THEN the system SHALL output the specific error that caused the failure
2. WHEN format checks fail THEN the system SHALL indicate which files need formatting
3. WHEN package verification fails THEN the system SHALL show what validation step failed
4. WHEN the SDK action fails THEN the system SHALL preserve build logs for debugging
5. WHEN errors occur THEN the system SHALL exit with appropriate non-zero exit codes
