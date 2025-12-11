# Security Documentation

---

## 🌐 Language / Язык

**English** | [Русский](README.ru.md)

---

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

Use our private disclosure channel:
- [GitHub Security Advisory](https://github.com/nagual2/openwrt-captive-monitor/security/advisories/new) (preferred)

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

---

# Русский

---

## 🌐 Язык

[English](#security-documentation) | **Русский**

---

# Документация по безопасности

Этот раздел содержит всю документацию, связанную с безопасностью проекта openwrt-captive-monitor.

## 🔒 Отчёты и анализ безопасности

### Аудиты безопасности
- [Отчёт по аудиту безопасности](SECURITY_AUDIT_REPORT.md) — Подробные результаты аудита безопасности
- [Сводка по удалению аудита безопасности](SECURITY_AUDIT_REMOVAL_SUMMARY.md) — Документация по очистке артефактов аудита безопасности
- [Сводка по очистке безопасности](SECURITY_CLEANUP_SUMMARY.md) — Процедуры и результаты очистки по безопасности

### Сканирование безопасности
- [Реализация сканирования безопасности](SECURITY_SCANNING_IMPLEMENTATION.md) — Реализация автоматизированного сканирования безопасности

### Конфиденциальная информация
- [Отчёт об удалении конфиденциальной информации](SENSITIVE_INFO_REMOVAL_REPORT.md) — Документация по удалению конфиденциальных данных

## 🛡️ Политики и процедуры безопасности

### Политика безопасности
- [Политика безопасности](../../.github/SECURITY.md) — Официальная политика безопасности и рекомендации по сообщению об уязвимостях

### Инфраструктура сканирования безопасности
- [Документация по сканированию безопасности](../SECURITY_SCANNING.md) — Подробная документация по инфраструктуре сканирования безопасности

## 🚨 Сообщение о проблемах безопасности

**НЕ сообщайте об уязвимостях безопасности в публичных задачах или обсуждениях.**

Используйте наш закрытый канал раскрытия информации:
- [GitHub Security Advisory](https://github.com/nagual2/openwrt-captive-monitor/security/advisories/new) (предпочтительно)

## 📋 SLA по безопасности

- **Время ответа**: 7 рабочих дней
- **Критические уязвимости**: выпуск патча в течение 30 дней
- **Высокая критичность**: выпуск патча в течение 60 дней
- **Средняя/низкая критичность**: исправляются в следующем запланированном релизе

## 🔍 Механизмы безопасности

Проект реализует несколько уровней защиты:

- **Автоматизированное сканирование безопасности** — ShellCheck, Trivy, Dependency Review
- **Управление зависимостями** — Автоматическое обновление зависимостей и сканирование на уязвимости
- **Сканирование секретов** — Сканирование секретов GitHub с защитой при push
- **Защита ветки main** — Строгие правила защиты ветки `main`
- **Код‑ревью** — Обязательные обзоры PR для всех изменений

## 📚 Связанная документация

- [Руководство по вкладу](../contributing/CONTRIBUTING.md) — Рекомендации по разработке с учётом безопасности
- [Процесс релизов](../release/RELEASE_PROCESS.md) — Вопросы безопасности в процессе релиза
- [Документация по поддержке](../../.github/SUPPORT.md) — Каналы поддержки по вопросам безопасности
