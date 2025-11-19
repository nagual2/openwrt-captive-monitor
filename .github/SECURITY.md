# Security Policy

---

## 🌐 Language / Язык

**English** | [Русский](#политика-безопасности)

---

## Supported Versions

Only the latest released version of openwrt-captive-monitor receives security updates and patches. Users are strongly encouraged to upgrade to the most recent version to ensure they have the latest security fixes.

| Version | Supported |
|---------|------------------|
| Latest release | ✅ |
| Previous versions | ❌ |

## Automated Security Scanning

This repository employs multiple automated security scanning tools to identify vulnerabilities early:

### Active Security Tools

| Tool | Coverage | Runs On | Expected Duration | Status Check Name |
|------|----------|---------|-------------------|-------------------|
| **ShellCheck Security** | Shell scripts (Bash, POSIX sh) | PRs, main branch, weekly (Tue) | ~5-10 min | `ShellCheck Security Analysis` |
| **Dependency Review** | GitHub dependencies | PRs only | ~2-5 min | `Dependency Review` |
| **Trivy** | Vulnerabilities, misconfigs | PRs, main branch, weekly (Tue) | ~5-10 min | `Trivy Security Scan` |

### Branch Protection Requirements

For production workflows, we recommend configuring branch protection rules on `main` to require the following status checks:

**Required Security Checks:**

* `ShellCheck Security Analysis`
* `Dependency Review` (for PRs)
* `Trivy Security Scan`

These checks help prevent vulnerabilities from being merged into the main branch.

### Branch Protection Policy

The `main` branch is protected with the following rules to ensure code quality and security:

**Merge Requirements:**
- ✅ Pull request reviews required (minimum 1 approval)
- ✅ All status checks must pass (linting, testing, and all security scanners)
- ✅ Branches must be up to date before merging
- ✅ Linear history required (no merge commits)
- ✅ Stale reviews are dismissed when new commits are pushed
- ✅ All conversations must be resolved before merge
- ❌ Force pushes prohibited
- ❌ Branch deletions prohibited

**Status Checks Required:**
- All CI checks: `Lint (shfmt)`, `Lint (shellcheck)`, `Lint (markdownlint)`, `Lint (actionlint)`, `Test`
- All security checks: `ShellCheck Security Analysis`, `Dependency Review`, `Trivy Security Scan`

These protections are configured in [`.github/settings.yml`](settings.yml) and enforced by GitHub branch protection rules.

### Security Features Enabled

The repository has the following GitHub security and analysis features enabled:

- **Dependency Graph**: Automatically tracks repository dependencies
- **Dependabot Alerts**: Notifies maintainers of known vulnerabilities in dependencies
- **Dependabot Security Updates**: Automatically opens PRs to patch known security vulnerabilities
- **Secret Scanning**: Detects accidentally committed secrets (API keys, tokens, etc.)
- **Secret Scanning Push Protection**: Prevents pushing files containing detected secrets to the repository

These features work in conjunction with the automated scanning pipelines to provide multiple layers of security protection.

### Security Scan Results

All security scan results are automatically uploaded to the [Security tab](../../security/code-scanning) in the GitHub repository. Results are categorized by scanner for easy triaging.

**Viewing Results:**

1. Navigate to the **Security** tab in the repository
2. Click on **Code scanning** in the left sidebar
3. Filter by tool, branch, or severity level
4. Click on individual alerts for details and remediation guidance

### Handling False Positives

If a security alert is a false positive:

1. **Investigate thoroughly**: Ensure the alert is genuinely a false positive and not a real vulnerability
2. **Document the reason**: Add a comment to the alert explaining why it's a false positive
3. **Dismiss the alert**: Use GitHub's dismiss feature with an appropriate reason:
   * "Won't fix" - For accepted risks in non-critical code paths
   * "False positive" - For scanner errors or misidentifications
   * "Used in tests" - For test code that intentionally uses insecure patterns
4. **Suppress at source** (if applicable):
   * For ShellCheck: Add `# shellcheck disable=SC####` comment
5. **Document in code**: Include a comment explaining the suppression

**Example Suppression:**

```bash
# ShellCheck SC2086 disabled: intentional word splitting for argument list
# shellcheck disable=SC2086
eval "$command" $args
```

### Remediation Workflow

When a security alert is raised:

1. **Triage** (within 48 hours):
   * Review the alert in the Security tab
   * Assess severity and impact
   * Assign to appropriate team member

2. **Investigate** (within 1 week for HIGH/CRITICAL):
   * Reproduce the issue if possible
   * Determine root cause
   * Identify affected versions

3. **Remediate**:
   * **Critical**: Fix immediately, issue patch release
   * **High**: Fix in next release (within 2 weeks)
   * **Medium**: Fix in upcoming minor release
   * **Low**: Fix in next major release or backlog

4. **Verify**:
   * Ensure fix resolves the alert
   * Verify no regressions introduced
   * Update tests to prevent recurrence

5. **Document**:
   * Update CHANGELOG with security fix note
   * Create GitHub Security Advisory if warranted
   * Close the alert with fix reference

### Scanner Configuration

#### ShellCheck Security

* **Output Format**: SARIF (for GitHub Security integration)
* **Target**: All `.sh` files and shell scripts
* **Severity Filter**: Warnings and errors only

#### Dependency Review

* **Fail Severity**: Moderate and above
* **License Restrictions**: GPL-3.0, AGPL-3.0 (denied)
* **Snapshot Warnings**: Retry enabled

#### Trivy

* **Scan Types**: Vulnerabilities and misconfigurations
* **Severity**: CRITICAL, HIGH, MEDIUM
* **Scanners**: vuln, misconfig
* **Ignore Unfixed**: Yes (reduces noise from unfixable vulnerabilities)

### Disabling Security Checks

Security checks should **not** be disabled except in exceptional circumstances. Branch protection rules on `main` require all security checks to pass before merging, so bypassing them requires:

1. **Maintainer approval**: Get explicit approval from a repository maintainer
2. **Branch protection override**: Only repository administrators can override branch protection
3. **Documentation**: Document the reason in the PR description and commit message
4. **Follow-up action**: Create a follow-up issue to address the security concern
5. **Audit trail**: Use `[security skip: reason]` in commit message for traceability

**Important**: The `main` branch has branch protection enabled that requires **all status checks to pass before merging**. If a security check fails:
- The pull request cannot be merged by anyone except repository administrators
- Even administrators should avoid bypassing security checks
- Maintainers should instead investigate and fix the security issue
- If you have a legitimate reason to skip a check, discuss it with maintainers first

These protections ensure that no vulnerable code reaches the main branch and that all changes are properly reviewed.

## Reporting a Vulnerability

The openwrt-captive-monitor team takes security vulnerabilities seriously. We appreciate your efforts to responsibly disclose your findings.

If you discover a security vulnerability, please report it privately before disclosing it publicly.

### Reporting Channels

**Preferred method**: Use [GitHub's private vulnerability reporting](https://github.com/nagual2/openwrt-captive-monitor/security/advisories/new)

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

We aim to respond to security reports within **7 business days** and provide a detailed analysis and timeline for addressing the vulnerability.

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

We thank all researchers who help us keep openwrt-captive-monitor secure. Your responsible disclosure helps protect the entire OpenWrt community.

---

# Политика Безопасности

## Поддерживаемые Версии

Только последняя выпущенная версия openwrt-captive-monitor получает обновления безопасности и патчи. Пользователям настоятельно рекомендуется обновляться до последней версии, чтобы обеспечить наличие последних исправлений безопасности.

| Версия | Поддерживается |
|---------|------------------|
| Последний выпуск | ✅ |
| Предыдущие версии | ❌ |

## Сообщение об Уязвимости

Команда openwrt-captive-monitor серьезно относится к уязвимостям безопасности. Мы ценим ваши усилия по ответственному раскрытию найденных проблем.

Если вы обнаружили уязвимость безопасности, пожалуйста, сообщите о ней частным образом перед публичным раскрытием.

### Каналы Сообщения

**Предпочтительный метод**: Используйте [приватное сообщение об уязвимости GitHub](https://github.com/nagual2/openwrt-captive-monitor/security/advisories/new)

### Что Включить в Ваше Сообщение

Пожалуйста, включите как можно больше из следующей информации, чтобы помочь нам лучше понять и оценить ваше сообщение:

* **Тип проблемы** (например, переполнение буфера, SQL-инъекция, межсайтовый скриптинг и т.д.)
* **Полные пути к исходным файлам, связанным с проявлением проблемы**
* **Местоположение затронутого исходного кода** (тег/ветка/коммит или прямой URL)
* **Любая специальная конфигурация, необходимая для воспроизведения проблемы**
* **Пошаговые инструкции для воспроизведения проблемы**
* **Proof-of-concept или эксплойт-код** (если возможно)
* **Влияние проблемы, включая то, как злоумышленник может ее использовать**

### Сроки Ответа

Мы стремимся отвечать на сообщения о безопасности в течение **7 рабочих дней** и предоставлять детальный анализ и график устранения уязвимости.

### Ожидания по Исправлению

* **Критические уязвимости**: Цель - выпустить патч в течение 30 дней после раскрытия
* **Уязвимости высокой степени серьезности**: Цель - выпустить патч в течение 60 дней после раскрытия
* **Уязвимости средней/низкой степени серьезности**: Будут устранены в следующем запланированном выпуске

### Политика Раскрытия

* Мы будем координировать раскрытие с вами, чтобы обеспечить решение вашей проблемы перед публичным раскрытием
* Как только исправление будет доступно, мы публично раскроем уязвимость (с указанием вашего авторства, если вы этого желаете)
* Мы можем запросить дополнительное время, если уязвимость требует сложной координации с вышестоящими проектами OpenWrt

### Рекомендации по Безопасности для Пользователей

* Поддерживайте вашу установку openwrt-captive-monitor обновленной до последней версии
* Следуйте рекомендациям по безопасности OpenWrt для усиления защиты роутера
* Регулярно проверяйте и обновляйте прошивку роутера и зависимости
* Следите за [выпусками GitHub](https://github.com/nagual2/openwrt-captive-monitor/releases) для объявлений о безопасности

### Благодарности за Безопасность

Мы благодарим всех исследователей, которые помогают нам поддерживать безопасность openwrt-captive-monitor. Ваше ответственное раскрытие помогает защитить все сообщество OpenWrt.
