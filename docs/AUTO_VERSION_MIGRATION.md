# Migration to Date-Based Auto-Versioning

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---

## Summary

The project has migrated from **semantic versioning (v1.2.3)** to **date-based auto-versioning (vYYYY.M.D.N)**.

## Key Changes

### Version Format

**Before (Semantic Versioning):**
```
v1.0.0, v1.1.0, v1.2.3
```

**After (Date-Based):**
```
v2025.1.15.1, v2025.1.15.2, v2025.12.3.1
```

### Version Format Details

- `YYYY` - Year (4 digits)
- `M` - Month (1-12, no leading zeros)
- `D` - Day (1-31, no leading zeros)
- `N` - Sequential number (starts at 1 each day)

## What Changed

### 1. New Workflow

**File:** `.github/workflows/auto-version-tag.yml`

This workflow automatically:
- Triggers on every push to `main` branch
- Calculates the next version based on current date
- Creates a git tag
- Creates a GitHub Release with commit history
- Triggers the build workflow

### 2. Updated Documentation

**New Documentation:**
- [`docs/release/AUTO_VERSION_TAG.md`](./release/AUTO_VERSION_TAG.md) - Complete guide to the new system

**Updated Documentation:**
- [`docs/release/RELEASE_PROCESS.md`](./release/RELEASE_PROCESS.md) - Marked as legacy
- [`docs/release/README.md`](./release/README.md) - Updated to reference new system

### 3. Test Script

**File:** `scripts/test-version-calculation.sh`

Script to test version calculation logic locally.

## How It Works

### Automatic Release on Merge

```
Developer merges PR to main
          ↓
Auto-version workflow triggers
          ↓
Calculate next version (e.g., v2025.1.15.1)
          ↓
Create and push git tag
          ↓
Create GitHub Release with commit history
          ↓
Build workflow triggers (tag-build-release.yml)
          ↓
Artifacts built and attached to release
```

### Multiple Releases Same Day

The system handles multiple releases on the same day:

```
First merge today  → v2025.1.15.1
Second merge today → v2025.1.15.2
Third merge today  → v2025.1.15.3
```

Next day:
```
First merge tomorrow → v2025.1.16.1  (resets to .1)
```

## Benefits

### Advantages of Date-Based Versioning

1. **Simplicity** - No need to decide on version bump size
2. **Automatic** - Every merge creates a release automatically
3. **Traceable** - Version includes the release date
4. **Predictable** - Same format every time
5. **No Conflicts** - No merge conflicts on version files

### Use Cases

Date-based versioning is ideal for:
- Applications (not libraries)
- Time-sensitive releases
- Continuous deployment
- Projects where release date matters more than API compatibility

## Migration Guide

### For Developers

**No changes needed!** Just merge to main as usual:

```bash
# Before (with Release Please)
git commit -m "feat: add new feature"  # Requires conventional commits
git push

# After (with Auto-Version)
git commit -m "add new feature"  # Any commit message works
git push
# → Automatically creates v2025.1.15.1
```

**Best Practices:**
- Write clear commit messages (they appear in release notes)
- Ensure CI passes before merging
- Monitor the Actions tab after merge

### For Users

**Existing releases are preserved.** Old semantic versions (v1.0.0, etc.) remain available.

**Finding releases:**
- Latest release: Always the newest date-based tag
- Specific date: Search for `v2025.1.15.*`
- All releases: Visit the [Releases page](https://github.com/nagual2/openwrt-captive-monitor/releases)

### For CI/CD

**Build workflow unchanged.** The `tag-build-release.yml` workflow still triggers on any `v*` tag, so it works with both formats.

**Status checks unchanged.** Branch protection rules remain the same.

## Backward Compatibility

### Existing Tags

All existing semantic version tags are preserved:
- `v1.0.0`
- `v1.1.0`
- `v1.2.3`
- etc.

These remain accessible and functional.

### Co-existence

The new date-based tags co-exist with old semantic tags:

```
Existing tags:     v1.0.0, v1.1.0, v1.2.3
New tags:          v2025.1.15.1, v2025.1.15.2
```

Both formats work with the build workflow.

## Testing

### Test Version Calculation

Run the test script to validate the logic:

```bash
./scripts/test-version-calculation.sh
```

This tests:
- Version calculation with various tag scenarios
- Pattern matching for valid/invalid tags
- Edge cases (large sequence numbers, non-sequential tags)

### Verify Workflow

Check the workflow is valid:

```bash
./actionlint .github/workflows/auto-version-tag.yml
```

## Troubleshooting

### "Tag already exists" Error

**Cause:** A tag was already created for today's date and sequence.

**Solution:** This is normal if the workflow ran multiple times. The workflow will skip tag creation gracefully.

### No Release Created

**Cause:** Possible GitHub API rate limit or permissions issue.

**Solution:**
1. Check workflow logs in Actions tab
2. Verify `contents: write` permission
3. Manually create release if needed: `gh release create v2025.1.15.1`

### Build Not Triggered

**Cause:** Build workflow not watching for the new tag.

**Solution:** Verify `tag-build-release.yml` has `tags: ['v*']` trigger pattern.

## Rollback Plan

If needed, you can revert to Release Please:

1. Disable auto-version workflow:
   ```bash
   mv .github/workflows/auto-version-tag.yml .github/workflows/auto-version-tag.yml.disabled
   ```

2. Re-enable Release Please (it's still present in `release-please.yml`)

3. Continue using conventional commits for version control

## Questions & Support

### Where to Get Help

- **Documentation:** [`docs/release/AUTO_VERSION_TAG.md`](./release/AUTO_VERSION_TAG.md)
- **Test Script:** `./scripts/test-version-calculation.sh`
- **Issues:** Open an issue on GitHub
- **Workflow Logs:** Check the Actions tab

### Common Questions

**Q: Can I use semantic versioning again?**  
A: Yes, just disable the auto-version workflow and use Release Please.

**Q: What happens to VERSION file?**  
A: It's no longer automatically updated. Manual updates may be needed for package builds.

**Q: Can I create tags manually?**  
A: Yes, but use the date format: `v2025.1.15.1`

**Q: How do I know what changed in a release?**  
A: Check the release notes in GitHub Releases - they list all commits.

**Q: Can I skip a release?**  
A: Disable the workflow temporarily before merging, or merge to a different branch first.

## Timeline

- **Previous System:** Release Please (semantic versioning)
- **Migration Date:** January 2025
- **New System:** Date-based auto-versioning

## Related Documentation

- [Auto Version Tag Guide](./release/AUTO_VERSION_TAG.md) - Complete user guide
- [Release Process (Legacy)](./release/RELEASE_PROCESS.md) - Historical documentation
- [Release Documentation](./release/README.md) - Release documentation index

---

**Last Updated:** January 2025  
**Migration Status:** ✅ Complete

---

# Русский

---

## 🌐 Язык

[English](#migration-to-date-based-auto-versioning) | **Русский**

---

## Краткое резюме

Проект переключился с **семантического версионирования (v1.2.3)** на **датированное авто‑версионирование (vYYYY.M.D.N)**. Новая схема автоматически создаёт теги и релизы при каждом push'е в ветку `main`, а номера версий напрямую привязаны к дате релиза.

## Основные изменения

- **Формат версий**:
  - Было: `vMAJOR.MINOR.PATCH` (например, `v1.2.3`).
  - Стало: `vYYYY.M.D.N` (например, `v2025.1.15.1`).
- **Workflow**:
  - Новый workflow `auto-version-tag.yml` запускается на каждый push в `main`.
  - Находит существующие теги за текущую дату и рассчитывает следующий порядковый номер `N`.
  - Создаёт тег и GitHub‑релиз с простыми release notes на основе списка коммитов.
  - Тег автоматически запускает сборочный workflow `tag-build-release.yml`.
- **Документация**:
  - Добавлен подробный гайд `docs/release/AUTO_VERSION_TAG.md`.
  - `docs/release/RELEASE_PROCESS.md` помечен как наследуемый (legacy).

## Как работает авто‑версионирование

- При каждом merge в `main` workflow:
  - Подтягивает все существующие теги.
  - Определяет, есть ли теги за текущую дату (`vYYYY.M.D.*`).
  - Устанавливает `N = 1`, если тегов нет, или `N = max(existing) + 1`.
  - Создаёт новый тег `vYYYY.M.D.N` и связанный релиз с краткой историей изменений.
- Если тег уже существует (например, создан вручную), workflow пропускает создание и не ломает сборку.

## Причины перехода

- **Проще для приложений, чем для библиотек**: важна дата релиза, а не API‑совместимость.
- **Упрощение процесса**: разработчикам не нужно решать, какой bump (major/minor/patch) делать — каждая интеграция в `main` даёт новый тег.
- **Отсутствие конфликтов по версии**: не нужно редактировать `VERSION` в каждом PR, нет merge‑конфликтов в файлах с номером версии.
- **Прозрачность**: по тегу сразу видно, когда произошёл релиз.

## Влияние на разработчиков и пользователей

- **Разработчикам**:
  - Больше не требуется жёстко следовать Conventional Commits для управления номером версии (хотя стиль коммитов по‑прежнему полезен для changelog'ов).
  - Достаточно мёрджить PR'ы в `main`; теги и релизы появятся автоматически.
- **Пользователям**:
  - Старые семантические теги (`v1.0.0`, `v1.1.0` и т.д.) остаются доступными.
  - Актуальная версия — это последний датированный тег.
  - Для поиска релиза по дате можно использовать шаблон `vYYYY.M.D.*`.

## Совместимость с существующим процессом релизов

- Workflow `tag-build-release.yml` продолжает реагировать на любые теги `v*` — как семантические, так и датированные.
- Проверки безопасности, линтинга и тестов остаются без изменений.
- Старый процесс на базе Release Please можно при необходимости
  временно вернуть, отключив `auto-version-tag.yml` и снова полагаясь на `release-please.yml`.

## FAQ (кратко)

- **Что будет с файлом `VERSION`?**  
  Он больше не обновляется автоматически; при необходимости его можно обновлять вручную для отдельных сценариев (например, для сборки пакетов).

- **Можно ли создавать теги вручную?**  
  Да, но желательно придерживаться формата `vYYYY.M.D.N`.

- **Можно ли пропустить релиз?**  
  Можно временно отключить workflow или мёрджить изменения во вспомогательную ветку, а затем уже в `main`.

## Дополнительные материалы

- `docs/release/AUTO_VERSION_TAG.md` — подробный пользовательский гайд по авто‑версионированию.
- `docs/release/RELEASE_PROCESS.md` — историческое описание процесса на базе Release Please.
- `docs/release/README.md` — индекс документации по релизам.
