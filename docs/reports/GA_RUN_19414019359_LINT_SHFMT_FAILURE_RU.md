# Отчёт по сбою CI: Lint (shfmt)

Ссылка на задание: https://github.com/nagual2/openwrt-captive-monitor/actions/runs/19414019359/job/55539517588

Идентификаторы:
- Workflow run ID: 19414019359
- Job ID: 55539517588
- Job: Lint (shfmt)
- Статус: failure
- Ветка: fix-actionlint-ci-matrix-include-sc2231 (PR merge: pull/259/merge)
- Runner: GitHub Actions 1000005989 (ubuntu-24.04)
- Время: 2025-11-16T23:50:16Z → 2025-11-16T23:50:40Z (24 сек)

Краткий вывод:
- Задача «Lint (shfmt)» завершилась с ошибкой, так как форматирование ряда shell-скриптов не соответствует политике форматирования проекта.
- В работе использовался shfmt v3.8.0 (Ubuntu 24.04 / noble), командой:
  - shfmt -d -s -i 4 -ci -sr .
- shfmt обнаружил отличия и вернул ненулевой код выхода. В логе присутствуют unified diff для затронутых файлов.

Затронутые файлы (по логам shfmt):
- openwrt_captive_monitor.sh
- package/openwrt-captive-monitor/files/etc/init.d/captive-monitor
- scripts/build_ipk.sh
- scripts/check-pipe-guards.sh
- scripts/ci-helper.sh
- scripts/diagnose-actions.sh
- scripts/diagnose-github-actions.sh
- scripts/lib/colors.sh
- scripts/monitor-github-actions.sh
- scripts/parse-latest-failed-workflows.sh
- scripts/run_openwrt_vm.sh
- scripts/setup-opkg-utils.sh
- scripts/stage_artifacts.sh
- scripts/test-version-calculation.sh
- scripts/upload-sdk-to-github.sh
- scripts/validate-docs.sh
- scripts/validate-sdk-image.sh
- scripts/validate-sdk-url.sh
- scripts/validate-workflows.sh
- scripts/validate_ipk.sh
- scripts/verify_package.sh
- setup_captive_monitor.sh
- tests/mocks/_iptables_mock.sh
- tests/mocks/_lib.sh
- tests/run.sh

Суть несоответствий:
- Преимущественно отступы и выравнивание конструкций:
  - Приведение отступа к 4 пробелам (-i 4).
  - Выравнивание case/esac, if/then/fi, функциям и многострочным пайплайнам (-ci, -sr, -s).
  - Нормализация пробелов перед/после аргументов команд и переносов строк.
- Пример (фрагмент из лога для init-скрипта):
  - Было:
    -      if [ ! -x "$SCRIPT_PATH" ]; then
    -              logger -t captive-monitor -p user.err "Script not found or not executable: $SCRIPT_PATH"
    -              return 1
    -      fi
  - Стало:
    +    if [ ! -x "$SCRIPT_PATH" ]; then
    +        logger -t captive-monitor -p user.err "Script not found or not executable: $SCRIPT_PATH"
    +        return 1
    +    fi

Первопричина:
- В репозиторий попали изменения shell-скриптов, не отформатированные shfmt в конфигурации проекта (.shfmt.conf и/или параметры в CI). Это системный несоответствующий стиль (не баг выполнения), который принудительно контролируется в CI.

Воспроизведение локально:
1) На Ubuntu 24.04:
   - sudo apt-get update && sudo apt-get install -y shfmt
   - Проверка: shfmt --version  # ожидается 3.8.0
2) Запустить проверку в корне репозитория:
   - shfmt -d -s -i 4 -ci -sr .
3) Автоисправление формата:
   - shfmt -w -s -i 4 -ci -sr .

Рекомендации по исправлению:
- Выполнить автоматическую переформатировку всех shell-скриптов указанной командой (shfmt -w -s -i 4 -ci -sr .).
- Перепроверить bash/ash-совместимость после форматирования, особенно:
  - set -eu и условный pipefail (через set -o pipefail если доступно).
  - Отсутствие bash-специфичных расширений в скриптах, исполняемых BusyBox ash.
  - Сохранение зависимостей на общий файл цветов scripts/lib/colors.sh (если используется).
- Добавить локальный pre-commit-хук (опционально), который вызывает shfmt перед коммитом:
  - scripts/ci-helper.sh или отдельный .githooks/pre-commit с вызовом shfmt в режиме -w.
- После фикса: запустить все lint-задачи локально либо в PR, чтобы убедиться в чистоте CI.

Наблюдения по среде выполнения:
- Runner: ubuntu-24.04 (noble), apt устанавливает shfmt 3.8.0.
- Пакеты для шага линтинга устанавливаются композитным экшеном ./.github/actions/setup-system-packages (busybox, shfmt, shellcheck).

Итог:
- Сбой не связан с логикой проекта или сборкой пакетов; это несоблюдение стиля shell-скриптов. Проектный стиль задаётся shfmt и проверяется в CI. Необходимо привести к нему все изменённые скрипты.

Приложение: фрагменты лога
- Команда линтера: `shfmt -d -s -i 4 -ci -sr .`
- Обнаружены отличия в 25 файлах (см. список выше).
