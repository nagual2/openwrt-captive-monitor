#!/bin/sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd 2>/dev/null)"
LOCAL_SCRIPT="$SCRIPT_DIR/package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor"

if [ -n "$SCRIPT_DIR" ] && [ -x "$LOCAL_SCRIPT" ]; then
    exec "$LOCAL_SCRIPT" "$@"
fi

if command -v openwrt_captive_monitor >/dev/null 2>&1; then
    exec "$(command -v openwrt_captive_monitor)" "$@"
fi

if [ -x /usr/sbin/openwrt_captive_monitor ]; then
    exec /usr/sbin/openwrt_captive_monitor "$@"
fi

echo "openwrt_captive_monitor executable not found" >&2
exit 127
