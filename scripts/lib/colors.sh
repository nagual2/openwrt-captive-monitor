#!/bin/sh
# shellcheck shell=ash
# POSIX-compliant color handling library
#
# This library provides consistent ANSI color code handling across all shell scripts.
# It automatically detects TTY output and respects the NO_COLOR environment variable.
#
# Usage:
#   # Source this file at the beginning of your script
#   . "$(dirname "$0")/lib/colors.sh"
#   # or with absolute path
#   . /path/to/scripts/lib/colors.sh
#
#   # Then use the color variables
#   printf "%sSuccess%s\n" "$GREEN" "$NC"
#   printf "%sError%s\n" "$RED" "$NC"
#
# Available color variables:
#   RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN - Standard colors
#   NC - No Color (reset)
#
# Environment variables:
#   NO_COLOR - Set to any value to disable colors
#
# The library automatically disables colors if:
#   - NO_COLOR environment variable is set
#   - Output is not a TTY (e.g., piped or redirected)

# ANSI color codes (POSIX-safe octal escape sequences)
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
MAGENTA='\033[35m'
CYAN='\033[36m'
NC='\033[0m' # No Color

# Disable colors if NO_COLOR is set or stdout is not a TTY
if [ -n "${NO_COLOR:-}" ] || [ ! -t 1 ]; then
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    MAGENTA=''
    CYAN=''
    NC=''
fi
