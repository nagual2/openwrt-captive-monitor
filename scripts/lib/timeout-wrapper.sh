#!/bin/bash
# Wrapper для выполнения команд с таймаутом и отключением интерактивности

set -euo pipefail

TIMEOUT=${TIMEOUT:-30}  # По умолчанию 30 секунд

# Отключить все интерактивные элементы
export GIT_PAGER=cat
export PAGER=cat
export EDITOR=cat
export VISUAL=cat
export DEBIAN_FRONTEND=noninteractive
export TERM=dumb

# Проверка наличия команды timeout
if ! command -v timeout > /dev/null 2>&1; then
    echo "ERROR: timeout command not found" >&2
    echo "Running command without timeout..." >&2
    exec "$@"
fi

# Выполнить команду с таймаутом
# --kill-after=5s - убить процесс через 5 секунд если не завершился
timeout --kill-after=5s "$TIMEOUT" "$@"
exit_code=$?

if [ $exit_code -eq 124 ]; then
    echo "ERROR: Command timed out after $TIMEOUT seconds" >&2
    exit 124
elif [ $exit_code -eq 137 ]; then
    echo "ERROR: Command was killed (SIGKILL)" >&2
    exit 137
fi

exit $exit_code
