# Виртуализированное тестирование OpenWrt Captive Monitor

---

## 🌐 Language / Язык

**English** | [Русский](README.ru.md)

---


> Комплексное руководство по настройке автоматизированного тестирования OpenWrt в виртуализированной среде для валидации пакетов и функциональности captive monitor.

## 📋 Обзор

Данный документ описывает стратегию виртуализированного тестирования для проекта openwrt-captive-monitor, дополняя существующий [тест-план](../TEST_PLAN.md) эмуляцией полноценной среды OpenWrt. Виртуализация позволяет проводить интеграционное тестирование на реальных системах OpenWrt без необходимости использования физического оборудования.

## 🏗️ Анализ платформ виртуализации

### QEMU с KVM ускорением
**Преимущества:**
- Нативная производительность для x86_64 гостевых систем
- Полная поддержка эмуляции сети (virtio-net)
- Совместимость с CI/CD системами
- Широкая поддержка в дистрибутивах Linux
- Поддержка снепшотов и отладки

**Недостатки:**
- Требует поддержки виртуализации на хосте (VT-x/AMD-V)
- Недоступно в GitHub Actions (нет nested virtualization)
- Более сложная настройка сетевых bridge

**Рекомендации:** Оптимальный выбор для локальной разработки и dedicated CI runners.

### QEMU TCG (полная эмуляция)
**Преимущества:**
- Работает без поддержки аппаратной виртуализации
- Полностью совместим с GitHub Actions runners
- Единая среда для всех хостов
- Надёжная изоляция

**Недостатки:**
- Значительно ниже производительность (3-5x медленнее)
- Высокое потребление CPU
- Ограничения по пропускной способности сети
- Длительное время загрузки системы

**Рекомендации:** Единственный вариант для GitHub Actions, подходит для smoke-тестов.

### Containerized OpenWrt rootfs
**Преимущества:**
- Минимальные накладные расходы
- Быстрый старт и остановка
- Эффективное использование ресурсов
- Простая интеграция с Docker

**Недостатки:**
- Ограниченная функциональность (нет полноценного сетевого стека)
- Проблемы с эмуляцией firewall правил
- Отсутствие настоящей изоляции сети
- Сложности с тестированием init-скриптов

**Рекомендации:** Подходит для unit-тестов, но не для интеграционного тестирования captive monitor.

### VirtualBox/VMware
**Преимущества:**
- Дружелюбный интерфейс управления
- Хорошая документация
- Поддержка снепшотов
- Кросс-платформенность

**Недостатки:**
- Требует GUI для первоначальной настройки
- Проблемы с автоматизацией в headless режиме
- Дополнительные зависимости
- Не подходит для CI/CD

**Рекомендации:** Только для ручного тестирования и отладки.

## 📦 Артефакты OpenWrt x86

### Рекомендуемые релизные каналы
- **Stable:** OpenWrt 24.10 LTS (рекомендуется для продакшена)
- **Testing:** OpenWrt 25.01 (для раннего тестирования новых функций)
- **Snapshot:** Последние сборки (для проверки совместимости)

### Типы образов
| Тип | Размер | Преимущества | Недостатки | Рекомендация |
|-----|-------|--------------|------------|--------------|
| combined-ext4 | ~150MB | Простота использования, изменяемый | Больший размер | **Рекомендуется** |
| combined-squashfs | ~80MB | Экономия места, защита от изменений | Требует overlayfs | Для CI |
| rootfs-ext4 | ~120MB | Гибкость настройки | Требует ручной сборки | Для продвинутых |
| generic-ext4 | ~140MB | Максимальная совместимость | Общие драйверы | Для тестирования |

### Системные требования
- **CPU:** Минимум 1 vCPU (рекомендуется 2 для QEMU KVM)
- **RAM:** Минимум 256MB (рекомендуется 512MB)
- **Диск:** 1GB свободного пространства для qcow2 overlay
- **Сеть:** Доступ к интернету для скачивания пакетов

### Контрольные суммы и проверка
```bash
# Проверка SHA256 для OpenWrt 24.10
wget https://downloads.openwrt.org/releases/24.10.0/targets/x86/64/openwrt-24.10.0-x86-64-generic-ext4-combined-efi.img.gz
echo "a1b2c3d4e5f6..." | sha256sum -c -
```

### Консольный доступ
```bash
# Serial console для отладки
qemu-system-x86_64 -nographic -serial mon:stdio \
  -drive if=virtio,file=openwrt.img,format=qcow2
```

## 🔧 Требования к хост-системе

### Базовые зависимости
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
  qemu-system-x86 \
  qemu-img \
  qemu-utils \
  expect \
  sshpass \
  curl \
  wget \
  genisoimage \
  util-linux

# Arch Linux
sudo pacman -Syu
sudo pacman -S --needed \
  qemu \
  expect \
  sshpass \
  curl \
  wget \
  libisoburn \
  util-linux
```

### Дополнительные утилиты
```bash
# Для работы с сетью
sudo apt-get install -y bridge-utils uml-utilities

# Для автоматизации
sudo apt-get install -y expect tcl

# Для отладки
sudo apt-get install -y tcpdump wireshark-common
```

### Права доступа
```bash
# Добавление пользователя в группы kvm и libvirt
sudo usermod -a -G kvm,libvirt $USER
newgrp kvm

# Проверка прав
test -w /dev/kvm && echo "KVM доступен" || echo "KVM недоступен"
```

### Сетевые настройки
```bash
# Создание bridge для сети VM
sudo brctl addbr br0
sudo ip addr add 192.168.100.1/24 dev br0
sudo ip link set br0 up

# Включение IP forwarding
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward
```

### Дисковое пространство
- **Минимум:** 5GB свободного места
- **Рекомендуется:** 20GB для кэша образов и логов
- **CI:** 10GB с очисткой после каждого запуска

### Переменные окружения
```bash
export OPENWRT_MIRROR="https://downloads.openwrt.org"
export OPENWRT_VERSION="24.10.0"
export OPENWRT_TARGET="x86/64"
export VM_MEMORY="512"
export VM_CPUS="2"
export VM_TIMEOUT="300"
```

## 🚀 Совместимость с GitHub Actions CI

### Ограничения runners
- **Нет nested virtualization:** Только QEMU TCG
- **Ограниченные ресурсы:** 2 CPU, 7GB RAM, 14GB диска
- **Временные лимиты:** 6 часов для job
- **Сетевые ограничения:** Ограниченная пропускная способность

### Оптимизация для CI
```yaml
- name: Setup QEMU for CI
  run: |
    # Использование TCG вместо KVM
    export QEMU_CPU="max"
    # Оптимизация памяти
    export VM_MEMORY="256"
    # Кэширование образов между запусками
    echo "CACHE_DIR=$HOME/.cache/openwrt-images" >> $GITHUB_ENV
```

### Стратегия кэширования
```yaml
- name: Cache OpenWrt images
  uses: actions/cache@v4
  with:
    path: ~/.cache/openwrt-images
    key: openwrt-${{ env.OPENWRT_VERSION }}-${{ env.OPENWRT_TARGET }}
    restore-keys: |
      openwrt-${{ env.OPENWRT_VERSION }}-
      openwrt-
```

### Управление артефактами
```yaml
- name: Upload VM logs
  uses: actions/upload-artifact@v4
  if: always()
  with:
    name: vm-logs-${{ github.run_number }}
    path: |
      vm-logs/
      test-results/
    retention-days: 7
```

### Оценка времени выполнения
- **Подготовка окружения:** 2-3 минуты
- **Загрузка VM:** 3-5 минут (TCG)
- **Установка пакета:** 1-2 минуты
- **Выполнение тестов:** 2-4 минуты
- **Очистка:** 30 секунд

**Итого:** 8-14 минут на полный цикл тестирования

## 🔄 Автоматизированный workflow

### Общая схема процесса
```
1. Подготовка окружения
   ↓
2. Скачивание OpenWrt образа
   ↓
3. Создание qcow2 overlay
   ↓
4. Запуск VM (QEMU)
   ↓
5. Ожидание инициализации системы
   ↓
6. Генерация SSH ключей
   ↓
7. Установка пакета (.ipk)
   ↓
8. Конфигурация через UCI
   ↓
9. Выполнение валидации
   ↓
10. Сбор логов и артефактов
    ↓
11. Остановка VM и очистка
```

### Ключевые этапы автоматизации

#### 1. Подготовка окружения
```bash
setup_environment() {
    mkdir -p "${VM_WORK_DIR}"
    cd "${VM_WORK_DIR}"
    
    # Проверка зависимостей
    check_dependencies qemu-system-x86_64 qemu-img expect sshpass
    
    # Настройка сети
    setup_tap_network
    
    # Подготовка SSH ключей
    ssh-keygen -t rsa -N "" -f vm_key
}
```

#### 2. Управление образами
```bash
download_openwrt_image() {
    local base_url="${OPENWRT_MIRROR}/releases/${OPENWRT_VERSION}/targets/${OPENWRT_TARGET}"
    local image_name="openwrt-${OPENWRT_VERSION}-${OPENWRT_TARGET//\//-}-generic-ext4-combined-efi.img.gz"
    
    wget "${base_url}/${image_name}"
    gunzip "${image_name}"
    
    # Создание overlay для сохранения изменений
    qemu-img create -f qcow2 -b "${image_name%.gz}" -F raw overlay.qcow2
}
```

#### 3. Запуск VM
```bash
start_vm() {
    qemu-system-x86_64 \
      -m "${VM_MEMORY}" \
      -smp "${VM_CPUS}" \
      -cpu "${QEMU_CPU:-host}" \
      -drive if=virtio,file=overlay.qcow2,format=qcow2 \
      -netdev tap,id=net0,ifname=tap0,script=no,downscript=no \
      -device virtio-net-pci,netdev=net0 \
      -nographic \
      -serial mon:stdio \
      -pidfile vm.pid \
      -daemonize
    
    # Ожидание готовности VM
    wait_for_vm_ready
}
```

#### 4. Провизионирование
```bash
provision_vm() {
    local vm_ip="192.168.100.2"
    
    # Копирование SSH ключа
    ssh-copy-id -i vm_key.pub root@${vm_ip}
    
    # Установка зависимостей
    ssh root@${vm_ip} "opkg update && opkg install curl dnsmasq-full"
    
    # Загрузка пакета
    scp openwrt-captive-monitor_*.ipk root@${vm_ip}:/tmp/
    
    # Установка пакета
    ssh root@${vm_ip} "opkg install /tmp/openwrt-captive-monitor_*.ipk"
}
```

#### 5. Валидация
```bash
run_validation() {
    local vm_ip="192.168.100.2"
    
    # Базовые тесты
    ssh root@${vm_ip} "openwrt_captive_monitor --help"
    ssh root@${vm_ip} "openwrt_captive_monitor --oneshot"
    
    # Тестирование firewall
    test_firewall_rules ${vm_ip}
    
    # Тестирование DNS redirects
    test_dns_redirects ${vm_ip}
    
    # Проверка cleanup
    test_cleanup ${vm_ip}
}
```

## 🛠️ Инструкция по настройке рабочей станции

### Шаг 1: Установка зависимостей
```bash
# Обновление системы
sudo apt-get update && sudo apt-get upgrade -y

# Установка QEMU и утилит
sudo apt-get install -y qemu-system-x86 qemu-utils qemu-img

# Установка утилит автоматизации
sudo apt-get install -y expect sshpass curl wget

# Установка сетевых утилит
sudo apt-get install -y bridge-utils uml-utilities tcpdump
```

### Шаг 2: Настройка прав доступа
```bash
# Добавление в группы
sudo usermod -a -G kvm,libvirt,input $USER

# Применение изменений
newgrp kvm

# Проверка
groups | grep kvm
```

### Шаг 3: Настройка сети
```bash
# Создание TAP интерфейса
sudo tunctl -t tap0 -u $USER
sudo ip link set tap0 up

# Создание bridge
sudo brctl addbr br0
sudo brctl addif br0 tap0
sudo ip addr add 192.168.100.1/24 dev br0
sudo ip link set br0 up

# Настройка NAT
sudo iptables -t nat -A POSTROUTING -s 192.168.100.0/24 -j MASQUERADE
```

### Шаг 4: Подготовка рабочей директории
```bash
mkdir -p ~/openwrt-testing/{images,logs,scripts}
cd ~/openwrt-testing

# Создание конфигурационного файла
cat > config.env << 'EOF'
export OPENWRT_VERSION="24.10.0"
export OPENWRT_TARGET="x86/64"
export VM_MEMORY="512"
export VM_CPUS="2"
export VM_TIMEOUT="300"
export VM_NETWORK="192.168.100.0/24"
export VM_IP="192.168.100.2"
export VM_HOST_IP="192.168.100.1"
EOF
```

### Шаг 5: Тестовая проверка
```bash
# Скачивание тестового образа
wget https://downloads.openwrt.org/releases/24.10.0/targets/x86/64/openwrt-24.10.0-x86-64-generic-ext4-combined-efi.img.gz

# Распаковка
gunzip openwrt-24.10.0-x86-64-generic-ext4-combined-efi.img.gz

# Создание overlay
qemu-img create -f qcow2 -b openwrt-24.10.0-x86-64-generic-ext4-combined-efi.img -F raw test-overlay.qcow2

# Тестовый запуск
qemu-system-x86_64 -m 512 -drive if=virtio,file=test-overlay.qcow2,format=qcow2 -netdev user,id=net0 -device virtio-net-pci,netdev=net0 -nographic
```

### Шаг 6: Очистка после тестирования
```bash
cleanup_testing() {
    # Остановка VM
    if [ -f vm.pid ]; then
        kill $(cat vm.pid) 2>/dev/null || true
        rm -f vm.pid
    fi
    
    # Удаление временных файлов
    rm -f *.qcow2 *.img.gz
    
    # Очистка сетевых интерфейсов
    sudo ip link set tap0 down 2>/dev/null || true
    sudo ip link set br0 down 2>/dev/null || true
    sudo brctl delbr br0 2>/dev/null || true
    
    # Очистка логов
    rm -f logs/*
}
```

## 🔗 Интеграция с существующей стратегией QA

### Соотношение с текущим тест-планом
| Уровень | Существующий подход | Виртуализированное дополнение |
|---------|-------------------|------------------------------|
| Unit-тесты | Mock-based тесты | Без изменений |
| Интеграционные | Эмуляция OpenWrt контейнер | Полная VM эмуляция |
| Системные | Ручное тестирование на устройстве | Автоматизированное VM тестирование |
| Регрессионные | Локальные проверки | CI/CD интеграция |

### Дополнение к docs/TEST_PLAN.md
Виртуализированное тестирование добавляет новый уровень между "Эмуляция OpenWrt 24.x" и "Полевые испытания":

```markdown
## 2.5. Виртуализированное тестирование (CI/локальное)
- Автоматизированная валидация на полной VM OpenWrt
- Тестирование установщика и init-скриптов
- Проверка firewall правил в реальной среде
- Регрессионное тестирование в CI
```

### Обновление docs/index.md
Добавить в раздел "📋 Development":
```markdown
- [Virtualized Testing Guide](guides/virtualized-testing.md) - VM-based testing strategy and automation
```

### Метрики успеха
- **Покрытие тестами:** Дополнение к mock-based тестам
- **Время выполнения:** 8-14 минут в CI
- **Надёжность:** >95% успешных запусков
- **Обнаружение дефектов:** Интеграционные проблемы, не видимые в mocks

## 📊 Рекомендации по внедрению

### Фаза 1: Базовая инфраструктура (1-2 недели)
- Настройка базовых скриптов для VM управления
- Интеграция с существующей сборкой .ipk
- Простая валидация (установка, запуск, проверка версии)

### Фаза 2: Расширенное тестирование (2-3 недели)
- Автоматизированная проверка firewall правил
- Тестирование DNS/HTTP redirects
- Валидация cleanup процедур
- Интеграция с GitHub Actions

### Фаза 3: Оптимизация и CI/CD (1-2 недели)
- Кэширование образов
- Параллельное выполнение тестов
- Оптимизация для CI runners
- Генерация отчётов и артефактов

## 🔍 Отладка и troubleshooting

### Распространённые проблемы
```bash
# VM не запускается
qemu-system-x86_64: -drive if=virtio,file=overlay.qcow2,format=qcow2: Could not open 'overlay.qcow2': No such file or directory
# Решение: Проверить путь к файлу и права доступа

# Нет сети в VM
# Решение: Проверить настройки TAP интерфейса и bridge

# SSH недоступен
# Решение: Проверить IP адрес и настройки файрвола

# Тесты падают по таймауту
# Решение: Увеличить VM_TIMEOUT или проверить производительность
```

### Полезные команды отладки
```bash
# Мониторинг VM
qemu-monitor -h $(cat vm.pid)

# Проверка сети
tcpdump -i tap0 -n

# Логи VM
ssh root@${VM_IP} "logread | grep captive"

# Статус сервисов
ssh root@${VM_IP} "/etc/init.d/captive-monitor status"
```

## 📝 Заключение

Виртуализированное тестирование предоставляет мощный инструментарий для автоматизации валидации OpenWrt пакетов, дополняя существующие mock-based тесты и ручное тестирование на оборудовании. Интеграция с CI/CD позволяет обеспечить стабильность релизов и раннее обнаружение регрессий.

Рекомендуется начать с базовой инфраструктуры и постепенно расширять функциональность тестирования, опираясь на потребности проекта и доступные ресурсы CI.