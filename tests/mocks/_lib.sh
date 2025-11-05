#!/bin/sh

MOCK_ROOT=$(cd "$(dirname "$0")" 2> /dev/null && pwd)
LOG_FILE=${TEST_LOG:-}
STATE_ROOT=${TEST_STATE_DIR:-}

mock_init() {
  if [ -n "$STATE_ROOT" ]; then
    mkdir -p "$STATE_ROOT" 2> /dev/null || true
  fi
}

mock_log() {
  mock_init
  if [ -n "$LOG_FILE" ]; then
    cmd="$1"
    shift || true
    printf '%s' "$cmd" >> "$LOG_FILE"
    while [ "$#" -gt 0 ]; do
      printf ' %s' "$1" >> "$LOG_FILE"
      shift
    done
    printf '\n' >> "$LOG_FILE"
  fi
}

mock_state_file() {
  mock_init
  name="$1"
  if [ -n "$STATE_ROOT" ]; then
    printf '%s/%s.state' "$STATE_ROOT" "$name"
  else
    printf '%s/%s.state' "$MOCK_ROOT" "$name"
  fi
}
