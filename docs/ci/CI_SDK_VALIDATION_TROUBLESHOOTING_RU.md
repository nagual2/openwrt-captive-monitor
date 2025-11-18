# Руководство по устранению неполадок с валидацией SDK в CI

Это руководство поможет вам устранить распространенные проблемы, связанные с валидацией OpenWrt SDK в CI/CD конвейере.

## Общие проблемы и решения

### 1. Ошибка: "Lint (shfmt) failed"

**Проблема**: Скрипт валидации имеет неправильное форматирование кода.

**Решение**:
```bash
# Проверить форматирование локально
shfmt -d -i 4 -ln posix scripts/validate-sdk-*.sh

# Исправить форматирование автоматически
shfmt -w -i 4 -ln posix scripts/validate-sdk-*.sh

# Проверить после исправлений
shellcheck scripts/validate-sdk-*.sh
```

### 2. Ошибка: "SDK image not found in registry"

**Проблема**: Указан неверный тег или версия Docker образа OpenWrt SDK.

**Решение**:
1. Проверить правильный формат тега:
   ```bash
   # Правильный формат: arch-version
   # Например: x86_64-23.05.3
   ./scripts/validate-sdk-image.sh ghcr.io/openwrt/sdk:x86_64-23.05.3 x86/64 23.05.3 x86_64
   ```

2. Проверить доступные версии:
   ```bash
   # Проверить доступные образы
   docker manifest inspect ghcr.io/openwrt/sdk:x86_64-23.05.3
   ```

3. Обновить матрицу в CI:
   ```yaml
   # В .github/workflows/ci.yml
   matrix:
     include:
       - openwrt_version: '23.05.3'  # Исправить версию
         sdk_target: 'x86/64'
         sdk_slug: 'x86-64'          # Соответствует arch
         arch: 'x86_64'              # Использовать в CONTAINER
   ```

### 3. Ошибка: "No accessible SDK mirrors found"

**Проблема**: URL для скачивания SDK tarball недоступен.

**Решение**:
1. Проверить версию OpenWrt:
   ```bash
   # Проверить доступные версии
   curl -s "https://downloads.openwrt.org/releases/" | grep -o 'href="[0-9]\+\.[0-9]\+\(\.[0-9]\+\)\?/"' | head -5
   ```

2. Проверить URL вручную:
   ```bash
   # Протестировать URL
   curl --head --silent --connect-timeout 10 "https://downloads.openwrt.org/releases/23.05.2/targets/x86/64/openwrt-sdk-23.05.2-x86-64_gcc-12.3.0_musl.Linux-x86_64.tar.xz"
   ```

3. Обновить контрольную сумму:
   ```bash
   # Получить правильную контрольную сумму
   curl -s "https://downloads.openwrt.org/releases/23.05.2/targets/x86/64/sha256sums" | grep "openwrt-sdk-23.05.2-x86-64"
   ```

### 4. Ошибка: "Invalid OpenWrt version format"

**Проблема**: Неверный формат версии OpenWrt.

**Решение**:
Используйте правильный формат: `X.Y` или `X.Y.Z`
- ✅ Правильно: `23.05.2`, `23.05.3`, `22.03.5`
- ❌ Неправильно: `23.05`, `v23.05.2`, `23.05.2.0`

### 5. Ошибка: "Invalid target/subtarget format"

**Проблема**: Неверный формат цели/подцели.

**Решение**:
Используйте формат: `target/subtarget`
- ✅ Правильно: `x86/64`, `bcm27xx/bcm2711`, `ipq40xx/generic`
- ❌ Неправильно: `x86-64`, `x86_64`, `x86/64/`

## Процесс отладки

### Шаг 1: Локальная отладка
```bash
# Клонировать репозиторий
git clone https://github.com/nagual2/openwrt-captive-monitor.git
cd openwrt-captive-monitor

# Проверить скрипты валидации
./scripts/validate-sdk-image.sh ghcr.io/openwrt/sdk:x86_64-23.05.3 x86/64 23.05.3 x86_64
./scripts/validate-sdk-url.sh 23.05.2

# Проверить синтаксис YAML
yamllint -d relaxed .github/workflows/ci.yml
```

### Шаг 2: Создание тестового PR
```bash
# Создать ветку с исправлениями
git checkout -b fix/sdk-validation

# Внести исправления
# (согласно рекомендациям выше)

# Закоммитить изменения
git add .
git commit -m "fix(ci): исправить валидацию SDK"

# Отправить PR
git push origin fix/sdk-validation
```

### Шаг 3: Проверка в CI
1. Открыть PR в GitHub
2. Дождаться завершения CI
3. Проверить логи в Actions tab
4. Если ошибки исправлены - слить PR

## Частые причины ошибок

### 1. Изменения в OpenWrt
- OpenWrt периодически выпускает новые версии
- Старые версии могут быть удалены
- Форматы тегов могут меняться

### 2. Проблемы с сетью
- Временные сбои в доступности mirror
- Проблемы с аутентификацией в GitHub registry

### 3. Изменения в API GitHub
- GitHub может изменять API endpoints
- Требуются обновления токенов аутентификации

## Рекомендации по поддержке

### 1. Регулярное обновление
```bash
# Проверять актуальные версии quarterly
curl -s "https://downloads.openwrt.org/releases/" | grep -o 'href="[0-9]\+\.[0-9]\+\(\.[0-9]\+\)\?/"' | head -3
```

### 2. Мониторинг CI failures
```bash
# Настроить уведомления о сбоях
# В GitHub repository settings → Branches → Branch protection rules
```

### 3. Документирование изменений
```bash
# Вести CHANGELOG с изменениями форматов
echo "## $(date +%Y-%m-%d)"
echo "- Обновлен формат Docker тегов: openwrt-version → arch-version"
echo "- Добавлена валидация URL для SDK tarball"
```

## Полезные команды

```bash
# Проверить статус CI
gh run list --repo nagual2/openwrt-captive-monitor --limit 10

# Скачать логи конкретного run
gh run view 19412528368 --repo nagual2/openwrt-captive-monitor --log

# Проверить доступность SDK образа
docker manifest inspect ghcr.io/openwrt/sdk:x86_64-23.05.3

# Проверить форматирование скриптов
shfmt -d scripts/validate-sdk-*.sh

# Запустить валидацию локально
./scripts/validate-sdk-image.sh ghcr.io/openwrt/sdk:x86_64-23.05.3 x86/64 23.05.3 x86_64
```

## Контакты для поддержки

Если проблема не решается с помощью этого руководства:

1. **Создать Issue** в репозитории с меткой `ci/sdk-validation`
2. **Прикрепить логи** CI для анализа
3. **Указать версию** OpenWrt и архитектуру
4. **Описать шаги** воспроизведения ошибки

## Пример Issue template

```markdown
## Проблема с валидацией SDK

### Окружение
- Версия OpenWrt: 23.05.3
- Архитектура: x86/64
- CI Run: #19412528368

### Описание
CI не проходит валидацию SDK с ошибкой: [текст ошибки]

### Шаги воспроизведения
1. [детальные шаги]

### Ожидаемое поведение
[описание правильного поведения]

### Дополнительная информация
[любая полезная информация]
```

---

Это руководство должно помочь вам быстро идентифицировать и устранять проблемы с валидацией SDK в CI, минимизируя время простоя и улучшая надежность конвейера.