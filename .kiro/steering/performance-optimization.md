# Оптимизация производительности

## Приоритет использования команд

### Правило: Нативные Windows команды в первую очередь

**Всегда используй нативные Windows/PowerShell команды когда это возможно, вместо WSL.**

WSL добавляет overhead на запуск Linux окружения. Используй WSL только когда нет альтернативы.

## Матрица выбора команд

### ✅ Используй нативные Windows команды:

| Задача | ❌ Не используй WSL | ✅ Используй нативно |
|--------|---------------------|----------------------|
| Git операции | `wsl git status` | `git status` |
| GitHub CLI | `wsl gh pr list` | `gh pr list` |
| Docker | `wsl docker ps` | `docker ps` |
| Файловые операции | `wsl ls -la` | `Get-ChildItem` или `dir` |
| Чтение файлов | `wsl cat file.txt` | `Get-Content file.txt` |
| Копирование | `wsl cp file1 file2` | `Copy-Item file1 file2` |
| Удаление | `wsl rm file` | `Remove-Item file` |
| Проверка файла | `wsl test -f file` | `Test-Path file` |
| Сетевые проверки | `wsl ping host` | `Test-Connection host` |
| Переменные окружения | `wsl echo $PATH` | `$env:PATH` |
| Python | `wsl python script.py` | `python script.py` |
| Curl | `wsl curl url` | `Invoke-WebRequest url` |

### ⚠️ Используй WSL только когда необходимо:

| Задача | Причина |
|--------|---------|
| `wsl ssh host` | SSH клиент в Windows может не быть настроен |
| `wsl bash script.sh` | Bash скрипты требуют Linux окружение |
| `wsl grep pattern file` | Нет прямого аналога в PowerShell |
| `wsl sed 's/old/new/' file` | Нет прямого аналога в PowerShell |
| `wsl awk '{print $1}' file` | Нет прямого аналога в PowerShell |
| `wsl make` | Makefile требует Linux окружение |

## Примеры оптимизации

### ❌ Неоптимально (через WSL):

```powershell
# Проверка статуса git
wsl git status

# Список файлов
wsl ls -la

# Чтение файла
wsl cat VERSION

# Проверка существования файла
wsl test -f package.ipk && echo "exists"

# Docker команды
wsl docker ps
wsl docker images
```

**Проблема:** Каждый вызов WSL запускает Linux окружение (~100-200ms overhead)

### ✅ Оптимально (нативно):

```powershell
# Проверка статуса git
git status

# Список файлов
Get-ChildItem
# или
dir

# Чтение файла
Get-Content VERSION

# Проверка существования файла
if (Test-Path package.ipk) { Write-Host "exists" }

# Docker команды
docker ps
docker images
```

**Преимущество:** Нативные команды выполняются мгновенно

## Когда WSL неизбежен

### Bash скрипты проекта

```powershell
# ✅ Правильно - скрипт требует bash
wsl bash scripts/update-version-metadata.sh 2025.11.28.3

# ✅ С таймаутом для безопасности
wsl bash -c "export GIT_PAGER=cat; bash scripts/update-version-metadata.sh 2025.11.28.3"
```

### SSH подключения

```powershell
# ✅ Правильно - используем настроенный SSH в WSL
wsl ssh openwrt-test "uname -a"

# ✅ Копирование через SCP
wsl scp package.ipk openwrt-test:/tmp/
```

### Linux-специфичные инструменты

```powershell
# ✅ Правильно - нет аналога в Windows
wsl grep -r "pattern" .
wsl sed -i 's/old/new/g' file.txt
wsl awk '{print $1}' data.txt
```

## Гибридный подход

### Комбинируй нативные и WSL команды

```powershell
# ✅ Оптимально - используй нативное где возможно
$version = Get-Content VERSION  # Нативно
git add VERSION                  # Нативно
git commit -m "chore: update version to $version"  # Нативно
git push                         # Нативно

# Только для bash скрипта используй WSL
wsl bash scripts/validate-version.sh
```

## Измерение производительности

### Сравнение времени выполнения

```powershell
# Тест WSL
Measure-Command { wsl git status } | Select-Object TotalMilliseconds
# Результат: ~150-250ms

# Тест нативно
Measure-Command { git status } | Select-Object TotalMilliseconds
# Результат: ~10-50ms

# Экономия: 100-200ms на каждый вызов
```

### В масштабе

Если выполняешь 100 git команд через WSL:
- WSL: 100 × 200ms = 20 секунд
- Нативно: 100 × 30ms = 3 секунды
- **Экономия: 17 секунд**

## Рекомендации для Kiro Agent

### При выборе команды спрашивай себя:

1. **Есть ли нативная PowerShell команда?** → Используй её
2. **Работает ли нативная git/gh/docker?** → Используй их
3. **Это bash скрипт или Linux-специфичная команда?** → Используй WSL
4. **Нужен SSH?** → Используй WSL (если Windows SSH не настроен)

### Чеклист перед использованием WSL:

- [ ] Проверил, есть ли нативная альтернатива?
- [ ] Это действительно требует Linux окружение?
- [ ] Нельзя ли переписать на PowerShell?
- [ ] Если WSL необходим - добавил таймаут?

## Исключения

### Когда WSL предпочтительнее:

1. **Bash скрипты проекта** - уже написаны для bash
2. **SSH операции** - настроены в WSL
3. **Сложные текстовые операции** - grep/sed/awk мощнее PowerShell аналогов
4. **Makefile** - требует GNU make
5. **Тестирование на Linux** - нужно Linux окружение

## Оптимизация WSL вызовов

### Если WSL необходим, оптимизируй:

```powershell
# ❌ Плохо - много отдельных вызовов WSL
wsl git status
wsl git add .
wsl git commit -m "message"
wsl git push

# ✅ Хорошо - один вызов WSL
wsl bash -c "git status && git add . && git commit -m 'message' && git push"

# ✅ Еще лучше - нативно
git status
git add .
git commit -m "message"
git push
```

### Группируй команды

```powershell
# ❌ Плохо - 5 вызовов WSL
wsl cat VERSION
wsl grep PKG_VERSION Makefile
wsl ls -la dist/
wsl test -f package.ipk
wsl sha256sum package.ipk

# ✅ Хорошо - 1 вызов WSL
wsl bash -c "
  cat VERSION
  grep PKG_VERSION Makefile
  ls -la dist/
  test -f package.ipk && sha256sum package.ipk
"
```

## Мониторинг использования WSL

### Отслеживай сколько раз используешь WSL

```powershell
# Добавь в PowerShell profile для статистики
$global:WSLCallCount = 0

function wsl {
    $global:WSLCallCount++
    & wsl.exe @args
}

# Проверить статистику
Write-Host "WSL calls: $global:WSLCallCount"
```

## Итоговое правило

> **Используй нативные Windows/PowerShell команды везде где возможно.  
> WSL только когда нет альтернативы или это значительно проще.**

Это экономит время, ресурсы и делает выполнение быстрее.
