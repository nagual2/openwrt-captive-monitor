# Historical Tags and Releases Restoration

---

## 🌐 Language / Язык

**English** | [Русский](#русский)

---

## 1. Background

The **openwrt-captive-monitor** project has gone through two distinct
versioning eras:

- **Semantic versioning (SemVer)** – historical releases such as `v0.1.0`,
  `v0.1.1`, `v0.1.2`, `v1.0.1`, `v1.0.3`, `v1.0.6`, `v1.0.8`.
- **Date‑based versioning** – the current scheme (`vYYYY.M.D.N`), driven by
  the manual release workflow and documented in:
  - [`docs/release/RELEASE_PROCESS.md`](RELEASE_PROCESS.md)
  - [`docs/release/AUTO_VERSION_TAG.md`](AUTO_VERSION_TAG.md)
  - [`docs/release/MANUAL_RELEASE.md`](MANUAL_RELEASE.md)

In addition, a security cleanup was performed to remove the
`security_audit/` directory from git history
(see [`SECURITY_AUDIT_REMOVAL_SUMMARY.md`](../security/SECURITY_AUDIT_REMOVAL_SUMMARY.md)).
That operation used `git filter-branch` and a force‑push on `main`. As a side
effect on GitHub:

- Some **old semantic tags and their GitHub Releases were deleted**.
- Commit SHAs referenced in older reports (for example `18ed0d0` for the
  original `v1.0.8` tag) no longer exist in the rewritten history.

This document provides:

1. An **inventory of historical semantic tags** referenced in the
   documentation.
2. Guidance on how to **check which of those tags are present or missing** in a
   given clone.
3. A **conservative restoration plan** that avoids breaking the current
   date‑based release pipeline.

> **Important:** Because history was rewritten, it is **not always possible to
> reconstruct the exact original commit SHA** for every historical tag using
> this repository alone. Where only the old SHA is known from reports, it is
> recorded here as a historical reference.

---

## 2. Inventory of historical semantic tags

The table below summarizes the semantic‑version tags that appear in the
existing documentation and reports.

| Tag     | Version files at the time | GitHub Release (historical) | Notes |
|--------|----------------------------|-----------------------------|-------|
| `v0.1.0` | `PKG_VERSION=0.1.0`, `PKG_RELEASE=1` | Yes, but **no package assets attached** (see `docs/PACKAGES.md`) | First public packaged release; initial OpenWrt integration. |
| `v0.1.1` | `PKG_VERSION=0.1.1`, `PKG_RELEASE=1` | Intended | Packaging & CI improvements; release branch `release-v0.1.1-ci-fix-ipk-build-opkg-feed-publish` mentioned in branch audits. |
| `v0.1.2` | `PKG_VERSION=0.1.2`, `PKG_RELEASE=1` | **No GitHub Release**; tag only (see `docs/PACKAGES.md`) | Documentation & CI hardening, SDK compatibility fixes. |
| `v1.0.1` | `PKG_VERSION=1.0.1`, `PKG_RELEASE=1` | CI artifacts only | First 1.x series release; extensive documentation cleanup and repo restructuring (see `CHANGELOG.md`). |
| `v1.0.3` | `PKG_VERSION=1.0.3`, `PKG_RELEASE=1` | CI artifacts only; packaging assets expected but not attached at the time (see `RELEASE_SUMMARY_v1.0.3.md` and `PACKAGES.md`) | Documentation and CI fixes; `RELEASE_SUMMARY_v1.0.3.md` describes the release in detail. |
| `v1.0.6` | `PKG_VERSION=1.0.6`, `PKG_RELEASE=1` | Local/CI builds only (no separate release doc) | Used while fixing IPK packaging issues (see `IPK_BUILD_FIX_SUMMARY.md`); not recorded in `CHANGELOG.md`. |
| `v1.0.8` | `PKG_VERSION=1.0.8`, `PKG_RELEASE=1` | Planned final 1.x release; build initially blocked, then unblocked | Detailed in the `v1.0.8` diagnostic reports: `V1_0_8_BUILD_FAILURE_DIAGNOSIS.md`, `V1_0_8_FINAL_DIAGNOSIS_COMPLETE.md`, `V1_0_8_STATUS_REPORT_FINAL.md`. |

Where known from reports, historical commit IDs are:

- **`v1.0.3`** – created from commit `f070048` (`chore: bump version to 1.0.3`)
  in the pre‑cleanup history
  (see `docs/reports/RELEASE_SUMMARY_v1.0.3.md`).
- **`v1.0.8`** – originally pointed at commit
  `18ed0d0b3ac90e483dd403120438e54f98048d6e` (no longer present after
  history cleanup; see `V1_0_8_BUILD_FAILURE_DIAGNOSIS.md`).

These SHAs are preserved here **only as historical references** – they cannot
be resolved in the current, cleaned history.

---

## 3. Diagnostic / temporary tags around v1.0.8

The v1.0.8 debugging work used additional temporary tags that may have been
created and deleted during diagnosis:

| Tag             | Historical commit | Purpose |
|----------------|-------------------|---------|
| `v1.0.8-test`  | `4c1d821` | Test tag on a fixed `main` to validate Dependency Review and branch‑protection compatibility (see `V1_0_8_BUILD_FAILURE_DIAGNOSIS.md`). |
| `v1.0.8-retry` | `efc489e` | Second test tag after workflow fixes; used to confirm that all required status checks and the tag‑build pipeline work end‑to‑end (see `V1_0_8_FINAL_DIAGNOSIS_COMPLETE.md`). |

Both tags were intended as **temporary diagnostic tags**. The final plan in the
reports was:

1. Use `v1.0.8-test` / `v1.0.8-retry` to validate the pipeline.
2. Once everything is green, **delete the test tags**.
3. Re‑create the final `v1.0.8` tag on the validated commit.

When restoring history it is usually **not necessary** to restore
`v1.0.8-test` or `v1.0.8-retry` unless you explicitly want those diagnostic
points visible in the tag list.

---

## 4. Checking which historical tags exist in a clone

To make it easy to see which semantic tags are currently present in a given
clone, a small helper script is provided:

```bash
scripts/report-historical-tags.sh
```

This script:

- Treats `v0.1.0`, `v0.1.1`, `v0.1.2`, `v1.0.1`, `v1.0.3`, `v1.0.6`, `v1.0.8`
  as the **canonical list of historical semantic tags**.
- Prints, for each tag, whether it exists locally and (if present) the short
  commit SHA.

Example output:

```text
Historical semantic-version tags status:
  Tag       Status    Target commit (if present)
  --------  --------  --------------------------
  v0.1.0    present   b91b947e
  v0.1.1    present   b91b947e
  v0.1.2    present   b91b947e
  v1.0.1    missing   —
  v1.0.3    missing   —
  v1.0.6    missing   —
  v1.0.8    missing   —
```

> **Note:** In this repository snapshot some semantic tags may have been
> re‑attached to a newer commit (for example `b91b947`), rather than their
> original semantic‑release commit. The goal of this script is simply to tell
> you **which tag names exist**, not to validate that they point to the exact
> historical tree.

---

## 5. Restoring tags safely

Because history was rewritten to remove `security_audit/`, there are two
realistic restoration strategies:

### 5.1. If you still have an archival clone with the old history

If you (or another maintainer) have a local clone **created before** the
security‑audit cleanup, that clone still contains the original commits and tag
pointers. In that case, the safest restoration strategy is:

1. **Add the current GitHub repository as a new remote** in the archival clone
   (for example `origin-clean`).
2. **Fetch the current branches** from GitHub but **do not push branches or
   tags yet**:
   
   ```bash
   git fetch origin-clean
   ```
3. From the archival clone, **re‑push the semantic tags only** to the cleaned
   repository:
   
   ```bash
   # Example: push an existing historical tag from the archival clone
   git push origin-clean refs/tags/v0.1.0
   git push origin-clean refs/tags/v0.1.1
   git push origin-clean refs/tags/v0.1.2
   git push origin-clean refs/tags/v1.0.1
   git push origin-clean refs/tags/v1.0.3
   git push origin-clean refs/tags/v1.0.6
   git push origin-clean refs/tags/v1.0.8
   ```

This approach preserves the **exact original tag → commit mapping** while
keeping the cleaned `main` branch intact.

> Do **not** push old branches from the archival clone unless you intend to
> keep them as historical references. The ticket’s scope is limited to
> restoring tags and GitHub Releases, not branch topology.

### 5.2. If the old history is no longer available

If no archival clone exists and only the cleaned history remains:

- Original SHAs like `18ed0d0` and `f070048` **cannot be resurrected**.
- You can still create **placeholder tags** with the correct names, but they
  will necessarily point at newer commits that do not exactly match the old
  trees.

In that case the recommended approach is:

1. **Keep the cleaned `main` history as the source of truth** for future work.
2. Treat semantic versions (`v0.1.x`, `v1.0.x`) as **archival labels only**.
3. If you decide to create placeholder tags for discoverability, annotate them
   very clearly, for example:

   ```bash
   git tag -a v1.0.8 <new-sha> \
     -m "Restored historical tag v1.0.8 after security-audit history cleanup (tree may differ from original)."
   git push origin v1.0.8
   ```

4. In the corresponding GitHub Releases, add a paragraph explaining that:

   - The tag was restored after a history rewrite.
   - The underlying commit identifier differs from the original.
   - Original binary artifacts are **not** reproduced.

This keeps the **naming and documentation continuity** without pretending that
we have a perfect bit‑for‑bit reconstruction of the original 1.x history.

---

## 6. Restoring GitHub Releases (without rebuilding old artifacts)

For each restored semantic tag you can recreate a GitHub Release using either
GitHub’s UI or the `gh` CLI.

### 6.1. Recommended release body

Because the current packaging and validation scripts are strictly oriented
around date‑based versions, **do not attempt to re‑run the modern
`simple-release` or `manual-release` workflows for old semantic tags.** Doing
so would produce new artifacts that may not match the original packaging
conventions.

Instead, create lightweight historical releases whose body:

- Links to the relevant documentation (changelog and reports).
- Clearly states that original artifacts are no longer available.
- Describes the role of that release in the project history.

Example using the `gh` CLI (for `v1.0.3`):

```bash
gh release create v1.0.3 \
  --title "v1.0.3 (historical release, restored)" \
  --notes-file docs/reports/RELEASE_SUMMARY_v1.0.3.md
```

For tags where no dedicated summary exists, you can point to the changelog:

```bash
gh release create v0.1.2 \
  --title "v0.1.2 (historical release, restored)" \
  --notes "Restored historical release. See docs/release/CHANGELOG.md for details. Binary artifacts from the original CI runs are no longer available."
```

In all cases, **do not upload newly built `.ipk` files under old semantic
version numbers** unless you have a strong reason and have independently
validated that the resulting metadata matches the historical expectations.

### 6.2. Interaction with the current date‑based workflows

The current workflows are deliberately scoped so that restoring semantic tags
**does not trigger unwanted builds**:

- `simple-release.yml` only reacts to tags matching
  `v[0-9][0-9][0-9][0-9].[0-9]*.[0-9]*.[0-9]*`
  (date‑based `vYYYY.M.D.N`).
- `manual-release.yml` is `workflow_dispatch` only and always uses the date‑
  based format.
- `auto-version-tag.yml` is disabled by default and can only be run manually.
- CI (`ci.yml`) and security scanning (`security-scanning.yml`) run on
  **branches**, not on tag creation.

As a result, re‑creating semantic tags like `v1.0.3` or `v1.0.8` will **not
trigger the modern date‑based release workflows** and will not interfere with
current versioning rules.

---

## 7. How to interpret old vs new releases

- **Semantic releases (`v0.1.x`, `v1.0.x`)**
  - Represent the project’s early evolution.
  - Are documented primarily through:
    - `docs/release/CHANGELOG.md`
    - `docs/reports/RELEASE_SUMMARY_v1.0.3.md`
    - The various `v1.0.8` diagnostic reports under `docs/reports/`.
  - May not have downloadable `.ipk` assets anymore.

- **Date‑based releases (`vYYYY.M.D.N`)**
  - Are the **canonical, supported releases going forward**.
  - Are created via the **Manual Release** workflow
    (`.github/workflows/manual-release.yml`).
  - Keep `VERSION`, `PKG_VERSION`, and `PKG_RELEASE` fully in sync and are
    validated by modern tooling such as `scripts/validate-ipk-version.sh` and
    `scripts/update-version-metadata.sh`.

When in doubt:

- Prefer the **latest date‑based release** for production use.
- Treat semantic releases as **historical snapshots** that are useful for
  auditing and documentation, but not as the primary upgrade target.

---

<a name="русский"></a>

## Русский

---

## 1. Контекст

Проект **openwrt-captive-monitor** использовал две схемы версионирования:

- **Семантическое версионирование (SemVer)** – исторические релизы
  `v0.1.0`, `v0.1.1`, `v0.1.2`, `v1.0.1`, `v1.0.3`, `v1.0.6`, `v1.0.8`.
- **Датированное версионирование** – текущая схема (`vYYYY.M.D.N`),
  управляемая ручным workflow `Manual Release` и описанная в:
  - [`RELEASE_PROCESS.md`](RELEASE_PROCESS.md)
  - [`AUTO_VERSION_TAG.md`](AUTO_VERSION_TAG.md)
  - [`MANUAL_RELEASE.md`](MANUAL_RELEASE.md)

Позже из истории репозитория был безвозвратно удалён каталог
`security_audit/` (см.
[`SECURITY_AUDIT_REMOVAL_SUMMARY.md`](../security/SECURITY_AUDIT_REMOVAL_SUMMARY.md)).
Для этого использовался `git filter-branch` с последующим **force‑push** ветки
`main`. Побочный эффект на GitHub:

- Некоторые старые **семантические теги и соответствующие GitHub Releases были
  удалены**.
- SHA‑хэши из старых отчётов (например, `18ed0d0` для исходного тега
  `v1.0.8`) больше не существуют в очищенной истории.

Этот документ:

1. Фиксирует **инвентарь исторических семантических тегов**.
2. Описывает, как **проверить, какие из них присутствуют или отсутствуют** в
   конкретном клоне.
3. Даёт **осторожный план восстановления**, который **не ломает** текущую
   датированную схему релизов.

> **Важно:** из‑за переписи истории **невозможно во всех случаях восстановить
> исходный коммит для каждого тега**, опираясь только на текущий репозиторий.
> Там, где известен только старый SHA из отчётов, он сохранён здесь как
> историческая ссылка.

---

## 2. Инвентарь исторических семантических тегов

Ниже приведены теги SemVer, которые упоминаются в существующей документации и
отчётах.

| Тег     | Версионные файлы на тот момент     | GitHub Release (исторически) | Примечания |
|---------|------------------------------------|-------------------------------|-----------|
| `v0.1.0` | `PKG_VERSION=0.1.0`, `PKG_RELEASE=1` | Есть релиз, **без прикреплённых пакетов** (см. `docs/PACKAGES.md`) | Первый публичный релиз пакета. |
| `v0.1.1` | `PKG_VERSION=0.1.1`, `PKG_RELEASE=1` | Планировался | Улучшения упаковки и CI; в отчётах фигурирует ветка `release-v0.1.1-…`. |
| `v0.1.2` | `PKG_VERSION=0.1.2`, `PKG_RELEASE=1` | **Релиз не создавался**, только тег (см. `docs/PACKAGES.md`) | Документация и усиление CI. |
| `v1.0.1` | `PKG_VERSION=1.0.1`, `PKG_RELEASE=1` | Только артефакты CI | Первый релиз линейки 1.x; крупная чистка документации (см. `CHANGELOG.md`). |
| `v1.0.3` | `PKG_VERSION=1.0.3`, `PKG_RELEASE=1` | Только артефакты CI; пакеты ожидались, но не были прикреплены (см. `RELEASE_SUMMARY_v1.0.3.md`, `PACKAGES.md`) | Исправления документации и CI. |
| `v1.0.6` | `PKG_VERSION=1.0.6`, `PKG_RELEASE=1` | Локальные/CI‑сборки | Использовалась при отладке упаковки IPK (см. `IPK_BUILD_FIX_SUMMARY.md`); в `CHANGELOG.md` не отражена. |
| `v1.0.8` | `PKG_VERSION=1.0.8`, `PKG_RELEASE=1` | Планировался финальный релиз 1.x; первоначально сборка была заблокирована, затем разблокирована | Подробно описана в отчётах `V1_0_8_*` в каталоге `docs/reports/`. |

Из отчётов известны следующие исторические SHA:

- **`v1.0.3`** – тег был создан от коммита `f070048`
  (`chore: bump version to 1.0.3`) в доочищенной истории
  (см. `RELEASE_SUMMARY_v1.0.3.md`).
- **`v1.0.8`** – изначально указывал на коммит
  `18ed0d0b3ac90e483dd403120438e54f98048d6e`
  (см. `V1_0_8_BUILD_FAILURE_DIAGNOSIS.md`), который больше не существует в
  текущей истории.

Эти SHA приведены **только как историческая справка**.

---

## 3. Диагностические / временные теги вокруг v1.0.8

При отладке `v1.0.8` использовались дополнительные временные теги:

| Тег             | Исторический коммит | Назначение |
|-----------------|---------------------|-----------|
| `v1.0.8-test`  | `4c1d821` | Тестовый тег на исправленном `main` для проверки Dependency Review и правил защиты ветки. |
| `v1.0.8-retry` | `efc489e` | Второй тестовый тег после доработки workflow; использовался для проверки полного конвейера сборки и релиза. |

Согласно отчётам, итоговый план был таким:

1. Использовать `v1.0.8-test` / `v1.0.8-retry` для диагностики.
2. После успешных прогонов **удалить тестовые теги**.
3. Создать финальный `v1.0.8` на проверенном коммите.

При восстановлении истории обычно **нет необходимости** восстанавливать
`t`v1.0.8-test` и `v1.0.8-retry`, если только вы сознательно не хотите видеть
их в списке тегов.

---

## 4. Проверка наличия тегов в локальном клоне

Для удобства добавлен маленький скрипт:

```bash
scripts/report-historical-tags.sh
```

Скрипт:

- считает `v0.1.0`, `v0.1.1`, `v0.1.2`, `v1.0.1`, `v1.0.3`, `v1.0.6`, `v1.0.8`
  **каноническим списком исторических семантических тегов**;
- для каждого тега выводит, существует ли он локально, и (если да) короткий
  SHA коммита.

---

## 5. Безопасное восстановление тегов

Из‑за переписи истории существуют два основных сценария восстановления:

### 5.1. Если у вас есть архивный клон со старой историей

Лучший вариант – использовать локальный клон, созданный **до** очистки
истории:

1. Добавьте текущий GitHub‑репозиторий как новый `remote` (например,
   `origin-clean`).
2. Выполните `git fetch origin-clean`, не выполняя push веток или тегов.
3. Перепушьте **только теги** (`v0.1.x`, `v1.0.x`) из архивного клона в
   очищенный репозиторий, как показано в английском разделе.

Так вы сохраните исходное соответствие «тег → коммит», не трогая очищенную
ветку `main`.

### 5.2. Если старая история недоступна

Если старые коммиты потеряны и осталась только очищенная история:

- теги можно восстановить только как **плейсхолдеры** (указатели на новые
  коммиты);
- в GitHub Releases необходимо явно указать, что это восстановленные
  исторические релизы без оригинальных артефактов.

Рекомендуется:

1. Считать датированные теги (`vYYYY.M.D.N`) единственным источником правды
   для текущих релизов.
2. Использовать теги `v0.1.x` и `v1.0.x` только как **архивные маркеры**.
3. Если вы всё‑таки создаёте плейсхолдер‑теги, добавьте в сообщение тега и
   тело релиза явное пояснение, что это восстановленный исторический тег, а
   бинарные артефакты не воспроизводились.

---

## 6. Восстановление GitHub Releases (без пересборки старых артефактов)

Для каждого восстановленного семантического тега можно создать GitHub Release
через веб‑интерфейс или `gh` CLI. Рекомендуется **не запускать** современные
workflow `simple-release` / `manual-release` для старых SemVer‑тегов, чтобы не
получать новые артефакты под старыми номерами версий.

Вместо этого создавайте лёгкие исторические релизы с телом, которое:

- ссылается на соответствующую документацию (changelog, отчёты);
- явно говорит об отсутствии оригинальных бинарных артефактов;
- описывает роль релиза в истории проекта.

---

## 7. Как интерпретировать старые и новые релизы

- **Семантические релизы (`v0.1.x`, `v1.0.x`)** – исторические снимки,
  полезные для аудита и понимания эволюции проекта.
- **Датированные релизы (`vYYYY.M.D.N`)** – **актуальная и поддерживаемая
  линия релизов**, создаваемая через workflow `Manual Release`.

Для продакшена рекомендуется использовать **последний датированный релиз** и
считать SemVer‑теги только исторической справкой.
