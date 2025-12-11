# openwrt-captive-monitor Support

---

## 🌐 Language / Язык

**English** | [Русский](README.ru.md)

---

# Support

## Getting Help

The openwrt-captive-monitor project provides several channels for getting support, reporting bugs, and asking questions. Choose the most appropriate channel for your needs.

## 🐛 Bug Reports

**Where to file**: [GitHub Issues](https://github.com/nagual2/openwrt-captive-monitor/issues/new?assignees=&labels=bug&template=bug_report.md)

**Before reporting**:
1. Check existing [open issues](https://github.com/nagual2/openwrt-captive-monitor/issues?q=is%3Aissue+is%3Aopen+label%3Abug) to avoid duplicates
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

**GitHub Issues with "question" label**: [Create an issue](https://github.com/nagual2/openwrt-captive-monitor/issues/new?assignees=&labels=question&template=---)
* Use when you have a specific question that might benefit from future users finding it
* Good for clarifications about features or behavior

## 📚 Documentation

**Primary documentation**:
* [README.md](https://github.com/nagual2/openwrt-captive-monitor/blob/main/README.md) - Installation, configuration, and basic usage
* [Extended documentation](docs/) - Advanced troubleshooting and deployment guides
* [CHANGELOG.md](https://github.com/nagual2/openwrt-captive-monitor/blob/main/docs/release/CHANGELOG.md) - Version history and release notes

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

Found a bug you want to fix or have a feature idea? Check out our [Contributing Guide](https://github.com/nagual2/openwrt-captive-monitor/blob/main/docs/contributing/CONTRIBUTING.md) for:

* Development setup instructions
* Code style and testing requirements
* Pull request process
* Branch protection and review policies

## 🔒 Security Issues

**Do NOT report security vulnerabilities in public issues or discussions.**

Use our private disclosure channel:
* [GitHub Security Advisory](https://github.com/nagual2/openwrt-captive-monitor/security/advisories/new) (preferred)

See our [Security Policy](https://github.com/nagual2/openwrt-captive-monitor/blob/main/.github/SECURITY.md) for details on responsible disclosure.

## 📋 Feature Requests

**Where to file**: [GitHub Issues](https://github.com/nagual2/openwrt-captive-monitor/issues/new?assignees=&labels=enhancement&template=feature_request.md)

**Before requesting**:
1. Search existing [feature requests](https://github.com/nagual2/openwrt-captive-monitor/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement)
2. Consider if this is a core feature that benefits all users
3. Think about edge cases and implementation complexity

**What to include**:
* Clear problem statement
* Proposed solution or approach
* Use case and benefits
* Alternative approaches considered

## 🤝 Community Support

This project is maintained by volunteers and community contributors. Response times vary based on maintainers' availability:

* **Bug reports**: Typically reviewed within 1-2 weeks
* **Feature requests**: Evaluated during roadmap planning
* **Questions**: Community-driven, response times vary

For urgent production issues, consider:
* Rolling back to a previous stable version
* Consulting the OpenWrt community forums
* Seeking professional OpenWrt support services

## 📞 Contact Information

**Project maintainers**: See [CODEOWNERS](https://github.com/nagual2/openwrt-captive-monitor/blob/main/.github/CODEOWNERS)

**Repository**: https://github.com/nagual2/openwrt-captive-monitor

---

Thank you for using openwrt-captive-monitor! Your feedback and contributions help make this project better for everyone.

---

# <a id="русский"></a> Поддержка

## Получение помощи

Проект openwrt-captive-monitor предоставляет несколько каналов для получения поддержки, сообщения об ошибках и задавания вопросов. Выберите наиболее подходящий канал для ваших нужд.

## 🐛 Отчёты об ошибках

**Где сообщить**: [GitHub Issues](https://github.com/nagual2/openwrt-captive-monitor/issues/new?assignees=&labels=bug&template=bug_report.md)

**Перед отправкой отчёта**:
1. Проверьте существующие [открытые задачи](https://github.com/nagual2/openwrt-captive-monitor/issues?q=is%3Aissue+is%3Aopen+label%3Abug), чтобы избежать дубликатов
2. Убедитесь, что используете последнюю версию
3. По возможности протестируйте на чистой установке
4. Соберите соответствующие логи и детали конфигурации

**Что включить**:
* Версия OpenWrt и модель устройства
* Версия openwrt-captive-monitor
* Полные сообщения об ошибках и логи
* Шаги для воспроизведения проблемы
* Текущая конфигурация (очищенная от конфиденциальных данных)

## 💬 Вопросы и общее обсуждение

**GitHub Discussions**: [Начать обсуждение](https://github.com/nagual2/openwrt-captive-monitor/discussions/new)
* Используйте для вопросов "как сделать", помощи с конфигурацией и общих обсуждений
* Идеально для устранения неполадок, которые не являются явной ошибкой
* Поддержка сообщества от других пользователей и сопровождающих

**GitHub Issues с меткой "question"**: [Создать задачу](https://github.com/nagual2/openwrt-captive-monitor/issues/new?assignees=&labels=question&template=---)
* Используйте, когда у вас есть конкретный вопрос, который может быть полезен будущим пользователям
* Хорошо подходит для уточнений о функциях или поведении

## 📚 Документация

**Основная документация**:
* [README.md](https://github.com/nagual2/openwrt-captive-monitor/blob/main/README.md) - Установка, конфигурация и базовое использование
* [Расширенная документация](docs/) - Продвинутое устранение неполадок и руководства по развёртыванию
* [CHANGELOG.md](https://github.com/nagual2/openwrt-captive-monitor/blob/main/docs/release/CHANGELOG.md) - История версий и примечания к выпускам

**Справочник по конфигурации**:
* Конфигурация по умолчанию в `/etc/config/captive-monitor` после установки
* Справка командной строки: `openwrt_captive_monitor --help`

## 🆘 Устранение распространённых проблем

### Служба не запускается
```bash
## Проверить статус службы
/etc/init.d/captive-monitor status

## Просмотреть логи
logread | grep captive-monitor

## Проверить конфигурацию
uci show captive-monitor
```

### Проблемы с установкой пакета
```bash
## Проверить зависимости пакета
opkg depends openwrt-captive-monitor

## Проверить целостность пакета
opkg verify openwrt-captive-monitor
```

### Проблемы с сетевым подключением
```bash
## Проверить вручную в режиме одноразового запуска
openwrt_captive_monitor --mode oneshot --verbose

## Проверить разрешение DNS
nslookup google.com
```

## 🏗️ Участие в разработке

Нашли ошибку, которую хотите исправить, или есть идея новой функции? Ознакомьтесь с нашим [Руководством по участию](https://github.com/nagual2/openwrt-captive-monitor/blob/main/docs/contributing/CONTRIBUTING.md), где описаны:

* Инструкции по настройке окружения разработки
* Требования к стилю кода и тестированию
* Процесс создания pull request
* Политики защиты веток и проверки

## 🔒 Вопросы безопасности

**НЕ сообщайте об уязвимостях безопасности в публичных задачах или обсуждениях.**

Используйте наш приватный канал раскрытия информации:
* [GitHub Security Advisory](https://github.com/nagual2/openwrt-captive-monitor/security/advisories/new) (предпочтительно)

Смотрите нашу [Политику безопасности](https://github.com/nagual2/openwrt-captive-monitor/blob/main/.github/SECURITY.md) для подробностей об ответственном раскрытии информации.

## 📋 Запросы функций

**Где подать запрос**: [GitHub Issues](https://github.com/nagual2/openwrt-captive-monitor/issues/new?assignees=&labels=enhancement&template=feature_request.md)

**Перед отправкой запроса**:
1. Поищите существующие [запросы функций](https://github.com/nagual2/openwrt-captive-monitor/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement)
2. Подумайте, является ли это основной функцией, которая принесёт пользу всем пользователям
3. Подумайте о граничных случаях и сложности реализации

**Что включить**:
* Чёткое описание проблемы
* Предлагаемое решение или подход
* Варианты использования и преимущества
* Рассмотренные альтернативные подходы

## 🤝 Поддержка сообщества

Этот проект поддерживается волонтёрами и участниками сообщества. Время ответа зависит от доступности сопровождающих:

* **Отчёты об ошибках**: Обычно рассматриваются в течение 1-2 недель
* **Запросы функций**: Оцениваются при планировании дорожной карты
* **Вопросы**: Поддержка сообщества, время ответа варьируется

Для срочных производственных проблем рассмотрите:
* Откат к предыдущей стабильной версии
* Консультацию на форумах сообщества OpenWrt
* Поиск профессиональных услуг поддержки OpenWrt

## 📞 Контактная информация

**Сопровождающие проекта**: См. [CODEOWNERS](https://github.com/nagual2/openwrt-captive-monitor/blob/main/.github/CODEOWNERS)

**Репозиторий**: https://github.com/nagual2/openwrt-captive-monitor

---

Спасибо за использование openwrt-captive-monitor! Ваши отзывы и вклад помогают сделать этот проект лучше для всех.
