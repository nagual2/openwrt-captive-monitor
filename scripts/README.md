# Scripts Directory

Эта директория содержит вспомогательные скрипты для управления проектом и тестовыми средами.

## Скрипты управления WiFi точкой доступа (Minisforum)

### change-ap-password.sh
**Назначение:** Интерактивная смена пароля WiFi точки доступа на Minisforum Z83-F

**Расположение на Minisforum:** `/usr/local/bin/change-ap-password.sh`

**Использование:**
```bash
# На Minisforum
sudo /usr/local/bin/change-ap-password.sh
```

**Особенности:**
- Интерактивный ввод пароля (скрытый)
- Двойное подтверждение пароля
- Автоматическое создание резервных копий
- Валидация длины пароля (8-63 символа)

**Документация:** [docs/change-ap-password-guide.md](../docs/change-ap-password-guide.md)

### remote-change-ap-password.sh
**Назначение:** Удаленная смена пароля WiFi точки доступа из Windows/WSL

**Использование:**
```bash
# Из Windows PowerShell
wsl bash scripts/remote-change-ap-password.sh
```

**Особенности:**
- Локальный интерактивный ввод пароля
- Удаленное применение через SSH
- Автоматический перезапуск AP
- Безопасная передача пароля через here-document

## Скрипты управления WSL

### convert-to-wsl1.ps1
**Назначение:** Конвертация WSL дистрибутива в WSL 1

**Использование:**
```powershell
.\scripts\convert-to-wsl1.ps1
```

### convert-to-wsl2.ps1
**Назначение:** Конвертация WSL дистрибутива в WSL 2

**Использование:**
```powershell
.\scripts\convert-to-wsl2.ps1
```

### enable-wsl2.ps1
**Назначение:** Включение WSL 2 на Windows

**Использование:**
```powershell
.\scripts\enable-wsl2.ps1
```

### manual-convert-to-wsl1.ps1
**Назначение:** Ручная конвертация в WSL 1 (с подробными инструкциями)

### manual-convert-to-wsl2.ps1
**Назначение:** Ручная конвертация в WSL 2 (с подробными инструкциями)

### disable-hyperv-for-vmware.ps1
**Назначение:** Отключение Hyper-V для совместимости с VMware

**Использование:**
```powershell
.\scripts\disable-hyperv-for-vmware.ps1
```

## Безопасность

### Передача паролей

⚠️ **Важно:** Никогда не передавайте пароли как параметры командной строки!

**Плохо:**
```bash
# ❌ Пароль виден в истории команд и списке процессов
sudo change-password.sh "MyPassword123"
```

**Хорошо:**
```bash
# ✅ Интерактивный ввод (пароль скрыт)
sudo change-password.sh

# ✅ Через here-document для автоматизации
sudo change-password.sh <<EOF
MyPassword123
MyPassword123
EOF
```

### Хранение паролей

- Не коммитить пароли в Git
- Использовать `.env` файлы (добавлены в `.gitignore`)
- Хранить пароли в зашифрованном виде
- Использовать менеджеры паролей

## Добавление новых скриптов

При добавлении новых скриптов:

1. Добавьте shebang в начало файла:
   ```bash
   #!/bin/bash
   # или
   #!/usr/bin/env pwsh
   ```

2. Добавьте описание и использование в комментариях:
   ```bash
   #!/bin/bash
   # Script Name: my-script.sh
   # Description: What this script does
   # Usage: ./my-script.sh [options]
   ```

3. Используйте `set -euo pipefail` для bash скриптов:
   ```bash
   #!/bin/bash
   set -euo pipefail
   ```

4. Сделайте скрипт исполняемым:
   ```bash
   chmod +x scripts/my-script.sh
   ```

5. Обновите этот README с описанием нового скрипта

6. Добавьте документацию в `docs/` если скрипт сложный

## Тестирование скриптов

Перед коммитом проверьте скрипты:

```bash
# Shellcheck для bash скриптов
wsl shellcheck scripts/*.sh

# PSScriptAnalyzer для PowerShell скриптов
Invoke-ScriptAnalyzer -Path scripts/*.ps1

# Запуск в dry-run режиме (если поддерживается)
./scripts/my-script.sh --dry-run
```

## Связанные документы

- [docs/commands_cheatsheet.md](../docs/commands_cheatsheet.md) - Часто используемые команды
- [Minisforum/Docs/Minisforum.md](../Minisforum/Docs/Minisforum.md) - Документация по Minisforum Z83-F
- [docs/wsl_guide.md](../docs/wsl_guide.md) - Руководство по WSL
- [Minisforum/Docs/change-ap-password-guide.md](../Minisforum/Docs/change-ap-password-guide.md) - Руководство по смене пароля AP
