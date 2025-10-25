#!/bin/sh
# shellcheck shell=ash
# shellcheck disable=SC2039
# shellcheck disable=SC2086
# shellcheck disable=SC2046
# shellcheck disable=SC2120
set -eu

if (set -o pipefail) 2> /dev/null; then
    # shellcheck disable=SC3040
    set -o pipefail
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" 2> /dev/null && pwd 2> /dev/null || printf '')"
LOCAL_SCRIPT="$SCRIPT_DIR/package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor"

if [ -n "$SCRIPT_DIR" ] && [ -x "$LOCAL_SCRIPT" ]; then
    exec "$LOCAL_SCRIPT" "$@"
fi

SYSTEM_SCRIPT="$(command -v openwrt_captive_monitor 2> /dev/null || printf '')"
if [ -n "$SYSTEM_SCRIPT" ]; then
    exec "$SYSTEM_SCRIPT" "$@"
fi

if [ -x /usr/sbin/openwrt_captive_monitor ]; then
    exec /usr/sbin/openwrt_captive_monitor "$@"
fi

echo "openwrt_captive_monitor executable not found" >&2
exit 127
