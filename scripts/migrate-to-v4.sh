#!/bin/bash
# migrate-to-v4.sh - Миграция контейнера captive-portal-dual на v4
# Выполняется на минисфоруме

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Миграция captive-portal-dual на v4 ===${NC}"
echo ""

# Проверка аргументов
if [ -z "$1" ]; then
    echo -e "${RED}Ошибка: Укажите источник образа${NC}"
    echo "Использование: $0 <truenas-ip>"
    echo "Пример: $0 192.168.1.100"
    exit 1
fi

TRUENAS_IP=$1
echo -e "${GREEN}Источник: TrueNAS DEV ($TRUENAS_IP)${NC}"
echo ""

# 1. Экспорт образа с TrueNAS
echo -e "${YELLOW}1. Экспорт образа с TrueNAS...${NC}"
ssh root@$TRUENAS_IP "docker save captive-portal-dual:v4 | gzip" > /tmp/captive-portal-dual-v4.tar.gz
echo -e "${GREEN}✓ Образ экспортирован${NC}"
echo ""

# 2. Импорт образа на минисфоруме
echo -e "${YELLOW}2. Импорт образа на минисфоруме...${NC}"
gunzip -c /tmp/captive-portal-dual-v4.tar.gz | docker load
echo -e "${GREEN}✓ Образ импортирован как captive-portal-dual:v4${NC}"
echo ""

# 3. Остановка текущего контейнера (без удаления)
echo -e "${YELLOW}3. Остановка текущего контейнера...${NC}"
if docker ps -q -f name=captive-portal-dual | grep -q .; then
    docker stop captive-portal-dual
    echo -e "${GREEN}✓ Контейнер остановлен (контейнер сохранён)${NC}"
else
    echo -e "${YELLOW}⚠ Контейнер не был запущен${NC}"
fi
echo ""

# 4. Переименование старого контейнера (на всякий случай)
echo -e "${YELLOW}4. Сохранение старого контейнера...${NC}"
if docker ps -a -q -f name=captive-portal-dual | grep -q .; then
    docker rename captive-portal-dual captive-portal-dual-backup-$(date +%Y%m%d-%H%M%S)
    echo -e "${GREEN}✓ Старый контейнер переименован в captive-portal-dual-backup-*${NC}"
fi
echo ""

# 5. Запуск нового контейнера v4
echo -e "${YELLOW}5. Запуск нового контейнера v4...${NC}"
cd /opt/captive-portal-dual || cd ~/captive-portal-dual || cd /root/captive-portal-dual

# Проверяем наличие docker-compose.v4.yml
if [ ! -f docker-compose.v4.yml ]; then
    echo -e "${RED}Ошибка: docker-compose.v4.yml не найден${NC}"
    echo "Создайте конфигурацию перед запуском"
    exit 1
fi

docker-compose -f docker-compose.v4.yml up -d
echo -e "${GREEN}✓ Новый контейнер запущен${NC}"
echo ""

# 6. Проверка статуса
echo -e "${YELLOW}6. Проверка статуса...${NC}"
sleep 3
docker ps -f name=captive-portal-dual
echo ""

# 7. Проверка логов
echo -e "${YELLOW}7. Последние логи:${NC}"
docker logs --tail 20 captive-portal-dual
echo ""

echo -e "${GREEN}=== Миграция завершена ===${NC}"
echo ""
echo "Команды для управления:"
echo "  docker ps -a                    # Список всех контейнеров"
echo "  docker logs -f captive-portal-dual  # Логи в реальном времени"
echo "  docker-compose -f docker-compose.v4.yml down  # Остановка"
echo ""
echo "Для отката (если нужно):"
echo "  docker stop captive-portal-dual"
echo "  docker rm captive-portal-dual"
echo "  docker rename captive-portal-dual-backup-XXX captive-portal-dual"
echo "  # запустить старый docker-compose"
