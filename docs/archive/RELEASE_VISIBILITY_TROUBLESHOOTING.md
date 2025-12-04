# Решение проблемы с видимостью релизов

## Проблема
Релизы не отображаются на странице https://github.com/nagual2/openwrt-captive-monitor/releases

## Диагностика

✅ **Релизы существуют в GitHub API** - подтверждено через `gh` CLI
✅ **Теги существуют в репозитории** - подтверждено через `git ls-remote`
✅ **Релизы не являются draft** - все опубликованы
✅ **Релизы не являются prerelease** - все стабильные

### Найденные релизы:

**Семантические релизы (5):**
- v0.1.0 - Historical Release (2025-11-28T21:26:26Z)
- v0.1.1 - Historical Release (2025-11-28T21:26:36Z)
- v0.1.2 - Historical Release (2025-11-28T21:26:46Z)
- v1.0.1 - Historical Release (2025-11-28T21:26:56Z)
- v1.0.3 - Historical Release (2025-11-28T21:27:07Z) - Latest

**Датированные релизы (7+):**
- v2025.11.21.34
- v2025.11.22.1, v2025.11.22.99, v2025.11.22.100
- v2025.11.27.10, v2025.11.27.11, v2025.11.27.12
- И другие...

## Возможные причины

### 1. Кэширование GitHub
GitHub кэширует страницу релизов на CDN. После создания новых релизов может потребоваться время для обновления кэша.

**Решение:**
- Подождите 5-10 минут
- Обновите страницу с очисткой кэша (Ctrl+F5 или Cmd+Shift+R)

### 2. Кэш браузера
Ваш браузер может кэшировать старую версию страницы.

**Решение:**
1. Очистите кэш браузера:
   - Chrome/Edge: Ctrl+Shift+Delete → Очистить кэш
   - Firefox: Ctrl+Shift+Delete → Кэш
2. Откройте страницу в режиме инкогнито:
   - Chrome/Edge: Ctrl+Shift+N
   - Firefox: Ctrl+Shift+P
3. Попробуйте другой браузер

### 3. Прямые ссылки на релизы
Попробуйте открыть релизы по прямым ссылкам:

**Семантические релизы:**
- https://github.com/nagual2/openwrt-captive-monitor/releases/tag/v0.1.0
- https://github.com/nagual2/openwrt-captive-monitor/releases/tag/v0.1.1
- https://github.com/nagual2/openwrt-captive-monitor/releases/tag/v0.1.2
- https://github.com/nagual2/openwrt-captive-monitor/releases/tag/v1.0.1
- https://github.com/nagual2/openwrt-captive-monitor/releases/tag/v1.0.3

**Датированные релизы:**
- https://github.com/nagual2/openwrt-captive-monitor/releases/tag/v2025.11.21.34
- https://github.com/nagual2/openwrt-captive-monitor/releases/tag/v2025.11.22.1
- https://github.com/nagual2/openwrt-captive-monitor/releases/tag/v2025.11.27.12

## Проверка через GitHub CLI

Вы можете проверить релизы через командную строку:

```powershell
# Список всех релизов
gh release list --limit 100

# Просмотр конкретного релиза
gh release view v0.1.0

# Проверка через API
gh api repos/nagual2/openwrt-captive-monitor/releases/tags/v0.1.0
```

## Проверка через Git

```powershell
# Проверить теги в удаленном репозитории
git ls-remote --tags origin | Select-String "v0.1|v1.0"

# Обновить локальные теги
git fetch --tags
```

## Если проблема сохраняется

1. **Проверьте настройки репозитория:**
   - Откройте Settings → General
   - Убедитесь, что репозиторий публичный (Public)
   - Проверьте, что нет ограничений на видимость релизов

2. **Обратитесь в поддержку GitHub:**
   - Если релизы не появляются через 30 минут
   - Создайте тикет: https://support.github.com/

3. **Пересоздайте один релиз для теста:**
   ```powershell
   # Удалить релиз (НЕ тег)
   gh release delete v0.1.0 --yes
   
   # Создать заново
   gh release create v0.1.0 --title "v0.1.0 - Historical Release" --notes "Test"
   ```

## Временное решение

Пока релизы не отображаются на веб-странице, вы можете:

1. Использовать `gh` CLI для просмотра релизов
2. Использовать прямые ссылки на релизы
3. Клонировать репозиторий и проверить теги локально

## Статус проверки

- ✅ Все 5 семантических релизов созданы и доступны через API
- ✅ Все 7 датированных релизов созданы и доступны через API
- ✅ Все релизы корректно помечены
- ✅ Все теги существуют в удаленном репозитории
- ⏳ Ожидается обновление кэша GitHub для отображения на веб-странице

---
Дата создания: 2025-11-28 22:45:00
