#!/bin/sh

# Source shared color definitions so output formatting stays consistent
# shellcheck source=scripts/lib/colors.sh
. "$(dirname "$0")/scripts/lib/colors.sh"

# Default configuration
WIFI_INTERFACE="phy1-sta0"
WIFI_LOGICAL="wwan"
MONITOR_INTERVAL=60
PING_SERVERS="1.1.1.1 8.8.8.8 9.9.9.9"
CHECK_URLS="http://connectivitycheck.gstatic.com/generate_204 http://detectportal.firefox.com/success.txt"

# Language handling
LANGUAGE="en" # Default language

# Parse command line arguments
for arg in "$@"; do
    case $arg in
        --lang=*)
            LANGUAGE="${arg#*=}"
            shift
            ;;
    esac
done

# Function to get localized message
get_msg() {
    local key="$1"
    local lang="${2:-$LANGUAGE}"

    # Default to English if language not specified
    [ -z "$lang" ] && lang="en"

    # Convert to lowercase
    lang=$(echo "$lang" | tr '[:upper:]' '[:lower:]')

    # English messages
    if [ "$lang" = "en" ]; then
        case "$key" in
            installing) echo "Installing OpenWRT Captive Monitor..." ;;
            installing_deps) echo "Installing required dependencies..." ;;
            creating_dirs) echo "Creating necessary directories..." ;;
            copying_files) echo "Copying package files..." ;;
            setting_perms) echo "Setting file permissions..." ;;
            install_success) echo "Package installed successfully" ;;
            configuring) echo "Configuring OpenWRT Captive Monitor..." ;;
            starting_service) echo "Enabling and starting the service..." ;;
            service_failed) echo "Warning: Failed to start captive-monitor service" ;;
            config_complete) echo "Configuration completed" ;;
            uninstalling) echo "Uninstalling OpenWRT Captive Monitor..." ;;
            removing_files) echo "Removing package files..." ;;
            removing_deps) echo "Removing dependencies..." ;;
            uninstall_success) echo "Package uninstalled successfully" ;;
            service_status) echo "=== Service Status ===" ;;
            configuration) echo "=== Configuration ===" ;;
            process_status) echo "=== Process Status ===" ;;
            running) echo "Captive monitor is running" ;;
            not_running) echo "Captive monitor is not running" ;;
            no_config) echo "No configuration found" ;;
            *) echo "$key" ;;
        esac
    # Russian messages
    elif [ "$lang" = "ru" ]; then
        case "$key" in
            installing) echo "Установка OpenWRT Captive Monitor..." ;;
            installing_deps) echo "Установка необходимых зависимостей..." ;;
            creating_dirs) echo "Создание необходимых директорий..." ;;
            copying_files) echo "Копирование файлов пакета..." ;;
            setting_perms) echo "Установка прав доступа..." ;;
            install_success) echo "Пакет успешно установлен" ;;
            configuring) echo "Настройка OpenWRT Captive Monitor..." ;;
            starting_service) echo "Включение и запуск службы..." ;;
            service_failed) echo "Внимание: Не удалось запустить службу captive-monitor" ;;
            config_complete) echo "Настройка завершена" ;;
            uninstalling) echo "Удаление OpenWRT Captive Monitor..." ;;
            removing_files) echo "Удаление файлов пакета..." ;;
            removing_deps) echo "Удаление зависимостей..." ;;
            uninstall_success) echo "Пакет успешно удален" ;;
            service_status) echo "=== Статус службы ===" ;;
            configuration) echo "=== Конфигурация ===" ;;
            process_status) echo "=== Статус процесса ===" ;;
            running) echo "Монитор активен" ;;
            not_running) echo "Монитор не запущен" ;;
            no_config) echo "Конфигурация не найдена" ;;
            *) echo "$key" ;;
        esac
    else
        # Default to English if language not supported
        get_msg "$key" "en"
    fi
}

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    printf "%sError: This script must be run as root%s\n" "$RED" "$NC" >&2
    exit 1
fi

# Function to install the package
install_package() {
    printf "%s%s%s\n" "$GREEN" "$(get_msg installing)" "$NC"

    printf "%s%s%s\n" "$GREEN" "$(get_msg installing_deps)" "$NC"
    if ! opkg update; then
        printf "%sError: Failed to update package lists%s\n" "$RED" "$NC" >&2
        return 1
    fi

    if ! opkg install dnsmasq curl ca-bundle; then
        printf "%sWarning: Some dependencies failed to install. Continuing anyway...%s\n" "$YELLOW" "$NC" >&2
    fi

    printf "%s%s%s\n" "$GREEN" "$(get_msg creating_dirs)" "$NC"
    mkdir -p /usr/sbin/ /etc/init.d/ /etc/config/ /etc/uci-defaults/ /usr/share/licenses/openwrt-captive-monitor/ || {
        printf "%sError: Failed to create directories%s\n" "$RED" "$NC" >&2
        return 1
    }

    printf "%s%s%s\n" "$GREEN" "$(get_msg copying_files)" "$NC"
    if [ ! -d "/tmp/openwrt-captive-monitor/package" ]; then
        printf "%sError: Package files not found in /tmp/openwrt-captive-monitor/%s\n" "$RED" "$NC" >&2
        return 1
    fi

    cp /tmp/openwrt-captive-monitor/package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor /usr/sbin/ || {
        printf "%sError: Failed to copy openwrt_captive_monitor%s\n" "$RED" "$NC" >&2
        return 1
    }

    cp /tmp/openwrt-captive-monitor/package/openwrt-captive-monitor/files/etc/init.d/captive-monitor /etc/init.d/ || {
        printf "%sError: Failed to copy init script%s\n" "$RED" "$NC" >&2
        return 1
    }

    if [ -f "/tmp/openwrt-captive-monitor/package/openwrt-captive-monitor/files/etc/config/captive-monitor" ]; then
        cp /tmp/openwrt-captive-monitor/package/openwrt-captive-monitor/files/etc/config/captive-monitor /etc/config/ || {
            printf "%sWarning: Failed to copy config file, using defaults%s\n" "$YELLOW" "$NC" >&2
        }
    else
        printf "%sWarning: No config file found, using defaults%s\n" "$YELLOW" "$NC" >&2
    fi

    printf "%s%s%s\n" "$GREEN" "$(get_msg setting_perms)" "$NC"
    sed -i 's/\r$//' /usr/sbin/openwrt_captive_monitor 2> /dev/null
    sed -i 's/\r$//' /etc/init.d/captive-monitor 2> /dev/null
    chmod +x /usr/sbin/openwrt_captive_monitor || {
        printf "%sError: Failed to set executable permissions%s\n" "$RED" "$NC" >&2
        return 1
    }
    chmod +x /etc/init.d/captive-monitor || {
        printf "%sError: Failed to set executable permissions%s\n" "$RED" "$NC" >&2
        return 1
    }

    # Initialize UCI config if it doesn't exist
    if ! uci -q get captive-monitor.@captive_monitor[0] > /dev/null; then
        uci add captive-monitor captive_monitor
    fi

    # Set language in config
    uci set captive-monitor.@captive_monitor[0].language="$LANGUAGE"
    uci commit captive-monitor || {
        printf "%sWarning: Failed to save configuration%s\n" "$YELLOW" "$NC" >&2
    }

    printf "%s%s%s\n" "$GREEN" "$(get_msg install_success)" "$NC"
    return 0
}

# Function to configure the package
configure_package() {
    # Get language from config or use default
    local config_lang
    config_lang=$(uci -q get captive-monitor.@captive_monitor[0].language || echo "$LANGUAGE")
    if [ -n "$config_lang" ]; then
        LANGUAGE="$config_lang"
    fi

    printf "%s%s%s\n" "$GREEN" "$(get_msg configuring)" "$NC"

    # Initialize UCI config if it doesn't exist
    if ! uci -q get captive-monitor.@captive_monitor[0] > /dev/null; then
        uci add captive-monitor captive_monitor
    fi

    # Set configuration values
    uci set captive-monitor.@captive_monitor[0].enabled='1'
    uci set captive-monitor.@captive_monitor[0].wifi_interface="$WIFI_INTERFACE"
    uci set captive-monitor.@captive_monitor[0].wifi_logical="$WIFI_LOGICAL"
    uci set captive-monitor.@captive_monitor[0].monitor_interval="$MONITOR_INTERVAL"
    uci set captive-monitor.@captive_monitor[0].ping_servers="$PING_SERVERS"
    uci set captive-monitor.@captive_monitor[0].captive_check_urls="$CHECK_URLS"
    uci set captive-monitor.@captive_monitor[0].language="$LANGUAGE"

    if ! uci commit captive-monitor; then
        printf "%sWarning: Failed to save configuration%s\n" "$YELLOW" "$NC" >&2
    fi

    printf "%s%s%s\n" "$GREEN" "$(get_msg starting_service)" "$NC"
    /etc/init.d/captive-monitor enable || {
        printf "%sWarning: Failed to enable service%s\n" "$YELLOW" "$NC" >&2
    }

    if ! /etc/init.d/captive-monitor start; then
        printf "%s%s%s\n" "$RED" "$(get_msg service_failed)" "$NC" >&2
        return 1
    fi

    if ! /etc/init.d/captive-monitor status > /dev/null 2>&1; then
        printf "%s%s%s\n" "$RED" "$(get_msg service_failed)" "$NC" >&2
        return 1
    fi

    printf "%s%s%s\n" "$GREEN" "$(get_msg config_complete)" "$NC"
    return 0
}

# Function to uninstall the package
uninstall_package() {
    # Get language from config or use default
    local config_lang
    config_lang=$(uci -q get captive-monitor.@captive_monitor[0].language || echo "$LANGUAGE")
    if [ -n "$config_lang" ]; then
        LANGUAGE="$config_lang"
    fi

    printf "%s%s%s\n" "$RED" "$(get_msg uninstalling)" "$NC"

    # Stop and disable the service if it exists
    if [ -f "/etc/init.d/captive-monitor" ]; then
        /etc/init.d/captive-monitor stop 2> /dev/null || true
        /etc/init.d/captive-monitor disable 2> /dev/null || true
    fi

    printf "%s%s%s\n" "$GREEN" "$(get_msg removing_files)" "$NC"
    rm -f /usr/sbin/openwrt_captive_monitor
    rm -f /etc/init.d/captive-monitor
    rm -f /etc/config/captive-monitor

    # Optionally remove dependencies (commented out by default)
    # printf "%s%s%s\n" "$GREEN" "$(get_msg removing_deps)" "$NC"
    # opkg remove dnsmasq curl ca-bundle

    printf "%s%s%s\n" "$GREEN" "$(get_msg uninstall_success)" "$NC"
    return 0
}

# Function to show service status
show_status() {
    # Get language from config or use default
    local config_lang
    config_lang=$(uci -q get captive-monitor.@captive_monitor[0].language || echo "$LANGUAGE")
    if [ -n "$config_lang" ]; then
        LANGUAGE="$config_lang"
    fi

    printf "\n%s%s%s\n" "$GREEN" "$(get_msg service_status)" "$NC"
    if [ -f "/etc/init.d/captive-monitor" ]; then
        /etc/init.d/captive-monitor status 2> /dev/null || printf "%s%s%s\n" "$YELLOW" "$(get_msg not_running)" "$NC"
    else
        printf "%sService not installed%s\n" "$YELLOW" "$NC"
    fi

    printf "\n%s%s%s\n" "$GREEN" "$(get_msg configuration)" "$NC"
    if uci -q get captive-monitor.@captive_monitor[0] > /dev/null; then
        uci show captive-monitor 2> /dev/null || printf "%s%s%s\n" "$YELLOW" "$(get_msg no_config)" "$NC"
    else
        printf "%s%s%s\n" "$YELLOW" "$(get_msg no_config)" "$NC"
    fi

    printf "\n%s%s%s\n" "$GREEN" "$(get_msg process_status)" "$NC"
    if pgrep -f "openwrt_captive_monitor" > /dev/null; then
        printf "%s%s%s\n" "$GREEN" "$(get_msg running)" "$NC"
        return 0
    else
        printf "%s%s%s\n" "$YELLOW" "$(get_msg not_running)" "$NC"
        return 1
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [command] [options]"
    echo "Commands:"
    echo "  install     - Install and configure the package"
    echo "  uninstall   - Uninstall the package"
    echo "  status      - Show service status"
    echo "  help        - Show this help message"
    echo ""
    echo "Options:"
    echo "  --lang=code  Set the language (en/ru)"
    echo ""
    echo "Examples:"
    echo "  $0 install --lang=ru"
    echo "  $0 status"
    echo "  $0 uninstall"
}

# Main script
COMMAND=""

# Parse command line arguments
while [ $# -gt 0 ]; do
    case "$1" in
        --lang=*)
            LANGUAGE="${1#*=}"
            shift
            ;;
        install | uninstall | status | help | --help | -h)
            COMMAND="$1"
            shift
            ;;
        *)
            printf "%sError: Unknown option: %s%s\n" "$RED" "$1" "$NC" >&2
            show_usage
            exit 1
            ;;
    esac
done

# Default to help if no command provided
if [ -z "$COMMAND" ]; then
    show_usage
    exit 0
fi

# Execute the requested command
case "$COMMAND" in
    install)
        install_package && configure_package
        ;;
    uninstall)
        uninstall_package
        ;;
    status)
        show_status
        ;;
    help | --help | -h)
        show_usage
        ;;
    *)
        printf "%sError: Unknown command: %s%s\n" "$RED" "$COMMAND" "$NC" >&2
        show_usage
        exit 1
        ;;
esac

exit $?
