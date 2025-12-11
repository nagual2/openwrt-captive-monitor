# Implementation Plan

- [x] 1. Удалить IPv6 функции из основного скрипта





  - Удалить функцию `ensure_lan_ipv6()`
  - Удалить функцию `resolve_portal_ipv6()`
  - Удалить функцию `is_ipv6()` из awk скрипта
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 2. Удалить IPv6 переменные из основного скрипта





  - Удалить объявление переменной `LAN_IPV6`
  - Удалить объявление переменной `HTTPD_IPV6_READY`
  - Удалить все присваивания этим переменным
  - _Requirements: 1.1, 3.4, 3.5_

- [x] 3. Удалить чтение IPv6 конфигурации из UCI





  - Удалить строку `value=$(uci_safe_get "${section}.lan_ipv6")`
  - Удалить строку `[ -n "$value" ] && LAN_IPV6="$value"`
  - _Requirements: 1.2_

- [x] 4. Обновить запуск HTTP сервера для IPv4 only





  - Удалить попытку запуска с `[::]`
  - Оставить только запуск с `0.0.0.0`
  - Удалить fallback логику для IPv6
  - Удалить установку `HTTPD_IPV6_READY=1`
  - _Requirements: 1.3_

- [x] 5. Удалить ip6tables правила для HTTP перехвата





  - Удалить весь блок `if [ "$HTTPD_IPV6_READY" = "1" ]; then`
  - Удалить проверку `if ensure_lan_ipv6; then`
  - Удалить создание правил ip6tables для HTTP DNAT
  - Удалить создание правил ip6tables для HTTP PREROUTING
  - _Requirements: 1.4_

- [x] 6. Удалить ip6tables правила для DNS перехвата





  - Удалить создание правил ip6tables для DNS UDP DNAT
  - Удалить создание правил ip6tables для DNS TCP DNAT
  - Удалить создание правил ip6tables для DNS PREROUTING
  - _Requirements: 1.4_

- [x] 7. Удалить IPv6 адреса из dnsmasq конфигурации





  - Удалить строку `echo "address=/#/$LAN_IPV6"`
  - Удалить строку `echo "address=/$portal_host/$portal_ip6"`
  - Удалить условия проверки `HTTPD_IPV6_READY`
  - _Requirements: 1.5_

- [x] 8. Обновить логирование для удаления упоминаний IPv6





  - Изменить "Запущен busybox httpd (PID $pid) для редиректа (IPv4/IPv6)" на "Запущен busybox httpd (PID $pid) для редиректа"
  - Удалить "Не удалось запустить busybox httpd с IPv6, пробуем только IPv4"
  - Удалить все log_warn с упоминанием ip6tables
  - Удалить все log_warn с упоминанием IPv6 адресов
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 9. Checkpoint - убедиться, что код компилируется и запускается





  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Обновить документацию README.md





  - Удалить все упоминания IPv6 функциональности
  - Удалить примеры конфигурации с lan_ipv6
  - Добавить явное указание "IPv6 не поддерживается"
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 11. Обновить документацию в docs/





  - Найти все файлы с упоминанием IPv6
  - Удалить инструкции по настройке IPv6
  - Удалить примеры с IPv6 адресами
  - _Requirements: 4.2, 4.3_

- [x] 12. Обновить примеры конфигурации





  - Удалить опцию lan_ipv6 из примеров UCI конфигурации
  - Удалить примеры с IPv6 адресами
  - Добавить комментарий "Поддерживается только IPv4"
  - _Requirements: 8.1, 8.2, 8.4_

- [x] 13. Обновить документацию конфигурационных опций





  - Удалить описание параметра lan_ipv6
  - Указать, что поддерживается только IPv4
  - _Requirements: 8.3, 8.4_

- [x] 14. Добавить запись в CHANGELOG.md




  - Создать новую секцию для версии
  - Добавить BREAKING CHANGE об удалении IPv6
  - Указать, что legacy параметры игнорируются
  - Указать, что системные настройки IPv6 не изменяются
  - _Requirements: 4.5_

- [x] 15. Удалить IPv6 тесты из tests/





  - Найти и удалить тесты функций ensure_lan_ipv6, resolve_portal_ipv6
  - Удалить моки для ip6tables
  - Удалить тестовые данные с IPv6 адресами
  - _Requirements: 6.1, 6.2, 6.3_

- [ ]* 16. Добавить property-based тест для проверки отсутствия IPv6 в коде
  - **Property 1: Code IPv6 Absence**
  - **Validates: Requirements 1.1, 1.2, 1.4, 3.1, 3.2, 3.3, 3.4, 3.5**
  - Создать bats тест, который проверяет все исходные файлы
  - Использовать grep для поиска IPv6 идентификаторов
  - Проверять: LAN_IPV6, HTTPD_IPV6_READY, ensure_lan_ipv6, resolve_portal_ipv6, is_ipv6, ip6tables, lan_ipv6

- [ ]* 17. Добавить property-based тест для проверки отсутствия IPv6 в документации
  - **Property 2: Documentation IPv6 Absence**
  - **Validates: Requirements 4.1, 4.2, 4.3, 8.2, 8.3**
  - Создать bats тест, который проверяет все файлы документации
  - Использовать grep для поиска IPv6 примеров и инструкций
  - Исключить явное указание "IPv6 не поддерживается"

- [ ]* 18. Добавить property-based тест для проверки отсутствия IPv6 в логах
  - **Property 3: Log Messages IPv6 Absence**
  - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
  - Создать bats тест, который запускает систему и проверяет логи
  - Использовать grep для поиска упоминаний IPv6, ip6tables, IPv6 адресов

- [ ]* 19. Добавить property-based тест для проверки отсутствия IPv6 в тестах
  - **Property 4: Test Code IPv6 Absence**
  - **Validates: Requirements 6.1, 6.2, 6.3**
  - Создать bats тест, который проверяет все тестовые файлы
  - Использовать grep для поиска IPv6 функций, моков, тестовых данных

- [ ]* 20. Добавить unit тест для проверки обработки legacy конфигурации
  - **Property 5: Configuration IPv6 Graceful Handling**
  - **Validates: Requirements 8.5**
  - Создать тестовую UCI конфигурацию с lan_ipv6
  - Запустить систему и убедиться, что нет ошибок
  - Проверить, что параметр игнорируется

- [ ]* 21. Добавить unit тест для проверки запуска HTTP сервера
  - **Example 1: HTTP server starts with IPv4 only**
  - **Validates: Requirements 1.3**
  - Создать mock для busybox httpd
  - Запустить функцию запуска HTTP сервера
  - Проверить, что вызов содержит 0.0.0.0, а не [::]

- [ ]* 22. Добавить unit тест для проверки dnsmasq конфигурации
  - **Example 2: dnsmasq configuration contains no IPv6 addresses**
  - **Validates: Requirements 1.5**
  - Запустить функцию создания dnsmasq конфигурации
  - Прочитать созданный файл
  - Проверить, что нет IPv6 адресов (паттерн с :)

- [ ]* 23. Добавить unit тест для проверки деактивации
  - **Example 7: Deactivation does not call ip6tables commands**
  - **Validates: Requirements 7.4**
  - Создать mock для ip6tables
  - Запустить функцию деактивации captive portal
  - Проверить, что ip6tables не вызывался

- [x] 24. Checkpoint - запустить все тесты




  - Ensure all tests pass, ask the user if questions arise.

- [x] 25. Обновить VERSION и создать коммит




  - Запустить `bash scripts/update-version-metadata.sh <new_version>`
  - Создать коммит с сообщением "feat!: remove IPv6 support"
  - _Requirements: все_
