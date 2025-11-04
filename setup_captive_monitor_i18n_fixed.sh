#!/bin/sh

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
YELLOW='\033[1;33m'

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

    # English messages
    if [ "$LANGUAGE" = "en" ]; then
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
    elif [ "$LANGUAGE" = "ru" ]; then
        case $key in
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
        LANGUAGE="en"
        get_msg "$key"
    fi
}

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root${NC}"
    exit 1
fi

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
            shift
            ;;
    esac
done

# Function to install the package
install_package() {
    echo -e "${GREEN}$(get_msg installing)${NC}"

    echo -e "${GREEN}$(get_msg installing_deps)${NC}"
    opkg update
    opkg install dnsmasq curl ca-bundle

    echo -e "${GREEN}$(get_msg creating_dirs)${NC}"
    mkdir -p /usr/sbin/ /etc/init.d/ /etc/config/ /etc/uci-defaults/ /usr/share/licenses/openwrt-captive-monitor/

    echo -e "${GREEN}$(get_msg copying_files)${NC}"
    cp /tmp/openwrt-captive-monitor/package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor /usr/sbin/
    cp /tmp/openwrt-captive-monitor/package/openwrt-captive-monitor/files/etc/init.d/captive-monitor /etc/init.d/
    cp /tmp/openwrt-captive-monitor/package/openwrt-captive-monitor/files/etc/config/captive-monitor /etc/config/

    echo -e "${GREEN}$(get_msg setting_perms)${NC}"
    sed -i 's/\r$//' /usr/sbin/openwrt_captive_monitor
    sed -i 's/\r$//' /etc/init.d/captive-monitor
    chmod +x /usr/sbin/openwrt_captive_monitor
    chmod +x /etc/init.d/captive-monitor

    # Set language in config
    uci set captive-monitor.@captive_monitor[0].language="$LANGUAGE"
    uci commit captive-monitor

    echo -e "${GREEN}$(get_msg install_success)${NC}"
}

# Function to configure the package
configure_package() {
    # Get language from config or use default
    CONFIG_LANG=$(uci -q get captive-monitor.@captive_monitor[0].language || echo "$LANGUAGE")
    if [ -n "$CONFIG_LANG" ]; then
        LANGUAGE="$CONFIG_LANG"
    fi

    echo -e "${GREEN}$(get_msg configuring)${NC}"

    # Enable the service
    uci set captive-monitor.@captive_monitor[0].enabled='1'
    uci set captive-monitor.@captive_monitor[0].wifi_interface="$WIFI_INTERFACE"
    uci set captive-monitor.@captive_monitor[0].wifi_logical="$WIFI_LOGICAL"
    uci set captive-monitor.@captive_monitor[0].monitor_interval="$MONITOR_INTERVAL"
    uci set captive-monitor.@captive_monitor[0].ping_servers="$PING_SERVERS"
    uci set captive-monitor.@captive_monitor[0].captive_check_urls="$CHECK_URLS"
    uci set captive-monitor.@captive_monitor[0].language="$LANGUAGE"
    uci commit captive-monitor

    echo -e "${GREEN}$(get_msg starting_service)${NC}"
    /etc/init.d/captive-monitor enable
    /etc/init.d/captive-monitor start

    if ! /etc/init.d/captive-monitor status > /dev/null 2>&1; then
        echo -e "${RED}$(get_msg service_failed)${NC}"
    fi

    echo -e "${GREEN}$(get_msg config_complete)${NC}"
}

# Function to uninstall the package
uninstall_package() {
    # Get language from config or use default
    CONFIG_LANG=$(uci -q get captive-monitor.@captive_monitor[0].language || echo "$LANGUAGE")
    if [ -n "$CONFIG_LANG" ]; then
        LANGUAGE="$CONFIG_LANG"
    fi

    echo -e "${RED}$(get_msg uninstalling)${NC}"

    # Stop and disable the service
    /etc/init.d/captive-monitor stop 2> /dev/null
    /etc/init.d/captive-monitor disable 2> /dev/null

    echo -e "${GREEN}$(get_msg removing_files)${NC}"
    rm -f /usr/sbin/openwrt_captive_monitor
    rm -f /etc/init.d/captive-monitor
    rm -f /etc/config/captive-monitor

    # Optionally remove dependencies (commented out by default)
    # echo -e "${GREEN}$(get_msg removing_deps)${NC}"
    # opkg remove dnsmasq curl ca-bundle

    echo -e "${GREEN}$(get_msg uninstall_success)${NC}"
}

# Function to show service status
show_status() {
    # Get language from config or use default
    CONFIG_LANG=$(uci -q get captive-monitor.@captive_monitor[0].language || echo "$LANGUAGE")
    if [ -n "$CONFIG_LANG" ]; then
        LANGUAGE="$CONFIG_LANG"
    fi

    echo -e "${GREEN}$(get_msg service_status)${NC}"
    /etc/init.d/captive-monitor status 2> /dev/null || echo -e "${YELLOW}$(get_msg not_running)${NC}"

    echo -e "\n${GREEN}$(get_msg configuration)${NC}"
    uci show captive-monitor 2> /dev/null || echo -e "${YELLOW}$(get_msg no_config)${NC}"

    echo -e "\n${GREEN}$(get_msg process_status)${NC}"
    if pgrep -f "openwrt_captive_monitor" > /dev/null; then
        echo -e "${GREEN}$(get_msg running)${NC}"
    else
        echo -e "${YELLOW}$(get_msg not_running)${NC}"
    fi
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
}

# Main script
case "$COMMAND" in
    install)
        install_package
        configure_package
        show_status
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

exit 0
