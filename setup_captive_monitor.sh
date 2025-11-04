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
LANGUAGE="en"  # Default language

# Translation strings
declare -A MSG

# English messages
MSG[en,installing]="Installing OpenWRT Captive Monitor..."
MSG[en,installing_deps]="Installing required dependencies..."
MSG[en,creating_dirs]="Creating necessary directories..."
MSG[en,copying_files]="Copying package files..."
MSG[en,setting_perms]="Setting file permissions..."
MSG[en,install_success]="Package installed successfully"
MSG[en,configuring]="Configuring OpenWRT Captive Monitor..."
MSG[en,starting_service]="Enabling and starting the service..."
MSG[en,service_failed]="Warning: Failed to start captive-monitor service"
MSG[en,config_complete]="Configuration completed"
MSG[en,uninstalling]="Uninstalling OpenWRT Captive Monitor..."
MSG[en,removing_files]="Removing package files..."
MSG[en,removing_deps]="Removing dependencies..."
MSG[en,uninstall_success]="Package uninstalled successfully"
MSG[en,service_status]="=== Service Status ==="
MSG[en,configuration]="=== Configuration ==="
MSG[en,process_status]="=== Process Status ==="
MSG[en,running]="Captive monitor is running"
MSG[en,not_running]="Captive monitor is not running"
MSG[en,no_config]="No configuration found"

# Russian messages
MSG[ru,installing]="Установка OpenWRT Captive Monitor..."
MSG[ru,installing_deps]="Установка необходимых зависимостей..."
MSG[ru,creating_dirs]="Создание необходимых директорий..."
MSG[ru,copying_files]="Копирование файлов пакета..."
MSG[ru,setting_perms]="Установка прав доступа..."
MSG[ru,install_success]="Пакет успешно установлен"
MSG[ru,configuring]="Настройка OpenWRT Captive Monitor..."
MSG[ru,starting_service]="Включение и запуск службы..."
MSG[ru,service_failed]="Внимание: Не удалось запустить службу captive-monitor"
MSG[ru,config_complete]="Настройка завершена"
MSG[ru,uninstalling]="Удаление OpenWRT Captive Monitor..."
MSG[ru,removing_files]="Удаление файлов пакета..."
MSG[ru,removing_deps]="Удаление зависимостей..."
MSG[ru,uninstall_success]="Пакет успешно удален"
MSG[ru,service_status]="=== Статус службы ==="
MSG[ru,configuration]="=== Конфигурация ==="
MSG[ru,process_status]="=== Статус процесса ==="
MSG[ru,running]="Монитор активен"
MSG[ru,not_running]="Монитор не запущен"
MSG[ru,no_config]="Конфигурация не найдена"

# Function to get localized message
get_msg() {
    local key=$1
    local lang=${LANGUAGE:-en}
    echo "${MSG[${lang},${key}]:-${MSG[en,${key}]}}"
}

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root${NC}"
    exit 1
fi

# Function to install the package
install_package() {
    echo -e "${GREEN}$(get_msg installing)${NC}"
    
    echo -e "${GREEN}$(get_msg installing_deps)${NC}"
    opkg update
    opkg install dnsmasq-full curl ca-bundle
    
    echo -e "${GREEN}$(get_msg creating_dirs)${NC}"
    mkdir -p /usr/sbin/ /etc/init.d/ /etc/config/ /etc/uci-defaults/ /usr/share/licenses/openwrt-captive-monitor/
    
    # Copy files from the current directory (for manual installation)
    echo -e "${GREEN}$(get_msg copying_files)${NC}"
    cp /tmp/openwrt-captive-monitor/package/openwrt-captive-monitor/files/usr/sbin/openwrt_captive_monitor /usr/sbin/
    cp /tmp/openwrt-captive-monitor/package/openwrt-captive-monitor/files/etc/init.d/captive-monitor /etc/init.d/
    cp /tmp/openwrt-captive-monitor/package/openwrt-captive-monitor/files/etc/config/captive-monitor /etc/config/
    
    # Fix permissions
    chmod +x /usr/sbin/openwrt_captive_monitor
    chmod +x /etc/init.d/captive-monitor
    
    # Fix line endings and make files executable
    echo -e "${GREEN}$(get_msg setting_perms)${NC}"
    sed -i 's/\r$//' /usr/sbin/openwrt_captive_monitor
    sed -i 's/\r$//' /etc/init.d/captive-monitor
    chmod +x /usr/sbin/openwrt_captive_monitor
    chmod +x /etc/init.d/captive-monitor
    
    # Set default language in config
    uci set captive-monitor.@captive_monitor[0].language="$LANGUAGE"
    uci commit captive-monitor
    
    echo -e "${GREEN}$(get_msg install_success)${NC}"
}

# Function to configure the package
configure_package() {
    # Get language from config or use default
    LANGUAGE=$(uci -q get captive-monitor.@captive_monitor[0].language || echo "en")
    echo -e "${GREEN}$(get_msg configuring)${NC}"
    
    # Enable the service
    uci set captive-monitor.@captive_monitor[0].enabled='1'
    uci set captive-monitor.@captive_monitor[0].wifi_interface="$WIFI_INTERFACE"
    uci set captive-monitor.@captive_monitor[0].wifi_logical="$WIFI_LOGICAL"
    uci set captive-monitor.@captive_monitor[0].monitor_interval="$MONITOR_INTERVAL"
    uci set captive-monitor.@captive_monitor[0].ping_servers="$PING_SERVERS"
    uci set captive-monitor.@captive_monitor[0].captive_check_urls="$CHECK_URLS"
    uci commit captive-monitor
    
    # Enable and start the service
    echo -e "${GREEN}$(get_msg starting_service)${NC}"
    /etc/init.d/captive-monitor enable
    /etc/init.d/captive-monitor start
    
    # Check if service started successfully
    if ! /etc/init.d/captive-monitor status >/dev/null 2>&1; then
        echo -e "${RED}$(get_msg service_failed)${NC}"
    fi
    
    echo -e "${GREEN}$(get_msg config_complete)${NC}"
}

# Function to uninstall the package
uninstall_package() {
    # Get language from config or use default
    LANGUAGE=$(uci -q get captive-monitor.@captive_monitor[0].language || echo "en")
    echo -e "${RED}$(get_msg uninstalling)${NC}"
    
    # Stop and disable the service
    /etc/init.d/captive-monitor stop 2>/dev/null
    /etc/init.d/captive-monitor disable 2>/dev/null
    
    # Remove files and clean up
    echo -e "${GREEN}$(get_msg removing_files)${NC}"
    rm -f /usr/sbin/openwrt_captive_monitor
    rm -f /etc/init.d/captive-monitor
    rm -f /etc/config/captive-monitor
    
    # Optionally remove dependencies (commented out by default)
    # echo -e "${GREEN}$(get_msg removing_deps)${NC}"
    # opkg remove dnsmasq-full curl ca-bundle
    
    echo -e "${GREEN}$(get_msg uninstall_success)${NC}"
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
    echo "  --lang=XX   - Set language (en/ru), default: en"
}

# Function to show service status
show_status() {
    # Get language from config or use default
    LANGUAGE=$(uci -q get captive-monitor.@captive_monitor[0].language || echo "en")
    
    echo -e "${GREEN}$(get_msg service_status)${NC}"
    /etc/init.d/captive-monitor status 2>/dev/null || echo -e "${YELLOW}$(get_msg not_running)${NC}"
    
    echo -e "\n${GREEN}$(get_msg configuration)${NC}"
    uci show captive-monitor 2>/dev/null || echo -e "${YELLOW}$(get_msg no_config)${NC}"
    
    echo -e "\n${GREEN}$(get_msg process_status)${NC}"
    if pgrep -f "openwrt_captive_monitor" >/dev/null; then
        echo -e "${GREEN}$(get_msg running)${NC}"
    else
        echo -e "${YELLOW}$(get_msg not_running)${NC}"
    fi
}

# Main script
case "$1" in
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
    *)
        show_usage
        exit 1
        ;;
esac

exit 0
