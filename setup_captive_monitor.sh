#!/bin/sh

# Default configuration
WIFI_INTERFACE="phy1-sta0"
WIFI_LOGICAL="wwan"
MONITOR_INTERVAL=60
PING_SERVERS="1.1.1.1 8.8.8.8 9.9.9.9"
CHECK_URLS="http://connectivitycheck.gstatic.com/generate_204 http://detectportal.firefox.com/success.txt"
LANGUAGE="en" # Default language

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
    echo "Error: This script must be run as root" >&2
    exit 1
fi

# Function to install the package
install_package() {
    echo "$(get_msg installing)"

    echo "$(get_msg installing_deps)"
    opkg update || {
        echo "Error: Failed to update package lists" >&2
        return 1
    }
    opkg install dnsmasq curl ca-bundle || {
        echo "Error: Failed to install dependencies" >&2
        return 1
    }

    echo "$(get_msg creating_dirs)"
    mkdir -p /usr/sbin/ /etc/init.d/ /etc/config/ /etc/uci-defaults/ /usr/share/licenses/openwrt-captive-monitor/ ||
        {
            echo "Error: Failed to create directories" >&2
            return 1
        }

    echo "$(get_msg copying_files)"
    cp /tmp/openwrt-captive-monitor/package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor /usr/sbin/ ||
        {
            echo "Error: Failed to copy openwrt_captive_monitor" >&2
            return 1
        }
    cp /tmp/openwrt-captive-monitor/package/openwrt-captive-monitor/files/etc/init.d/captive-monitor /etc/init.d/ ||
        {
            echo "Error: Failed to copy init script" >&2
            return 1
        }
    cp /tmp/openwrt-captive-monitor/package/openwrt-captive-monitor/files/etc/config/captive-monitor /etc/config/ ||
        echo "Warning: No config file found, using defaults" >&2

    echo "$(get_msg setting_perms)"
    sed -i 's/\r$//' /usr/sbin/openwrt_captive_monitor
    sed -i 's/\r$//' /etc/init.d/captive-monitor
    chmod +x /usr/sbin/openwrt_captive_monitor || {
        echo "Error: Failed to set executable permissions" >&2
        return 1
    }
    chmod +x /etc/init.d/captive-monitor || {
        echo "Error: Failed to set executable permissions" >&2
        return 1
    }

    # Initialize UCI config if it doesn't exist
    if ! uci -q get captive-monitor.@captive_monitor[0] > /dev/null; then
        uci add captive-monitor captive_monitor
    fi

    # Set language in config
    uci set captive-monitor.@captive_monitor[0].language="$LANGUAGE"
    uci commit captive-monitor || echo "Warning: Failed to save configuration" >&2

    echo "$(get_msg install_success)"
    return 0
}

# Function to configure the package
configure_package() {
    # Get language from config or use default
    CONFIG_LANG=$(uci -q get captive-monitor.@captive_monitor[0].language || echo "$LANGUAGE")
    if [ -n "$CONFIG_LANG" ]; then
        LANGUAGE="$CONFIG_LANG"
    fi

    echo "$(get_msg configuring)"

    # Initialize UCI config if it doesn't exist
    if ! uci -q get captive-monitor.@captive_monitor[0] > /dev/null; then
        uci add captive-monitor captive_monitor
    fi

    # Enable the service
    uci set captive-monitor.@captive_monitor[0].enabled='1'
    uci set captive-monitor.@captive_monitor[0].wifi_interface="$WIFI_INTERFACE"
    uci set captive-monitor.@captive_monitor[0].wifi_logical="$WIFI_LOGICAL"
    uci set captive-monitor.@captive_monitor[0].monitor_interval="$MONITOR_INTERVAL"
    uci set captive-monitor.@captive_monitor[0].ping_servers="$PING_SERVERS"
    uci set captive-monitor.@captive_monitor[0].captive_check_urls="$CHECK_URLS"
    uci set captive-monitor.@captive_monitor[0].language="$LANGUAGE"
    uci commit captive-monitor || { echo "Warning: Failed to save configuration" >&2; }

    echo "$(get_msg starting_service)"
    /etc/init.d/captive-monitor enable || { echo "Warning: Failed to enable service" >&2; }
    /etc/init.d/captive-monitor start || {
        echo "$(get_msg service_failed)" >&2
        return 1
    }

    if ! /etc/init.d/captive-monitor status > /dev/null 2>&1; then
        echo "$(get_msg service_failed)" >&2
        return 1
    fi

    echo "$(get_msg config_complete)"
    return 0
}

# Function to uninstall the package
uninstall_package() {
    # Get language from config or use default
    CONFIG_LANG=$(uci -q get captive-monitor.@captive_monitor[0].language || echo "$LANGUAGE")
    if [ -n "$CONFIG_LANG" ]; then
        LANGUAGE="$CONFIG_LANG"
    fi

    echo "$(get_msg uninstalling)"

    # Stop and disable the service if it exists
    if [ -f /etc/init.d/captive-monitor ]; then
        /etc/init.d/captive-monitor stop 2> /dev/null || true
        /etc/init.d/captive-monitor disable 2> /dev/null || true
    fi

    echo "$(get_msg removing_files)"
    rm -f /usr/sbin/openwrt_captive_monitor
    rm -f /etc/init.d/captive-monitor

    # Don't remove config file to preserve settings
    # rm -f /etc/config/captive-monitor

    # Optionally remove dependencies (commented out by default)
    # echo "$(get_msg removing_deps)"
    # opkg remove dnsmasq curl ca-bundle

    echo "$(get_msg uninstall_success)"
    return 0
}

# Function to show service status
show_status() {
    # Get language from config or use default
    CONFIG_LANG=$(uci -q get captive-monitor.@captive_monitor[0].language 2> /dev/null || echo "$LANGUAGE")
    if [ -n "$CONFIG_LANG" ]; then
        LANGUAGE="$CONFIG_LANG"
    fi

    echo "$(get_msg service_status)"
    if [ -f /etc/init.d/captive-monitor ]; then
        /etc/init.d/captive-monitor status 2> /dev/null || echo "$(get_msg not_running)"
    else
        echo "Service not installed"
    fi

    echo ""
    echo "$(get_msg configuration)"
    if [ -f /etc/config/captive-monitor ]; then
        uci show captive-monitor 2> /dev/null || echo "$(get_msg no_config)"
    else
        echo "No configuration file found"
    fi

    echo ""
    echo "$(get_msg process_status)"
    if pgrep -f "openwrt_captive_monitor" > /dev/null; then
        echo "$(get_msg running)"
    else
        echo "$(get_msg not_running)"
    fi
    return 0
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [options] [command]"
    echo "Commands:"
    echo "  install     - Install and configure the package"
    echo "  uninstall   - Uninstall the package"
    echo "  status      - Show service status"
    echo "  help        - Show this help message"
    echo ""
    echo "Options:"
    echo "  --lang=XX   - Set language (en/ru), default: en"
    return 0
}

# Parse command line arguments
COMMAND=""
LANGUAGE="en"

# First parse language if specified
for arg in "$@"; do
    if [ "${arg#--lang=}" != "$arg" ]; then
        LANGUAGE="${arg#--lang=}"
        break
    fi
done

# Then parse command
for arg in "$@"; do
    case "$arg" in
        install | uninstall | status | help | --help | -h)
            COMMAND="$arg"
            break
            ;;
    esac
done

# If no command specified, show usage
[ -z "$COMMAND" ] && COMMAND="help"

# Main script execution
case "$COMMAND" in
    install)
        install_package
        configure_package
        ;;
    uninstall)
        uninstall_package
        ;;
    status)
        show_status
        ;;
    help | --help | -h | *)
        show_usage
        ;;
esac

exit $?
