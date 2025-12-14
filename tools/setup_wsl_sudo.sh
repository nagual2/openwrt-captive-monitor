#!/bin/bash
# Настройка sudo без пароля для сетевых команд в WSL

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Получить имя пользователя
USERNAME=$(whoami)

log "Настройка sudo без пароля для пользователя: $USERNAME"

# Создать sudoers файл для сетевых команд
SUDOERS_FILE="/etc/sudoers.d/wsl-routing"

log "Создаем sudoers правило: $SUDOERS_FILE"

# Команды, которые нужны для управления маршрутизацией
ALLOWED_COMMANDS=(
    "/sbin/ip route add *"
    "/sbin/ip route del *"
    "/usr/sbin/ip route add *"
    "/usr/sbin/ip route del *"
    "/bin/ip route add *"
    "/bin/ip route del *"
)

# Создать временный файл с правилами
TEMP_SUDOERS=$(mktemp)

cat > "$TEMP_SUDOERS" << EOF
# WSL Routing Manager - разрешить управление маршрутами без пароля
# Создано автоматически $(date)

# Разрешить пользователю $USERNAME выполнять команды ip route без пароля
$USERNAME ALL=(ALL) NOPASSWD: /sbin/ip route add *, /sbin/ip route del *
$USERNAME ALL=(ALL) NOPASSWD: /usr/sbin/ip route add *, /usr/sbin/ip route del *
$USERNAME ALL=(ALL) NOPASSWD: /bin/ip route add *, /bin/ip route del *

# Альтернативно - разрешить все команды ip (менее безопасно)
# $USERNAME ALL=(ALL) NOPASSWD: /sbin/ip, /usr/sbin/ip, /bin/ip
EOF

log "Содержимое sudoers правила:"
cat "$TEMP_SUDOERS"

echo
warning "Это правило разрешит выполнение команд 'ip route' без пароля"
warning "Продолжить? (y/N)"
read -r confirmation

if [[ ! "$confirmation" =~ ^[Yy] ]]; then
    log "Операция отменена"
    rm -f "$TEMP_SUDOERS"
    exit 0
fi

# Проверить синтаксис sudoers файла
if ! sudo visudo -c -f "$TEMP_SUDOERS"; then
    error "Ошибка в синтаксисе sudoers файла"
    rm -f "$TEMP_SUDOERS"
    exit 1
fi

# Установить файл
log "Устанавливаем sudoers правило..."
sudo cp "$TEMP_SUDOERS" "$SUDOERS_FILE"
sudo chmod 440 "$SUDOERS_FILE"
sudo chown root:root "$SUDOERS_FILE"

# Очистить временный файл
rm -f "$TEMP_SUDOERS"

success "Sudoers правило установлено: $SUDOERS_FILE"

# Проверить, что правило работает
log "Тестируем sudo без пароля..."

if sudo -n ip route show >/dev/null 2>&1; then
    success "Sudo без пароля работает корректно!"
else
    error "Sudo без пароля не работает"
    log "Проверьте файл: $SUDOERS_FILE"
    exit 1
fi

echo
success "Настройка завершена успешно!"
log "Теперь можно использовать wsl_routing_manager.sh без ввода пароля"

# Показать как использовать
echo
log "Примеры использования:"
echo "  ./tools/wsl_routing_manager.sh status    # Проверить статус"
echo "  ./tools/wsl_routing_manager.sh enable    # Включить маршрутизацию через dev"
echo "  ./tools/wsl_routing_manager.sh disable   # Отключить маршрутизацию"
echo "  ./tools/wsl_routing_manager.sh test      # Протестировать подключение"
