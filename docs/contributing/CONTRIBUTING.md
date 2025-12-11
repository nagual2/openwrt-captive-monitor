# Contributing to openwrt-captive-monitor

---

## 🌐 Language / Язык

**English** | [Русский](README.ru.md)

---


Thanks for taking the time to contribute! This project keeps OpenWrt routers online by recovering from captive portals and flaky uplinks, so changes need to be safe, reviewable, and well documented.

Please read our [Contributor Code of Conduct](CODE_OF_CONDUCT.md) to understand the expectations for community participation.

The repository follows a **trunk-based** workflow centred on the `main` branch. Short-lived topic branches, small pull requests, and fast feedback from CI keep releases predictable.

---

## 1. Branching model

1. Start from the latest `main` and keep your branch up to date by rebasing before opening a pull request.
2. Use descriptive branch prefixes:
   - `feature/<short-description>` for new capabilities
   - `fix/<short-description>` for bug fixes or regressions
   - `chore/<short-description>` for tooling, CI, or maintenance work
   - `docs/<short-description>` for documentation-only updates
   - `hotfix/<short-description>` for urgent production fixes that must land ahead of the regular release cadence
   Refer to [`BRANCHES_AND_MERGE_POLICY.md`](./docs/project/BRANCHES_AND_MERGE_POLICY.md) for the latest merge sequencing, branch protection checklist, and cleanup tasks.
3. Prefer incremental pull requests (aim for < ~300 lines of net change). Split large efforts into multiple PRs that can be reviewed independently.
4. Avoid long-lived release branches. If you need to ship a hotfix, branch from the appropriate tag, cherry-pick the fix, release, and merge the change back into `main` immediately afterwards.

### Why trunk-based over GitFlow?

Trunk-based development keeps the integration surface small, which is important for shell tooling that is hard to test exhaustively.
GitFlow introduces long-running `develop` and release branches that often diverge and amplify merge conflicts.
Unless you are maintaining multiple historical versions in parallel, GitFlow's additional ceremony rarely pays off here.

If the project eventually needs LTS maintenance, treat it as an exception: cut a release branch, backport critical changes, and retire the branch after support ends.


---

## 2. Local development workflow

1. Clone the repository and install the linting dependencies:
    ```bash
    git clone https://github.com/nagual2/openwrt-captive-monitor.git
    cd openwrt-captive-monitor
    sudo apt-get update && sudo apt-get install -y shellcheck shfmt npm nodejs
    npm install -g markdownlint-cli
    # For actionlint (optional, runs in CI)
    go install github.com/rhysd/actionlint/cmd/actionlint@latest
    ```
2. Create a topic branch following the naming rules above.
3. Make your changes and keep commits focused. Conventional Commit prefixes (`feat(wifi): …`, `fix(ci): …`, etc.) match the existing history and feed changelog automation.
4. Before pushing:
    ```bash
    # Shell formatting
    shfmt -w openwrt_captive_monitor.sh init.d/captive-monitor \
          package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor \
          package/openwrt-captive-monitor/files/etc/init.d/captive-monitor \
          package/openwrt-captive-monitor/files/etc/uci-defaults/99-captive-monitor \
          scripts/build_ipk.sh

    # Shell linting
    shellcheck openwrt_captive_monitor.sh init.d/captive-monitor \
               package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor \
               package/openwrt-captive-monitor/files/etc/init.d/captive-monitor \
               package/openwrt-captive-monitor/files/etc/uci-defaults/99-captive-monitor \
               scripts/build_ipk.sh

    # Markdown linting
    markdownlint "**/*.md" --ignore node_modules

    # Action linting (optional)
    actionlint .github/workflows/*.yml
    ```
5. Run any additional smoke tests that apply (e.g. running the script in `oneshot` mode, packaging via `scripts/build_ipk.sh`, or deploying to a test router).
6. Rebase on top of the latest `main` and resolve conflicts locally before opening the PR.

> Tip: use `git rebase --onto` if you need to drop unrelated commits that slipped into older branches. Keeping branches short-lived eliminates most painful rebases.

---

## 3. Pull request expectations

- Fill out the PR template. It captures the summary, testing evidence, and review checklist all in one place.
- Link the relevant issue or explain the motivation in the summary so that reviewers have context.
- Request at least one reviewer (see [`CODEOWNERS`](./.github/CODEOWNERS)) and wait for an approval before merging. Self-approval is reserved for docs-only or CI-only changes with no risk.
- Ensure the GitHub Actions jobs finish green:
  - `lint (shfmt)`, `lint (shellcheck)`, `lint (markdownlint)`, `lint (actionlint)`
  - `test`
  - `build (generic)` (or other relevant matrix targets when packaging files change)
- Squash-and-merge is the default. If a branch contains several independently useful commits, mention it explicitly in the PR so the reviewer can choose "Rebase and merge" instead.

---

## 4. Branch protection & automation

The `main` branch is protected by GitHub branch protection rules to ensure code quality and security. **All pull requests must pass all status checks before they can be merged.**

### Required Status Checks

Before your pull request can be merged to `main`, all of the following status checks must pass:

**Linting & Formatting:**
- `Lint (shfmt)` - Shell script formatting
- `Lint (shellcheck)` - Shell script linting
- `Lint (markdownlint)` - Markdown file validation
- `Lint (actionlint)` - GitHub Actions workflow validation

**Testing:**
- `Test` - Unit and integration tests

**Security Scanning:**
- `ShellCheck Security Analysis` - Shell script security analysis
- `Dependency Review` - Dependency vulnerability checks (PRs only)
- `Trivy Security Scan` - Vulnerability and misconfiguration scanning

### Merge Requirements

Repository administrators maintain the following settings on `main`:

- ✅ **Pull request reviews required**: Minimum 1 approval from a code owner
- ✅ **Status checks required**: ALL checks listed above must pass
- ✅ **Up-to-date branches required**: Branch must be rebased on the latest `main` before merging
- ✅ **Linear history**: No merge commits allowed; squash merging is required
- ✅ **Stale reviews dismissed**: Reviews are automatically dismissed when new commits are pushed
- ✅ **Conversations required**: All review conversations must be resolved before merging
- ✅ **Push restrictions**: Only maintainers can push directly to `main`; all others must use pull requests
- ✅ **Merge strategy**: Only squash merges allowed (merge commits and rebase merges are disabled)
- ✅ **Branch cleanup**: Branches are automatically deleted after merge
- ❌ **Force pushes blocked**: No force pushes allowed to `main`
- ❌ **Branch deletion blocked**: The `main` branch cannot be deleted

For detailed information about how these rules interact with the security scanning pipeline, see [`.github/SECURITY.md`](./.github/SECURITY.md).

### Configuration Location

These branch protection rules are codified in [`.github/settings.yml`](./.github/settings.yml) and enforced by GitHub's branch protection system.

---

## 5. Issue triage & support

- Use the GitHub Issue Forms to provide structured bug reports, feature requests, support questions, and documentation issues.
  The forms guide you through providing the necessary information for effective triage.
- For detailed guidance on templates and label usage, see [docs/triage/TEMPLATES_AND_LABELS.md](./docs/triage/TEMPLATES_AND_LABELS.md).
- Security problems should go through the private disclosure channel listed in our [Security Policy](.github/SECURITY.md) or GitHub security advisories.
- Tag issues with `good-first-issue` when they have a clear scope and minimal risk so newcomers can help.

---

## 6. Releases

Releases are created manually by maintainers using the **Manual Release** GitHub Actions workflow.

### Creating a Release

1. Ensure all changes are merged to `main` and all CI checks pass
2. Go to **Actions** → **Manual Release** in the GitHub repository
3. Click **"Run workflow"** and configure:
   - **Custom version** (optional): Specify version like `2025.11.27.1`, or leave empty for auto-generation
   - **Release notes** (optional): Provide custom notes, or leave empty for automatic generation
   - **Pre-release** (optional): Check to mark as pre-release
4. Click **"Run workflow"** to start the release

### What the Workflow Does

The Manual Release workflow automatically:
- Generates or uses the specified version tag (`vYYYY.M.D.N`)
- Updates `VERSION` file and `PKG_VERSION` in Makefile
- Creates a commit with version changes
- Creates and pushes a git tag
- Builds the universal package (`arch=all`)
- Validates the package
- Creates a GitHub Release with artifacts attached

### Manual Release (Advanced)

If you need to create a release manually without the workflow:

1. Update `CHANGELOG.md`, `docs/releases/`, and any other relevant docs
2. Assemble a local `.ipk` for validation:
   ```bash
   scripts/build_ipk.sh --arch all
   ```
3. Update version metadata:
   ```bash
   ./scripts/update-version-metadata.sh "2025.11.27.1"
   ```
4. Commit, tag, and push:
   ```bash
   git add VERSION package/openwrt-captive-monitor/Makefile
   git commit -m "chore: bump version to 2025.11.27.1"
   git push origin main
   git tag -a v2025.11.27.1 -m "Release v2025.11.27.1"
   git push origin v2025.11.27.1
   ```
5. Create the GitHub Release and upload artifacts manually

### Hotfixes

If a regression requires a hotfix:
1. Branch from the affected tag
2. Apply the fix
3. Build and test locally
4. Use the Manual Release workflow to create a hotfix release
5. Cherry-pick the change back into `main` immediately

### Important Notes

- **Do not create tags manually** - use the Manual Release workflow
- **Version format**: `vYYYY.M.D.N` (e.g., `v2025.11.27.1`)
- **PKG_RELEASE**: Always `1` for official releases
- **Automatic releases disabled**: The auto-version workflow is disabled to prevent unintended releases

---

## 7. Getting help

- Support options and guidance are available in our [Support Guide](.github/SUPPORT.md)
- Discussions: open a GitHub Discussion or issue with the `question` label.
- Real-world testing: share reproducible steps and logs in the PR or issue so maintainers can validate on similar hardware.
- Documentation updates: if anything in this guide is unclear, submit a PR – meta-contributions are welcome!

Thanks again for helping keep captive portal recovery on OpenWrt routers robust and user friendly.

---

## Русский

---

## 🌐 Язык

[English](#contributing-to-openwrt-captive-monitor) | **Русский**

---

## Вклад в openwrt-captive-monitor

Благодарим за то, что уделили время для вклада! Этот проект поддерживает маршрутизаторы OpenWrt в сети, восстанавливая соединение после порталов аутентификации и нестабильных подключений, поэтому изменения должны быть безопасными, проверяемыми и хорошо документированными.

Пожалуйста, прочитайте наш [Кодекс поведения участников](CODE_OF_CONDUCT.md), чтобы понять ожидания от участия в сообществе.

Репозиторий следует **trunk-based** рабочему процессу, центрированному на ветке `main`. Короткоживущие тематические ветки, небольшие pull request'ы и быстрая обратная связь от CI делают выпуски предсказуемыми.

---

## 1. Модель ветвления

1. Начните с последней `main` и поддерживайте свою ветку в актуальном состоянии с помощью rebase перед открытием pull request.
2. Используйте описательные префиксы веток:
   - `feature/<краткое-описание>` для новых возможностей
   - `fix/<краткое-описание>` для исправлений ошибок или регрессий
   - `chore/<краткое-описание>` для инструментов, CI или работ по обслуживанию
   - `docs/<краткое-описание>` для обновлений только документации
   - `hotfix/<краткое-описание>` для срочных исправлений в продакшене, которые должны попасть раньше регулярного цикла выпуска
   Ссылайтесь на [`BRANCHES_AND_MERGE_POLICY.md`](./docs/project/BRANCHES_AND_MERGE_POLICY.md) для получения последней последовательности слияния, контрольного списка защиты веток и задач очистки.
3. Предпочитайте инкрементальные pull request'ы (цель < ~300 строк чистых изменений). Разделите большие усилия на несколько PR, которые могут быть рассмотрены независимо.
4. Избегайте долгоживущих веток выпуска. Если вам нужно выпустить hotfix, создайте ветку от соответствующего тега, примените исправление, выпустите и немедленно слейте изменения обратно в `main`.

### Почему trunk-based вместо GitFlow?

Trunk-based разработка сохраняет небольшую поверхность интеграции, что важно для shell инструментов, которые трудно исчерпывающе протестировать.
GitFlow вводит долгоживущие ветки `develop` и выпуска, которые часто расходятся и усиливают конфликты слияния.
Если вы не поддерживаете несколько исторических версий параллельно, дополнительные церемонии GitFlow редко окупаются здесь.

Если проект в конечном итоге потребует обслуживания LTS, рассматривайте это как исключение: создайте ветку выпуска, перенесите критические изменения и выведите ветку из эксплуатации после окончания поддержки.

---

## 2. Локальный рабочий процесс разработки

1. Клонируйте репозиторий и установите зависимости линтинга:
    ```bash
    git clone https://github.com/nagual2/openwrt-captive-monitor.git
    cd openwrt-captive-monitor
    sudo apt-get update && sudo apt-get install -y shellcheck shfmt npm nodejs
    npm install -g markdownlint-cli
    # Для actionlint (опционально, запускается в CI)
    go install github.com/rhysd/actionlint/cmd/actionlint@latest
    ```
2. Создайте тематическую ветку, следуя правилам именования выше.
3. Внесите свои изменения и сохраняйте коммиты сфокусированными. Префиксы Conventional Commit (`feat(wifi): …`, `fix(ci): …` и т.д.) соответствуют существующей истории и питают автоматизацию changelog.
4. Перед отправкой:
    ```bash
    # Форматирование shell
    shfmt -w openwrt_captive_monitor.sh init.d/captive-monitor \
          package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor \
          package/openwrt-captive-monitor/files/etc/init.d/captive-monitor \
          package/openwrt-captive-monitor/files/etc/uci-defaults/99-captive-monitor \
          scripts/build_ipk.sh

    # Линтинг shell
    shellcheck openwrt_captive_monitor.sh init.d/captive-monitor \
               package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor \
               package/openwrt-captive-monitor/files/etc/init.d/captive-monitor \
               package/openwrt-captive-monitor/files/etc/uci-defaults/99-captive-monitor \
               scripts/build_ipk.sh

    # Линтинг Markdown
    markdownlint "**/*.md" --ignore node_modules

    # Линтинг Action (опционально)
    actionlint .github/workflows/*.yml
    ```
5. Запустите любые дополнительные дымовые тесты, которые применяются (например, запуск скрипта в режиме `oneshot`, упаковка через `scripts/build_ipk.sh` или развертывание на тестовом маршрутизаторе).
6. Сделайте rebase поверх последней `main` и разрешите конфликты локально перед открытием PR.

> Совет: используйте `git rebase --onto`, если вам нужно удалить несвязанные коммиты, которые просочились в старые ветки. Поддержание веток короткоживущими устраняет большинство болезненных rebase.

---

## 3. Ожидания от Pull Request

- Заполните шаблон PR. Он захватывает сводку, доказательства тестирования и контрольный список проверки все в одном месте.
- Ссылайтесь на соответствующий вопрос или объясните мотивацию в сводке, чтобы рецензенты имели контекст.
- Запросите как минимум одного рецензента (см. [`CODEOWNERS`](./.github/CODEOWNERS)) и дождитесь одобрения перед слиянием. Самоодобрение зарезервировано для изменений только в документации или только в CI без риска.
- Убедитесь, что задания GitHub Actions завершаются успешно:
  - `lint (shfmt)`, `lint (shellcheck)`, `lint (markdownlint)`, `lint (actionlint)`
  - `test`
  - `build (generic)` (или другие соответствующие цели матрицы, когда изменяются файлы упаковки)
- Squash-and-merge является стандартом. Если ветка содержит несколько независимо полезных коммитов, укажите это явно в PR, чтобы рецензент мог выбрать "Rebase and merge" вместо этого.

---

## 4. Защита веток и автоматизация

Ветка `main` защищена правилами защиты ветвей GitHub, чтобы обеспечить качество кода и безопасность. **Все pull request'ы должны пройти все проверки статуса перед тем, как они смогут быть объединены.**

### Требуемые проверки статуса

Перед объединением вашего pull request'а в `main` должны пройти все следующие проверки статуса:

**Линтинг и форматирование:**
- `Lint (shfmt)` - Форматирование shell скриптов
- `Lint (shellcheck)` - Линтинг shell скриптов
- `Lint (markdownlint)` - Валидация файлов Markdown
- `Lint (actionlint)` - Валидация рабочих процессов GitHub Actions

**Тестирование:**
- `Test` - Модульные и интеграционные тесты

**Сканирование безопасности:**
- `ShellCheck Security Analysis` - Анализ безопасности shell скриптов
- `Dependency Review` - Проверка уязвимостей зависимостей (только PR)
- `Trivy Security Scan` - Сканирование уязвимостей и неправильных конфигураций

### Требования к слиянию

Администраторы репозитория поддерживают следующие настройки на `main`:

- ✅ **Требуемые отзывы pull request**: Минимум 1 одобрение от владельца кода
- ✅ **Требуемые проверки статуса**: ВСЕ перечисленные выше проверки должны пройти
- ✅ **Требуется актуальность веток**: Ветка должна быть перебазирована на последнюю `main` перед слиянием
- ✅ **Линейная история**: Нет коммитов слияния; требуется squash слияние
- ✅ **Отклоняемые устаревшие отзывы**: Отзывы автоматически отклоняются при отправке новых коммитов
- ✅ **Требуемое разрешение беседы**: Все беседы рецензирования должны быть разрешены перед слиянием
- ✅ **Ограничения на отправку**: Только мейнтейнеры могут отправлять напрямую в `main`; все остальные должны использовать pull request'ы
- ✅ **Стратегия слияния**: Допускаются только squash слияния (коммиты слияния и rebase слияния отключены)
- ✅ **Очистка ветки**: Ветки автоматически удаляются после слияния
- ❌ **Блокированы force push'и**: На `main` запрещены force push'и
- ❌ **Блокировано удаление ветки**: Ветку `main` нельзя удалить

Для получения подробной информации о взаимодействии этих правил с конвейером сканирования безопасности см. [`.github/SECURITY.md`](./.github/SECURITY.md).

### Местоположение конфигурации

Эти правила защиты ветвей закодированы в [`.github/settings.yml`](./.github/settings.yml) и применяются системой защиты ветвей GitHub.

---

## 5. Тriage проблем и поддержка

- Используйте формы GitHub Issue для предоставления структурированных отчетов об ошибках, запросов функций, вопросов поддержки и проблем с документацией.
  Формы проводят вас через предоставление необходимой информации для эффективного triage.
- Для подробного руководства по шаблонам и использованию меток см. [docs/triage/TEMPLATES_AND_LABELS.md](./docs/triage/TEMPLATES_AND_LABELS.md).
- Проблемы с безопасностью должны проходить через канал частного раскрытия, указанный в нашей [Политике безопасности](.github/SECURITY.md) или советах по безопасности GitHub.
- Помечайте проблемы меткой `good-first-issue`, когда они имеют четкую область и минимальный риск, чтобы новички могли помочь.

---

## 6. Выпуски

Релизы создаются вручную мейнтейнерами с помощью workflow **Manual Release** в GitHub Actions.

### Создание релиза

1. Убедитесь, что все изменения слиты в `main` и все проверки CI прошли успешно
2. Перейдите в **Actions** → **Manual Release** в репозитории GitHub
3. Нажмите **"Run workflow"** и настройте:
   - **Custom version** (опционально): Укажите версию вроде `2025.11.27.1`, или оставьте пустым для автогенерации
   - **Release notes** (опционально): Укажите пользовательские примечания, или оставьте пустым для автогенерации
   - **Pre-release** (опционально): Отметьте, чтобы пометить как предварительный релиз
4. Нажмите **"Run workflow"** для запуска процесса релиза

### Что делает workflow

Workflow Manual Release автоматически:
- Генерирует или использует указанный тег версии (`vYYYY.M.D.N`)
- Обновляет файл `VERSION` и `PKG_VERSION` в Makefile
- Создает коммит с изменениями версии
- Создает и отправляет git тег
- Собирает универсальный пакет (`arch=all`)
- Валидирует пакет
- Создает GitHub Release с прикрепленными артефактами

### Ручной релиз (Продвинутый)

Если вам нужно создать релиз вручную без workflow:

1. Обновите `CHANGELOG.md`, `docs/releases/` и любую другую релевантную документацию
2. Соберите локальный `.ipk` для валидации:
   ```bash
   scripts/build_ipk.sh --arch all
   ```
3. Обновите метаданные версии:
   ```bash
   ./scripts/update-version-metadata.sh "2025.11.27.1"
   ```
4. Закоммитьте, создайте тег и отправьте:
   ```bash
   git add VERSION package/openwrt-captive-monitor/Makefile
   git commit -m "chore: bump version to 2025.11.27.1"
   git push origin main
   git tag -a v2025.11.27.1 -m "Release v2025.11.27.1"
   git push origin v2025.11.27.1
   ```
5. Создайте GitHub Release и загрузите артефакты вручную

### Hotfix'ы

Если регрессия требует hotfix:
1. Создайте ветку от затронутого тега
2. Примените исправление
3. Соберите и протестируйте локально
4. Используйте workflow Manual Release для создания hotfix релиза
5. Немедленно перенесите изменения обратно в `main`

### Важные замечания

- **Не создавайте теги вручную** - используйте workflow Manual Release
- **Формат версии**: `vYYYY.M.D.N` (например, `v2025.11.27.1`)
- **PKG_RELEASE**: Всегда `1` для официальных релизов
- **Автоматические релизы отключены**: Workflow auto-version отключен для предотвращения непреднамеренных релизов

---

## 7. Получение помощи

- Опции поддержки и руководства доступны в нашем [Руководстве по поддержке](.github/SUPPORT.md)
- Обсуждения: откройте GitHub Discussion или вопрос с меткой `question`.
- Тестирование в реальных условиях: поделитесь воспроизводимыми шагами и логами в PR или вопросе, чтобы мейнтейнеры могли проверить на аналогичном оборудовании.
- Обновления документации: если что-то в этом руководстве неясно, отправьте PR – метавклады приветствуются!

Еще раз благодарим за помощь в поддержании восстановления портала аутентификации на маршрутизаторах OpenWrt надежным и удобным для пользователей.
