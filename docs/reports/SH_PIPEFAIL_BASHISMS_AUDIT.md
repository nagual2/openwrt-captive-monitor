# Аудит pipefail/башизмов в sh-скриптах (OpenWrt)

Цель: выявить все места в репозитории, где используется `pipefail` или другие башизмы, важные для POSIX `sh` (BusyBox `ash` на OpenWrt), и дать рекомендации. Изменений кода не производилось.

Диалект целевой платформы: OpenWrt, по умолчанию BusyBox ash. Скрипты пакета должны быть совместимы с `/bin/sh` (ash), bash отсутствует из коробки.

Охват отчёта:
- Искали: `pipefail`, `set -o pipefail`, `set -euo pipefail` (и вариации с `pipefail`), шебанги с bash, а также shellcheck-директивы для башизмов: SC3040 (pipefail), SC2039/SC3043 (local), и отключения SC3040.
- Рассматривали только реальные скрипты репозитория (исключая документацию). Включены: скрипты пакета (`package/.../files/**`), их зеркала в `usr/` и `etc/`, обёртки запуска (`openwrt_captive_monitor.sh`, `init.d/captive-monitor`), а также вспомогательные скрипты в `scripts/`.

## Сводка

- Найдены использования `set -o pipefail` в POSIX-скриптах (ash), везде защищены проверкой доступности и сопровождаются `# shellcheck disable=SC3040`.
- Найдены bash-скрипты разработчика с `set -euo pipefail` и шебангами `#!/bin/bash` или `#!/usr/bin/env bash` — они не предназначены для исполнения на OpenWrt.
- Найдены shellcheck-директивы, указывающие на башизмы, используемые сознательно в ash: `SC3043/SC2039` (использование `local`).

## Совпадения по файлам (номер строки → фрагмент)

Примечания к колонкам:
- Shebang — текущий интерпретатор файла.
- ShellCheck — указанный диалект или отключения.

### 1) Пакет и исполняемые скрипты OpenWrt

- package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor
  - Shebang: [1] `#!/bin/sh`
  - ShellCheck: [2] `# shellcheck shell=ash`
  - ShellCheck: [3] `# shellcheck disable=SC3043` (использование `local` в ash)
  - ShellCheck: [4] `# shellcheck disable=SC2039` (в POSIX sh `local` не определён)
  - ShellCheck: [6] `# shellcheck disable=SC2039`
  - pipefail: [9] `if (set -o pipefail) 2> /dev/null; then`
  - SC3040 disable: [10] `# shellcheck disable=SC3040`
  - pipefail: [11] `set -o pipefail`

- usr/sbin/openwrt_captive_monitor (зеркало скрипта для удобного запуска)
  - Shebang: [1] `#!/bin/sh`
  - ShellCheck: [2] `# shellcheck shell=ash`
  - ShellCheck: [3] `# shellcheck disable=SC3043`
  - ShellCheck: [4] `# shellcheck disable=SC2039`
  - ShellCheck: [6] `# shellcheck disable=SC2039`
  - pipefail: [9] `if (set -o pipefail) 2> /dev/null; then`
  - SC3040 disable: [10] `# shellcheck disable=SC3040`
  - pipefail: [11] `set -o pipefail`

- package/openwrt-captive-monitor/files/etc/init.d/captive-monitor
  - Shebang: [1] `#!/bin/sh`
  - ShellCheck: [3] `# shellcheck shell=ash`
  - (pipefail не используется — совместим с ash)

- etc/init.d/captive-monitor (зеркало init-скрипта)
  - Shebang: [1] `#!/bin/sh`
  - ShellCheck: [3] `# shellcheck shell=ash`
  - (pipefail не используется)

- package/openwrt-captive-monitor/files/etc/uci-defaults/99-captive-monitor
  - Shebang: [1] `#!/bin/sh`
  - ShellCheck: [2] `# shellcheck shell=ash`
  - (pipefail не используется)

- etc/uci-defaults/99-captive-monitor (зеркало)
  - Shebang: [1] `#!/bin/sh`
  - ShellCheck: [2] `# shellcheck shell=ash`
  - (pipefail не используется)

- openwrt_captive_monitor.sh (обёртка поиска исполняемого файла)
  - Shebang: [1] `#!/bin/sh`
  - ShellCheck: [2] `# shellcheck shell=ash`
  - pipefail: [5] `if (set -o pipefail) 2> /dev/null; then`
  - SC3040 disable: [6] `# shellcheck disable=SC3040`
  - pipefail: [7] `set -o pipefail`

- init.d/captive-monitor (локальная обёртка на развитие)
  - Shebang: [1] `#!/bin/sh`
  - ShellCheck: [2] `# shellcheck shell=ash`
  - pipefail: [5] `if (set -o pipefail) 2> /dev/null; then`
  - SC3040 disable: [6] `# shellcheck disable=SC3040`
  - pipefail: [7] `set -o pipefail`

### 2) Вспомогательные скрипты (для разработки/CI, не для OpenWrt)

- scripts/build_ipk.sh
  - Shebang: [1] `#!/bin/sh`
  - ShellCheck: [3] `# shellcheck shell=ash`
  - ShellCheck: [4] `# shellcheck disable=SC3043`
  - pipefail: [7] `if (set -o pipefail) 2> /dev/null; then`
  - SC3040 disable: [8] `# shellcheck disable=SC3040`
  - pipefail: [9] `set -o pipefail`

- scripts/run_openwrt_vm.sh
  - Shebang: [1] `#!/bin/sh`
  - ShellCheck: [3] `# shellcheck shell=ash`
  - ShellCheck: [4] `# shellcheck disable=SC3043`
  - pipefail: [8] `if (set -o pipefail) 2> /dev/null; then`
  - SC3040 disable: [9] `# shellcheck disable=SC3040`
  - pipefail: [10] `set -o pipefail`

- scripts/stage_artifacts.sh
  - Shebang: [1] `#!/bin/sh`
  - pipefail: [26] `if (set -o pipefail) 2> /dev/null; then`
  - SC3040 disable: [27] `# shellcheck disable=SC3040`
  - pipefail: [28] `set -o pipefail`

- scripts/validate_ipk.sh
  - Shebang: [1] `#!/bin/sh`
  - ShellCheck: [3] `# shellcheck shell=ash`
  - ShellCheck: [4] `# shellcheck disable=SC3043`
  - pipefail: [7] `if (set -o pipefail) 2> /dev/null; then`
  - SC3040 disable: [8] `# shellcheck disable=SC3040`
  - pipefail: [9] `set -o pipefail`

- scripts/diagnose-github-actions.sh
  - Shebang: [1] `#!/bin/bash` (bash)
  - pipefail: [2] `set -euo pipefail`

- scripts/diagnose-actions.sh
  - Shebang: [1] `#!/bin/bash` (bash)
  - pipefail: [2] `set -euo pipefail`

- scripts/parse-latest-failed-workflows.sh
  - Shebang: [1] `#!/bin/bash` (bash)
  - pipefail: [2] `set -euo pipefail`

- scripts/test-version-calculation.sh
  - Shebang: [1] `#!/bin/bash` (bash)
  - pipefail: [5] `set -euo pipefail`

- scripts/verify_package.sh
  - Shebang: [1] `#!/usr/bin/env bash` (bash)
  - pipefail: [3] `set -euo pipefail`

- scripts/upload-sdk-to-github.sh
  - Shebang: [1] `#!/bin/bash` (bash)
  - (pipefail не используется: [2] `set -e`)

## Проверка контекста POSIX (sh/ash/bash)

- Скрипты пакета и исполняемые файлы на целевой системе (OpenWrt): шебанг `#!/bin/sh` присутствует корректно; большинство помечены `# shellcheck shell=ash`, что соответствует BusyBox ash на OpenWrt.
- Вспомогательные скрипты разработчика используют `bash` через `#!/bin/bash` или `#!/usr/bin/env bash` и не предназначены для окружения OpenWrt.
- Случаев шебанга на `dash` или `ash` нет — используется `#!/bin/sh` (ash через `sh`).

## Краткие рекомендации

По типам находок:

- Использование `set -o pipefail` в `sh`-скриптах:
  - Несовместимо с чистым POSIX `sh`. В BusyBox `ash` (OpenWrt) отсутствует.
  - Текущая практика в репозитории корректная: включение под условием и подавление SC3040:
    - `if (set -o pipefail) 2>/dev/null; then set -o pipefail; fi` + `# shellcheck disable=SC3040`.
  - Альтернативы: не использовать `pipefail` и при необходимости разбивать конвейеры на шаги с явной проверкой статусов; либо включать `pipefail` с `2>/dev/null || true` (но это тоже триггерит SC3040 без disable-комментария).

- Шебанг на bash (`#!/bin/bash` или `#!/usr/bin/env bash`):
  - Для OpenWrt (целевой системы) bash отсутствует по умолчанию, поэтому такие скрипты нельзя устанавливать/исполнять на устройстве.
  - Убедиться, что данные скрипты используются только в окружении разработчика/CI. Если понадобится перенос на устройство — переписать под `sh`/`ash` или добавить явную зависимость от bash (не рекомендуется для OpenWrt).

- Использование `local` в `sh`-скриптах и связанные отключения SC3043/SC2039:
  - В POSIX `sh` `local` не определён, но BusyBox `ash` поддерживает `local` — это распространённая практика на OpenWrt.
  - Существующие директивы `# shellcheck disable=SC3043` и `# shellcheck disable=SC2039` уместны при таргете на `ash`. При необходимости строгой POSIX-совместимости — заменить на POSIX-эквиваленты без `local`.

## Примечания

- Отчёт подготовлен без изменений кодовой базы. Все номера строк и фрагменты приведены по состоянию на текущую ветку `audit-sh-pipefail-bashisms`.
- При дальнейшем рефакторинге следует поддерживать статус-кво: скрипты для целевой прошивки — `#!/bin/sh` (ash), dev-скрипты могут требовать bash, но не должны попадать в состав пакета OpenWrt.
