# Объединённое руководство по проекту OpenWrt Captive Monitor для Cascade

## Языковые предпочтения

- Общение с пользователем на русском языке
- Планы, документация и объяснения на русском
- Git commit сообщения только на английском
- Показывать команды перед выполнением для прозрачности

## Приоритет использования команд

### Правило: Нативные Windows команды в первую очередь

**Всегда используй нативные Windows/PowerShell команды когда это возможно, вместо WSL.**

### Доверенные команды из VSCode настроек

#### Git команды:
- git, git *, gh, gh *

#### PowerShell Core:
- pwsh, pwsh *, powershell, powershell *
- Write-Host, Write-Host *, Write-Output *
- Get-Content, Get-Content *, Get-ChildItem, Get-ChildItem *
- Get-Process *, Get-Job *, Get-Date *, Get-PSDrive *, Get-Disk *
- Get-Partition *, Get-Volume *, Get-PartitionSupportedSize *
- Get-WmiObject *, Get-Service *, Set-Content *, Copy-Item *
- Move-Item *, Remove-Item *, New-Item *, Test-Path *, Test-Connection *
- Start-Process *, Start-Sleep *, Start-Job *, Stop-Job *, Receive-Job *, Remove-Job *
- Invoke-WebRequest *, Invoke-Expression *, Select-String *

#### Файловые операции:
- dir, ls *, cat *, type *, echo, echo *, mkdir *, chmod *

#### WSL команды:
- wsl, wsl *, bash *, ssh *

#### Docker:
- docker *

#### Python:
- python, python *, python3, pip *, winget *

#### Build tools:
- sed, shfmt *, yamllint *, curl *, timeout *, act *, icacls *, diskpart *
- Remove-Partition *

#### Проектные скрипты:
- .\fix_ci.ps1, .\fix_ci_v2.ps1, .\fix_ci_v3.ps1, .\fix_trailing_spaces.ps1
- .\docker\sdk\build-and-push-all.ps1 *, .\docker\sdk\build-parallel.ps1 *
- .\monitor-all-builds.ps1 *, .\build-arch.ps1 *

#### Переменные и выражения:
- Все переменные начинающиеся с $: $response *, $targets *, $mirrors *, $env:Path *, и т.д.
- Условные выражения: if *, (Get-Content *
- Массивы: @('ath79-generic', *, @\" *, # *, . *

#### Алиасы:
- gst *, file *, cleanup-dev *, npx *, и другие проектные алиасы

## SSH настройки
- Config file: ~/.ssh/config
- Show login terminal: true
- Remote platforms: openwrt-test (linux), openwrt (linux)
- Dynamic forwarding: false
- Connect timeout: 30s

## Принципы работы

### Основные принципы:
1. **Чёткость и лаконичность** - давать краткие и понятные ответы
2. **Безопасность** - не выполнять потенциально опасные команды без подтверждения
3. **Документирование** - оставлять понятные комментарии в коде
4. **Следование стандартам** - придерживаться стиля кода проекта

### Работа с кодом:
- Перед внесением изменений анализировать контекст
- Делать атомарные коммиты с понятными сообщениями
- Следовать принципам чистого кода
- Документировать сложные участки кода

### Взаимодействие с пользователем:
- Запрашивать уточнения при неоднозначных запросах
- Предлагать несколько вариантов решения, если применимо
- Объяснять сложные концепции простым языком
- Предупреждать о потенциальных рисках
