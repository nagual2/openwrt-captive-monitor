# Руководство быстрого старта

---

## 🌐 Язык

[English](quick-start.md) | [Deutsch](quick-start.de.md) | **[Русский](quick-start.ru.md)**

---

Запустите **openwrt-captive-monitor** на вашем маршрутизаторе OpenWrt всего за несколько минут.

## 🎯 Предварительные требования

- Маршрутизатор OpenWrt (рекомендуется 21.02+)
- Корневой доступ к маршрутизатору
- Базовое понимание конфигурации OpenWrt UCI

## 📦 Вариант 1: Установка готового пакета (Рекомендуется)

1. **Загрузите последний пакет**:
   ```bash
   wget https://github.com/nagual2/openwrt-captive-monitor/releases/latest/download/openwrt-captive-monitor_*.ipk
   ```

2. **Передайте на маршрутизатор**:
   ```bash
   scp openwrt-captive-monitor_*.ipk root@192.168.1.1:/tmp/
   ```

3. **Установите на маршрутизатор**:
   ```bash
   ssh root@192.168.1.1 "opkg install /tmp/openwrt-captive-monitor_*.ipk"
   ```

## 🔧 Вариант 2: Сборка из исходного кода

Подробные инструкции по сборке с помощью OpenWrt SDK см. в [Руководстве по установке](installation.md).

## ⚙️ Базовая конфигурация

1. **Включите сервис**:
   ```bash
   ssh root@192.168.1.1
   uci set captive-monitor.config.enabled='1'
   uci commit captive-monitor
   ```

2. **Настройте WiFi интерфейсы** (если они отличаются от значений по умолчанию):
   ```bash
   uci set captive-monitor.config.wifi_interface='phy1-sta0'
   uci set captive-monitor.config.wifi_logical='wwan'
   uci commit captive-monitor
   ```

3. **Запустите сервис**:
   ```bash
   /etc/init.d/captive-monitor enable
   /etc/init.d/captive-monitor start
   ```

## ✅ Проверка установки

Проверьте статус сервиса:
```bash
logread | grep captive-monitor
```

Вы должны увидеть логи, указывающие на то, что сервис контролирует подключение к Интернету.

## 🎉 Готово!

Монитор портала аутентификации теперь будет:
- Постоянно контролировать подключение к Интернету
- Автоматически обнаруживать порталы аутентификации
- Перенаправлять клиентов LAN на портал при необходимости
- Автоматически очищать систему при восстановлении доступа в Интернет

## 🔍 Следующие шаги

- [Продвинутая конфигурация](../configuration/advanced-config.md) - Точная настройка интервалов мониторинга и методов обнаружения
- [Решение проблем](../guides/troubleshooting.md) - Частые проблемы и решения
- [Пошаговый обход портала аутентификации](../guides/captive-portal-walkthrough.md) - Пример использования

## 🆘 Нужна помощь?

- Проверьте [Часто задаваемые вопросы](../project/faq.md) для общих вопросов
- Посетите наше [Руководство по поддержке](../../.github/SUPPORT.md)
- Откройте [проблему на GitHub](https://github.com/nagual2/openwrt-captive-monitor/issues)