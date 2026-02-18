#!/bin/bash
# Wrapper script for captive portal monitor
# Prevents multiple instances when running via cron

set -euo pipefail

LOCK_FILE="/var/lock/captive-portal-monitor.lock"
LOCK_FD=200

# Try to acquire lock
exec 200>"$LOCK_FILE"
if ! flock -n 200; then
    # Another instance is running
    exit 0
fi

# Run the main script
exec /usr/bin/captive-portal-monitor "$@"
