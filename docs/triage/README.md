# Triage & Audit Reports

---

## 🌐 Language / Язык

**English** | [Русский](README.ru.md)

---

This directory contains PR queue audit reports and triage artifacts for the `openwrt-captive-monitor` repository.

## Current Status

📊 **Latest Audit:** No current audit reports available

**Summary:** ✅ **0 open PRs** - Queue clean, all tests passing

## Files in This Directory

### Templates and Label Management

- [TEMPLATES_AND_LABELS.md](./TEMPLATES_AND_LABELS.md) - Guide to modernized issue/PR templates and label taxonomy
  - GitHub Issue Forms usage and triage processes
  - PR template structure and review checklist
  - Label taxonomy and synchronization workflow
  - Best practices for issue and PR triage

### Audit Reports

- No current audit reports available. Previous reports have been archived as part of repository cleanup.

### API Snapshots

- **pr-status-20251030T123851Z.json** - GitHub API response snapshot
  - Captured during 2025-10-30 audit
  - Shows empty PR queue at audit time

## Related Documentation

For historical context and prior triage work, see:

- [../project/BRANCHES_PR_AUDIT.md](../project/BRANCHES_PR_AUDIT.md) - Original branch & PR inventory (2025-10-24)
   - Documents 17 PRs that existed before comprehensive triage
   - Provides cleanup checklist and branching strategy

- [../project/PR_TRIAGE.md](../project/PR_TRIAGE.md) - Detailed triage analysis (2025-10-24)
   - Explains closure rationale for PRs #6, #11, #12
   - Documents prior triage of PRs #1-#2

- CI health tracking information has been archived as part of repository cleanup

## Audit Process

PR queue audits follow this process:

1. **Query GitHub API** for open pull requests
2. **Analyze each PR** for conflicts, CI status, merge readiness
3. **Run baseline tests** on main branch
4. **Document findings** in audit report
5. **Capture API snapshot** for historical record

## When to Run Next Audit

- **Frequency:** Monthly or when PR count exceeds 5
- **Trigger:** After major merges or releases
- **Process:** Follow `docs/RELEASE_CHECKLIST.md` guidelines

## Contributing

When conducting PR triage:

1. Review existing audit reports in this directory
2. Follow trunk-based workflow from `BRANCHES_AND_MERGE_POLICY.md`
3. Document closure rationale for declined PRs
4. Archive audit reports after completion

---

**Last updated:** 2025-10-30

---

# Русский

---

## 🌐 Язык

[English](#triage--audit-reports) | **Русский**

---

# Тестирование и отчеты аудита

Этот каталог содержит отчеты аудита очереди PR и артефакты тестирования для репозитория `openwrt-captive-monitor`.

## Текущий статус

📊 **Последний аудит:** Текущих отчетов об аудите нет

**Резюме:** ✅ **0 открытых PR** - Очередь чистая, все тесты проходят

## Файлы в этом каталоге

### Шаблоны и управление метками

- [TEMPLATES_AND_LABELS.md](./TEMPLATES_AND_LABELS.md) - Руководство по модернизированным шаблонам задач/PR и таксономии меток
  - Использование GitHub Issue Forms и процессы тестирования
  - Структура шаблона PR и контрольный список проверки
  - Таксономия меток и рабочий процесс синхронизации
  - Лучшие практики тестирования и PR

### Отчеты об аудите

- Текущих отчетов об аудите нет. Предыдущие отчеты были архивированы как часть очистки репозитория.

### Снимки API

- **pr-status-20251030T123851Z.json** - Снимок ответа GitHub API
  - Захвачено во время аудита 2025-10-30
  - Показывает пустую очередь PR на момент аудита

## Связанная документация

Для исторического контекста и предыдущих работ тестирования см.:

- [../project/BRANCHES_PR_AUDIT.md](../project/BRANCHES_PR_AUDIT.md) - Исходный инвентарь ветвей и PR (2025-10-24)
   - Документирует 17 PR, существовавших до комплексного тестирования
   - Предоставляет контрольный список очистки и стратегию ветвления

- [../project/PR_TRIAGE.md](../project/PR_TRIAGE.md) - Подробный анализ тестирования (2025-10-24)
   - Объясняет рациональ закрытия PR #6, #11, #12
   - Документирует предыдущее тестирование PR #1-#2

- Информация отслеживания здоровья CI была архивирована как часть очистки репозитория

## Процесс аудита

Аудиты очереди PR следуют этому процессу:

1. **Запрос GitHub API** для открытых pull request
2. **Анализ каждого PR** на конфликты, статус CI, готовность слияния
3. **Запуск базовых тестов** на ветке main
4. **Документирование результатов** в отчете об аудите
5. **Захват снимка API** для исторического учета

## Когда запустить следующий аудит

- **Частота:** Ежемесячно или когда количество PR превышает 5
- **Триггер:** После крупных слияний или выпусков
- **Процесс:** Следуйте рекомендациям из `docs/RELEASE_CHECKLIST.md`

## Внесение вклада

При проведении PR тестирования:

1. Проверьте существующие отчеты об аудите в этом каталоге
2. Следуйте рабочему процессу на основе ствола из `BRANCHES_AND_MERGE_POLICY.md`
3. Документируйте рациональ закрытия отклоненных PR
4. Архивируйте отчеты об аудите после завершения
