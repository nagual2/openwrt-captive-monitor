# Virtualization Testing

---

## 🌐 Language / Язык

**English** | [Русский](README.ru.md)

---

This directory contains documentation and wrappers for VM-based testing of the openwrt-captive-monitor package.

## Quick Start

The VM test harness provides automated end-to-end testing in a virtualized OpenWrt environment:

```bash
# From repository root
./scripts/run_openwrt_vm.sh
```

## Manual Testing

For manual testing and debugging:

```bash
# Run with custom settings
./scripts/run_openwrt_vm.sh \
    --openwrt-version 24.02 \
    --workdir /tmp/openwrt-test \
    --reuse-vm

# CI environment (no KVM acceleration)
./scripts/run_openwrt_vm.sh --reuse-vm --no-kvm
```

## Test Scenarios

The VM harness automatically executes these test scenarios:

1. **Baseline Test** - Normal operation with internet connectivity
2. **Captive Portal Simulation** - Blocked traffic with HTTP server
3. **Monitor Mode Test** - Continuous monitoring with short interval

## Artifacts

Test results and logs are collected in the working directory:

```
dist/vm-tests/artifacts/
├── vm_console.log       # VM boot and console output
├── test_*.log           # Individual test results
├── iptables.log         # Firewall rules state
├── nftables.log         # nftables ruleset
└── *.log                # Additional system logs
```

## Troubleshooting

For troubleshooting and advanced usage, see the [Virtualization Guide](../../docs/guides/virtualization.md).

## Prerequisites

Ensure the following tools are installed:

```bash
# Ubuntu/Debian
sudo apt-get install -y curl xz-utils qemu-system-x86 qemu-utils expect openssh-client

# Optional: KVM acceleration
sudo usermod -a -G kvm $USER
```

## Integration

The VM test harness is designed to integrate with CI/CD systems:

- **GitHub Actions**: Use `--reuse-vm --no-kvm` for consistent testing
- **Jenkins**: Archive `dist/vm-tests/artifacts/` for test results
- **Local Development**: Use default settings for quick iteration

## Support

For issues with the VM test harness:

1. Check the [Virtualization Guide](../../docs/guides/virtualization.md)
2. Review test artifacts for detailed error information
3. Open an issue with logs and environment details

---

## Русский

---

## 🌐 Язык

[English](#virtualization-testing) | **Русский**

---

## Тестирование виртуализации

Этот каталог содержит документацию и обертки для тестирования на основе ВМ пакета openwrt-captive-monitor.

## Быстрый старт

Виртуальная машина для тестирования обеспечивает автоматизированное сквозное тестирование в виртуализированной среде OpenWrt:

```bash
# Из корня репозитория
./scripts/run_openwrt_vm.sh
```

## Ручное тестирование

Для ручного тестирования и отладки:

```bash
# Запустить с пользовательскими параметрами
./scripts/run_openwrt_vm.sh \
    --openwrt-version 24.02 \
    --workdir /tmp/openwrt-test \
    --reuse-vm

# CI окружение (без ускорения KVM)
./scripts/run_openwrt_vm.sh --reuse-vm --no-kvm
```

## Сценарии тестирования

Виртуальная машина для тестирования автоматически выполняет эти сценарии тестирования:

1. **Базовый тест** - Нормальная работа с подключением в Интернет
2. **Симуляция портала аутентификации** - Заблокированный трафик с HTTP сервером
3. **Тест режима монитора** - Непрерывный мониторинг с коротким интервалом

## Артефакты

Результаты тестирования и логи собираются в рабочем каталоге:

```
dist/vm-tests/artifacts/
├── vm_console.log       # Загрузка ВМ и вывод консоли
├── test_*.log           # Результаты отдельных тестов
├── iptables.log         # Состояние правил файервола
├── nftables.log         # Набор правил nftables
└── *.log                # Дополнительные логи системы
```

## Решение проблем

Подробнее см. [Руководство по виртуализации](../../docs/guides/virtualization.md).

## Предварительные требования

Убедитесь, что установлены следующие инструменты:

```bash
# Ubuntu/Debian
sudo apt-get install -y curl xz-utils qemu-system-x86 qemu-utils expect openssh-client

# Опционально: ускорение KVM
sudo usermod -a -G kvm $USER
```

## Интеграция

Виртуальная машина для тестирования предназначена для интеграции с системами CI/CD:

- **GitHub Actions**: Используйте `--reuse-vm --no-kvm` для согласованного тестирования
- **Jenkins**: Архивируйте `dist/vm-tests/artifacts/` для результатов тестирования
- **Локальная разработка**: Используйте параметры по умолчанию для быстрой итерации

## Поддержка

Для проблем с виртуальной машиной для тестирования:

1. Проверьте [Руководство по виртуализации](../../docs/guides/virtualization.md)
2. Просмотрите артефакты тестирования для получения подробной информации об ошибках
3. Откройте проблему с логами и деталями окружения
