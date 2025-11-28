# Паттерны решения проблем

## Общий подход к troubleshooting

При возникновении проблемы следуй этому алгоритму:

1. **Сбор информации** - логи, error messages, контекст
2. **Воспроизведение** - можно ли воспроизвести проблему локально?
3. **Изоляция** - какой компонент вызывает проблему?
4. **Анализ** - что является root cause?
5. **Решение** - минимальное изменение для исправления
6. **Валидация** - проверка, что проблема решена
7. **Документация** - обновление docs/troubleshooting

## Типичные проблемы и решения

### 1. Docker образ превышает 2GB

**Симптомы:**
- `validate-docker-image-size.sh` выдает ошибку
- GitHub Actions workflow падает на валидации
- Образ занимает > 2GB

**Диагностика:**
```bash
# Проверить размер образа
docker inspect openwrt-sdk:local --format='{{.Size}}'

# Посмотреть историю слоев
docker history openwrt-sdk:local --human --no-trunc

# Найти самые большие слои
docker history openwrt-sdk:local --format "{{.Size}}\t{{.CreatedBy}}" | sort -h
```

**Типичные причины:**
1. Apt кэши не удаляются в том же слое
2. Временные файлы остаются в образе
3. SDK архив не удаляется после распаковки
4. Слишком много RUN команд (каждая создает слой)

**Решение:**
```dockerfile
# ❌ Плохо - создает несколько слоев
RUN apt-get update
RUN apt-get install -y pkg1 pkg2
RUN rm -rf /var/lib/apt/lists/*

# ✅ Хорошо - один слой с очисткой
RUN apt-get update && \
    apt-get install -y --no-install-recommends pkg1 pkg2 && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# ❌ Плохо - архив остается в образе
RUN tar -xf sdk.tar.xz
RUN rm sdk.tar.xz

# ✅ Хорошо - удаление в том же слое
RUN tar -xf sdk.tar.xz && rm -f sdk.tar.xz sha256sums
```

### 2. Ошибка загрузки OpenWrt SDK

**Симптомы:**
- `curl: (22) The requested URL returned error: 404`
- `download-sdk.sh` не может найти SDK файл
- Неправильный URL в логах

**Диагностика:**
```bash
# Проверить доступность директории
curl -I https://downloads.openwrt.org/releases/23.05.5/targets/x86/64/

# Посмотреть список файлов
curl -fsSL https://downloads.openwrt.org/releases/23.05.5/targets/x86/64/ | grep sdk

# Проверить sha256sums
curl -fsSL https://downloads.openwrt.org/releases/23.05.5/targets/x86/64/sha256sums | grep sdk
```

**Типичные причины:**
1. Неправильный суффикс MUSL для архитектуры
2. Версия OpenWrt не существует
3. Архитектура не поддерживается
4. Временные проблемы с сервером

**Решение:**
```bash
# Проверить правильность суффикса
# x86/64 -> musl (не glibc!)
# mips -> musl
# aarch64 -> musl

# Добавить retry логику
retry_count=0
max_retries=15
while [ $retry_count -lt $max_retries ]; do
  if curl -fsSL "$url" -o "$output"; then
    echo "Download successful"
    break
  fi
  retry_count=$((retry_count + 1))
  wait_time=$((2 ** retry_count))
  [ $wait_time -gt 60 ] && wait_time=60
  echo "Retry $retry_count/$max_retries after ${wait_time}s..."
  sleep $wait_time
done

# Добавить диагностику при ошибке
if [ $retry_count -eq $max_retries ]; then
  echo "ERROR: Failed to download SDK after $max_retries attempts"
  echo "URL: $url"
  echo "Available files:"
  curl -fsSL "${base_url}/" | grep -o 'href="[^"]*"' | cut -d'"' -f2
  exit 1
fi
```

### 3. GitHub Actions workflow timeout

**Симптомы:**
- Workflow работает > 30 минут и отменяется
- "The job was canceled because it exceeded the maximum execution time"
- Зависает на определенном шаге

**Диагностика:**
```powershell
# Посмотреть логи workflow
gh run view <run-id> --log

# Найти шаг, который занимает больше всего времени
gh run view <run-id> --log | Select-String "##\[group\]" -Context 0,50
```

**Типичные причины:**
1. Загрузка SDK занимает слишком много времени
2. Сборка пакета зависла
3. Нет timeout на отдельных шагах
4. Сетевые проблемы без retry

**Решение:**
```yaml
# Добавить timeout на job уровне
jobs:
  build:
    timeout-minutes: 30
    steps:
      # ...

# Добавить timeout на step уровне
- name: Download SDK
  timeout-minutes: 10
  run: |
    bash docker/sdk/download-sdk.sh

# Использовать кэширование
- name: Cache SDK
  uses: actions/cache@v3
  with:
    path: /tmp/sdk
    key: sdk-${{ env.OPENWRT_VERSION }}-${{ env.SDK_TARGET }}

# Использовать предсобранные Docker образы
- name: Pull SDK image
  run: |
    docker pull ghcr.io/${{ github.repository }}/openwrt-sdk:23.05.5-x86-64
```

### 4. Проблемы с путями на Windows

**Симптомы:**
- "Error response from daemon: invalid mount config"
- "No such file or directory" при монтировании
- Скрипты не находят файлы

**Диагностика:**
```powershell
# Проверить текущую директорию
Get-Location
${PWD}

# Проверить формат пути
(Get-Location).Path
(Get-Location).Path -replace '\\', '/'

# Тест монтирования
docker run --rm -v ${PWD}:/test alpine ls /test
```

**Типичные причины:**
1. Обратные слеши в путях
2. Пробелы в путях
3. Неправильный формат для Docker
4. Проблемы с file sharing в Docker Desktop

**Решение:**
```powershell
# ✅ PowerShell - используй ${PWD}
docker run -v ${PWD}:/workspace image

# ✅ CMD - используй %CD%
docker run -v %CD%:/workspace image

# ✅ Git Bash - используй $(pwd)
docker run -v "$(pwd):/workspace" image

# Для путей с пробелами
docker run -v "${PWD}:/workspace" image

# Проверить Docker Desktop file sharing
# Settings -> Resources -> File Sharing
# Добавить диск C:\ если его нет
```

### 5. Версия в пакете не совпадает с VERSION файлом

**Симптомы:**
- `validate-ipk-version.sh` выдает ошибку
- VERSION файл содержит одну версию, а IPK другую
- PKG_VERSION в Makefile не синхронизирован

**Диагностика:**
```bash
# Проверить VERSION файл
cat VERSION

# Проверить PKG_VERSION в Makefile
grep PKG_VERSION package/openwrt-captive-monitor/Makefile

# Проверить версию в собранном пакете
tar -xzOf openwrt-captive-monitor_*.ipk control.tar.gz | tar -xzO ./control | grep Version
```

**Типичные причины:**
1. Makefile не обновлен после изменения VERSION
2. Ручное изменение версии без синхронизации
3. Проблемы с auto-version workflow

**Решение:**
```bash
# Использовать скрипт обновления версии
bash scripts/update-version-metadata.sh

# Или вручную синхронизировать
VERSION=$(cat VERSION)
sed -i "s/^PKG_VERSION:=.*/PKG_VERSION:=${VERSION}/" package/openwrt-captive-monitor/Makefile

# Для релизов всегда PKG_RELEASE:=1
sed -i "s/^PKG_RELEASE:=.*/PKG_RELEASE:=1/" package/openwrt-captive-monitor/Makefile
```

### 6. Старые GitHub Actions workflow продолжают работать

**Симптомы:**
- Несколько запусков одного workflow одновременно
- Старые запуски не отменяются при новом push
- Превышение лимита concurrent jobs

**Диагностика:**
```powershell
# Посмотреть активные запуски
gh run list --status in_progress

# Посмотреть запуски для конкретной ветки
gh run list --branch feature/my-feature --status in_progress
```

**Решение:**
```yaml
# Добавить concurrency group в workflow
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

# Или использовать отдельный workflow для отмены
# .github/workflows/cancel-old-workflows.yml
```

```powershell
# Ручная отмена старых запусков
gh run list --status in_progress --branch $(git branch --show-current) --json databaseId --jq '.[].databaseId' | ForEach-Object { gh run cancel $_ }
```

### 7. Property-based тесты падают с неожиданными входными данными

**Симптомы:**
- Тест проходит для простых случаев, но падает при property testing
- "Falsified after X tests" с неожиданным counterexample
- Тест находит edge case, который не был учтен

**Диагностика:**
```bash
# Запустить тест с seed для воспроизведения
pytest test_properties.py --hypothesis-seed=12345

# Увеличить количество примеров
pytest test_properties.py --hypothesis-max-examples=1000

# Включить verbose режим
pytest test_properties.py -v --hypothesis-verbosity=verbose
```

**Типичные причины:**
1. Генератор создает невалидные данные
2. Функция не обрабатывает edge cases
3. Предусловия свойства слишком слабые
4. Постусловия свойства слишком строгие

**Решение:**
```python
# ❌ Плохо - генератор создает невалидные данные
@given(st.text())
def test_parse_roundtrip(s):
    assert parse(print(s)) == s

# ✅ Хорошо - генератор создает только валидные данные
@given(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
def test_parse_roundtrip(s):
    assume(len(s) > 0)  # Добавить предусловие
    result = parse(print(s))
    assert result == s

# Или использовать filter
@given(st.text().filter(lambda s: len(s) > 0 and s.strip() == s))
def test_parse_roundtrip(s):
    assert parse(print(s)) == s
```

## Диагностические скрипты

### Скрипт для анализа Docker слоев

```bash
#!/bin/bash
# analyze-docker-layers.sh

IMAGE=$1
if [ -z "$IMAGE" ]; then
  echo "Usage: $0 <image-name>"
  exit 1
fi

echo "=== Docker Image Analysis ==="
echo "Image: $IMAGE"
echo

echo "=== Total Size ==="
docker inspect "$IMAGE" --format='{{.Size}}' | numfmt --to=iec-i --suffix=B
echo

echo "=== Layer Sizes ==="
docker history "$IMAGE" --format "table {{.Size}}\t{{.CreatedBy}}" --no-trunc | head -20
echo

echo "=== Largest Layers ==="
docker history "$IMAGE" --format "{{.Size}}\t{{.CreatedBy}}" --no-trunc | \
  grep -v "0B" | \
  sort -h -r | \
  head -10
```

### Скрипт для проверки OpenWrt SDK URL

```bash
#!/bin/bash
# check-sdk-url.sh

OPENWRT_VERSION=$1
SDK_TARGET=$2
SDK_SUBTARGET=$3

BASE_URL="https://downloads.openwrt.org/releases/${OPENWRT_VERSION}/targets/${SDK_TARGET}/${SDK_SUBTARGET}"

echo "=== Checking SDK availability ==="
echo "Version: $OPENWRT_VERSION"
echo "Target: $SDK_TARGET/$SDK_SUBTARGET"
echo "Base URL: $BASE_URL"
echo

echo "=== Directory listing ==="
curl -fsSL "${BASE_URL}/" | grep -o 'href="[^"]*sdk[^"]*"' | cut -d'"' -f2
echo

echo "=== SHA256 sums ==="
curl -fsSL "${BASE_URL}/sha256sums" | grep sdk
```

### Скрипт для валидации спецификации

```bash
#!/bin/bash
# validate-spec.sh

SPEC_DIR=$1

echo "=== Validating Specification ==="
echo "Directory: $SPEC_DIR"
echo

# Проверить наличие файлов
for file in requirements.md design.md tasks.md; do
  if [ -f "$SPEC_DIR/$file" ]; then
    echo "✅ $file exists"
  else
    echo "❌ $file missing"
  fi
done
echo

# Проверить EARS паттерны в requirements
echo "=== Checking EARS patterns ==="
grep -E "(WHEN|WHILE|IF|WHERE|THE .* SHALL)" "$SPEC_DIR/requirements.md" | wc -l
echo "EARS patterns found"
echo

# Проверить correctness properties в design
echo "=== Checking Correctness Properties ==="
grep -E "Property [0-9]+:" "$SPEC_DIR/design.md" | wc -l
echo "Properties found"
echo

# Проверить ссылки на requirements
echo "=== Checking Requirements References ==="
grep -E "\*\*Validates: Requirements [0-9]+\.[0-9]+\*\*" "$SPEC_DIR/design.md" | wc -l
echo "Requirement references found"
```

## Чеклист для troubleshooting

Когда сталкиваешься с проблемой:

1. ✅ Собрал все логи и error messages
2. ✅ Попытался воспроизвести локально
3. ✅ Изолировал проблемный компонент
4. ✅ Проверил документацию и существующие issues
5. ✅ Проверил похожие проблемы в других спецификациях
6. ✅ Создал минимальный воспроизводимый пример
7. ✅ Определил root cause
8. ✅ Реализовал минимальное исправление
9. ✅ Добавил тесты для предотвращения регрессии
10. ✅ Обновил документацию

## Когда обращаться к пользователю

Обращайся к пользователю когда:

1. **Неоднозначность** - несколько возможных решений, нужен выбор
2. **Критическое изменение** - изменение может повлиять на другие компоненты
3. **Недостаточно информации** - нужны дополнительные детали
4. **Нестандартная ситуация** - проблема выходит за рамки обычных паттернов
5. **Требуется подтверждение** - перед merge в main или созданием release

**Не обращайся к пользователю** для:
- Стандартных исправлений с очевидным решением
- Рутинных задач (форматирование, линтинг)
- Промежуточных шагов в процессе решения
- Вопросов, на которые можно найти ответ в документации


### 8. Команда зависает в ожидании ввода

**Симптомы:**
- Команда типа `git show 9724d68 --stat` зависает
- Нет вывода, нет ошибки, просто ожидание
- Невозможно прервать команду через Ctrl+C
- Процесс висит неизвестно долго

**Причина:**
- Команда ожидает интерактивного ввода (например, пейджер `less`)
- Вывод команды слишком большой и автоматически открывается в пейджере
- В неинтерактивном окружении (CI, скрипт) пейджер не может работать

**Диагностика:**
```bash
# Проверить, запущен ли процесс
ps aux | grep git

# Проверить переменную окружения пейджера
echo $GIT_PAGER
echo $PAGER
```

**Решение:**

**Вариант 1: Отключить пейджер для конкретной команды**
```bash
# Использовать --no-pager
git --no-pager show 9724d68 --stat

# Или установить PAGER в cat
GIT_PAGER=cat git show 9724d68 --stat

# Или использовать переменную окружения
PAGER=cat git show 9724d68 --stat
```

**Вариант 2: Отключить пейджер глобально**
```bash
# Для текущей сессии
export GIT_PAGER=cat

# Для всех сессий (в ~/.bashrc или ~/.zshrc)
echo 'export GIT_PAGER=cat' >> ~/.bashrc

# Или через git config
git config --global core.pager cat
```

**Вариант 3: Использовать less с правильными опциями**
```bash
# -F: выйти если вывод помещается на один экран
# -R: разрешить ANSI цвета
# -X: не очищать экран при выходе
export GIT_PAGER="less -FRX"
```

**Для скриптов и CI:**
```bash
#!/bin/bash
# Всегда отключать пейджер в скриптах
export GIT_PAGER=cat
export PAGER=cat

# Или использовать --no-pager для каждой команды
git --no-pager log --oneline
git --no-pager show HEAD --stat
git --no-pager diff
```

**Для Kiro/автоматизации:**
```bash
# В начале скрипта или перед git командами
export GIT_PAGER=cat

# Или использовать флаг
git --no-pager <command>
```

### 9. WSL и Docker продолжают работать после использования

**Симптомы:**
- WSL процессы продолжают работать в фоне
- Docker Desktop потребляет ресурсы после завершения работы
- Высокое использование CPU/RAM даже когда не работаешь с проектом
- Медленная работа системы

**Причина:**
- WSL дистрибутивы не останавливаются автоматически
- Docker Desktop продолжает работать в фоне
- Контейнеры могут продолжать работать
- WSL2 VM не освобождает память автоматически

**Диагностика:**
```powershell
# Проверить запущенные WSL дистрибутивы
wsl --list --running

# Проверить статус Docker
docker ps

# Проверить использование ресурсов WSL
wsl --list --verbose

# Проверить процессы Docker Desktop
Get-Process | Where-Object {$_.ProcessName -like "*docker*"}
```

**Решение:**

**Остановка WSL:**
```powershell
# Остановить конкретный дистрибутив
wsl --terminate Ubuntu

# Остановить все WSL дистрибутивы
wsl --shutdown

# Проверить что все остановлено
wsl --list --running
```

**Остановка Docker:**
```powershell
# Остановить все контейнеры
docker stop $(docker ps -q)

# Или остановить Docker Desktop полностью
# Через GUI: System Tray -> Docker Desktop -> Quit Docker Desktop

# Или через PowerShell
Stop-Process -Name "Docker Desktop" -Force

# Проверить что Docker остановлен
docker ps  # Должна быть ошибка подключения
```

**Автоматизация очистки:**
```powershell
# Скрипт для полной остановки WSL и Docker
# cleanup-wsl-docker.ps1

Write-Host "Stopping Docker containers..."
docker stop $(docker ps -q) 2>$null

Write-Host "Stopping Docker Desktop..."
Stop-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue

Write-Host "Shutting down WSL..."
wsl --shutdown

Write-Host "Waiting for shutdown..."
Start-Sleep -Seconds 3

Write-Host "Checking status..."
wsl --list --running

Write-Host "✅ Cleanup complete"
```

**Добавить в common-commands.md:**
```powershell
# Быстрая очистка после работы
function cleanup-dev {
    docker stop $(docker ps -q) 2>$null
    wsl --shutdown
    Write-Host "✅ WSL and Docker stopped"
}

# Добавить в $PROFILE для использования в любой сессии
```

**Освобождение памяти WSL2:**
```powershell
# WSL2 не освобождает память автоматически
# Нужно остановить и запустить заново

# Остановить WSL
wsl --shutdown

# Подождать несколько секунд
Start-Sleep -Seconds 5

# Запустить снова (автоматически при первой команде)
wsl echo "WSL restarted"
```

**Настройка автоматической остановки Docker:**
```powershell
# В Docker Desktop Settings:
# General -> Start Docker Desktop when you log in (отключить)
# Resources -> Advanced -> Disk image location (проверить размер)

# Ограничить ресурсы WSL2 через .wslconfig
# Создать файл C:\Users\<User>\.wslconfig

[wsl2]
memory=4GB
processors=2
swap=2GB
```

**Пример .wslconfig:**
```ini
# C:\Users\<User>\.wslconfig

[wsl2]
# Ограничить память (по умолчанию 50% RAM)
memory=4GB

# Ограничить процессоры (по умолчанию все)
processors=2

# Ограничить swap
swap=2GB

# Освобождать память при простое
# (экспериментальная функция)
autoMemoryReclaim=gradual
```

**Мониторинг ресурсов:**
```powershell
# Проверить использование памяти WSL
wsl --list --verbose

# Проверить размер виртуального диска WSL
Get-ChildItem "$env:LOCALAPPDATA\Docker\wsl\data" -Recurse | 
    Measure-Object -Property Length -Sum | 
    Select-Object @{Name="Size(GB)";Expression={[math]::Round($_.Sum/1GB,2)}}

# Проверить использование Docker
docker system df
```

**Регулярная очистка:**
```powershell
# Очистка Docker (освобождает место)
docker system prune -a --volumes

# Очистка WSL кэша
wsl --shutdown
# Удалить временные файлы в WSL
wsl rm -rf /tmp/*
wsl rm -rf ~/.cache/*
```

### 10. Переполнение логов Docker при использовании axel

**Симптомы:**
- `[output clipped, log limit 2MiB reached]`
- Сборка зависает на определенном проценте загрузки
- Невозможно увидеть полный вывод Docker build

**Причина:**
- axel выводит слишком подробный прогресс
- Docker ограничивает размер логов до 2MB
- Каждое обновление прогресса создает новую строку в логах

**Диагностика:**
```bash
# Проверить размер логов контейнера
docker inspect <container-id> --format='{{.LogPath}}' | xargs ls -lh

# Посмотреть последние строки логов
docker logs <container-id> --tail 100
```

**Решение:**

**Вариант 1: Использовать --progress=plain**
```bash
# При сборке Docker образа
docker build --progress=plain -t image:tag .

# Это упрощает вывод и уменьшает размер логов
```

**Вариант 2: Использовать компактный вывод axel**
```bash
# В скрипте загрузки
axel -n 32 -a -o "$output" "$url"

# Опция -a делает прогресс-бар более компактным
```

**Вариант 3: Перенаправить вывод axel**
```bash
# Скрыть прогресс-бар полностью
axel -n 32 -q -o "$output" "$url"

# Или перенаправить в файл
axel -n 32 -o "$output" "$url" 2>&1 | tee /tmp/download.log
```

**Для CI/CD:**
```yaml
# В GitHub Actions
- name: Build Docker image
  run: |
    docker build --progress=plain -t image:tag .
```

### 11. Параллельные сборки не показывают вывод

**Симптомы:**
- PowerShell jobs запущены, но нет вывода
- Невозможно отследить прогресс сборки
- Не видно ошибок при падении сборки

**Причина:**
- Фоновые PowerShell jobs подавляют stdout
- Start-Job не показывает вывод в реальном времени
- Вывод буферизуется и доступен только после завершения

**Диагностика:**
```powershell
# Проверить запущенные jobs
Get-Job

# Получить вывод завершенного job
Receive-Job -Id 1

# Проверить статус
Get-Job | Format-Table Id, State, HasMoreData
```

**Решение:**

**Использовать controlPwshProcess вместо Start-Job:**
```powershell
# ❌ Плохо - нет вывода в реальном времени
Start-Job -ScriptBlock {
    docker build -t image:tag .
}

# ✅ Хорошо - вывод доступен через getProcessOutput
kiro controlPwshProcess --action start `
  --command "docker build -t image:tag ." `
  --path "docker/sdk"

# Мониторить вывод
kiro getProcessOutput --processId <id> --lines 20
```

**Или использовать Start-Process с перенаправлением:**
```powershell
# Перенаправить вывод в файл
Start-Process -FilePath "docker" `
  -ArgumentList "build -t image:tag ." `
  -RedirectStandardOutput "build.log" `
  -RedirectStandardError "build.err.log" `
  -NoNewWindow

# Мониторить файл
Get-Content build.log -Wait -Tail 20
```

### 12. Формат IPK пакета не распознаётся

**Симптомы:**
- `tar: This does not look like a tar archive`
- Ошибка при извлечении control.tar.gz
- Валидация пакета падает

**Причина:**
- Новые версии OpenWrt используют ar archive формат
- Старый скрипт ожидает tar.gz формат
- Разные версии OpenWrt используют разные форматы

**Диагностика:**
```bash
# Определить формат файла
file openwrt-captive-monitor_*.ipk

# Вывод для ar archive:
# openwrt-captive-monitor_1.0.0_all.ipk: Debian binary package (format 2.0)

# Вывод для tar.gz:
# openwrt-captive-monitor_1.0.0_all.ipk: gzip compressed data
```

**Решение:**
```bash
#!/bin/bash
# Универсальный скрипт извлечения IPK

IPK_FILE=$1

# Определить формат
if file "$IPK_FILE" | grep -q "Debian binary package"; then
    echo "Detected ar archive format"
    
    # Новый формат - использовать ar
    ar x "$IPK_FILE" control.tar.gz
    tar -xzf control.tar.gz ./control
    
elif file "$IPK_FILE" | grep -q "gzip compressed"; then
    echo "Detected tar.gz format"
    
    # Старый формат - использовать tar
    tar -xzOf "$IPK_FILE" control.tar.gz | tar -xzO ./control
    
else
    echo "ERROR: Unknown IPK format"
    file "$IPK_FILE"
    exit 1
fi

# Теперь можно работать с файлом control
cat control
```

**Для валидации версии:**
```bash
#!/bin/bash
# validate-ipk-version.sh

set -euo pipefail

IPK_FILE=$(find dist -name "*.ipk" | head -1)
VERSION=$(cat VERSION)

echo "Validating IPK version..."
echo "Expected version: $VERSION"
echo "IPK file: $IPK_FILE"

# Создать временную директорию
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Извлечь control файл (универсально)
if file "$IPK_FILE" | grep -q "Debian binary"; then
    ar x "$IPK_FILE" control.tar.gz
    tar -xzf control.tar.gz ./control
else
    tar -xzOf "$IPK_FILE" control.tar.gz | tar -xzO ./control > control
fi

# Проверить версию
IPK_VERSION=$(grep "^Version:" control | cut -d' ' -f2)

echo "IPK version: $IPK_VERSION"

if [ "$IPK_VERSION" != "$VERSION" ]; then
    echo "❌ ERROR: Version mismatch"
    exit 1
fi

echo "✅ Version matches"

# Очистка
cd -
rm -rf "$TEMP_DIR"
```
