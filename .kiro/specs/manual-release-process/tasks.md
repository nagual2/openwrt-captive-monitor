# Implementation Plan

- [x] 1. Создать manual-release workflow





  - Создать `.github/workflows/manual-release.yml`
  - Добавить workflow_dispatch trigger с параметрами (version, release_notes, prerelease)
  - Настроить permissions для contents: write
  - _Requirements: 1.1, 1.2, 1.4, 5.1, 5.2, 5.3_

- [x] 1.1 Реализовать генерацию версии


  - Добавить step для генерации версии на основе текущей даты
  - Реализовать логику инкремента порядкового номера при конфликте
  - Поддержать кастомную версию из input параметра
  - _Requirements: 1.1, 1.4_

- [x] 1.2 Реализовать обновление VERSION и Makefile


  - Добавить step для обновления VERSION файла
  - Добавить step для обновления PKG_VERSION в Makefile
  - Настроить git config для коммитов
  - _Requirements: 2.1, 2.2_

- [x] 1.3 Реализовать создание коммита и тега


  - Добавить step для создания коммита с изменениями версии
  - Добавить step для создания git тега
  - Добавить push коммита и тега в origin
  - _Requirements: 2.3, 2.4_

- [x] 1.4 Интегрировать сборку пакета


  - Использовать логику из simple-release.yml для сборки
  - Добавить setup opkg-utils
  - Добавить сборку с --arch all
  - Добавить валидацию пакета
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 1.5 Реализовать публикацию релиза


  - Добавить step для создания GitHub Release
  - Использовать release notes из input или автоматические
  - Загрузить .ipk файл и SHA256SUMS
  - Поддержать prerelease флаг
  - _Requirements: 4.4, 5.1, 5.2, 5.3_

- [x] 2. Отключить автоматический auto-version workflow





  - Закомментировать push trigger в auto-version-tag.yml
  - Оставить workflow_dispatch для ручного тестирования
  - Добавить комментарий о причине отключения
  - _Requirements: 3.1, 3.3_

- [x] 3. Обновить документацию





  - Добавить секцию "Creating a Release" в README.md
  - Обновить CONTRIBUTING.md с новым процессом релиза
  - Документировать параметры manual-release workflow
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 4. Протестировать новый процесс



  - Создать тестовый релиз через manual-release workflow
  - Проверить создание коммита, тега и релиза
  - Проверить наличие артефактов в релизе
  - Проверить что auto-version не запускается при push в main
  - _Requirements: 1.1, 1.2, 3.1, 4.4_

- [ ] 5. Очистка старых workflows
  - Удалить или архивировать tag-build-release.yml (использует SDK с ошибками)
  - Обновить комментарии в оставшихся workflows
  - _Requirements: 3.2_

- [ ] 6. Final Checkpoint - Убедиться что всё работает
  - Убедиться что все тесты проходят, спросить пользователя если возникают вопросы
