# План продолжения разработки функционала сборки пакетов (OpenWrt)

Цель: довести и стандартизировать сборку пакета openwrt-captive-monitor в CI/CD с гарантированной воспроизводимостью, предсказуемой версификацией, безопасной поставкой артефактов и удобной диагностики.

Вводные и существующие компоненты
- Билды в CI выполняются через OpenWrt SDK (openwrt/gh-action-sdk@v6).
- Контейнер SDK: ghcr.io/openwrt/sdk:{arch}-{version}; передаётся в action через env CONTAINER.
- Локальный feed (FEED_DIR, FEEDNAME=local), PACKAGES указывает собираемый пакет.
- Скрипты в репозитории:
  - scripts/validate-sdk-image.sh — проверка Docker-образа SDK и target/subtarget.
  - scripts/validate-sdk-url.sh — проверка доступности tarball SDK с зеркалами.
  - scripts/setup-opkg-utils.sh — установка opkg-build на host (не через apt в 24.04).
  - scripts/validate_ipk.sh и docs/ci/ipk-version-validation.md — правила версии внутри .ipk (main vs PR).
  - scripts/stage_artifacts.sh — выкладка артефактов под artifacts/<build-name>.
- Требования к артефактам: имя артефакта в CI — с dev+<shortsha>, внутри .ipk версия пакета не переписывается.

Глобальная дорожная карта

Фаза 0 — Разблокировка CI (lint)
- Исправить форматирование shell-скриптов (shfmt -w -s -i 4 -ci -sr .) и убедиться, что «Lint (shfmt)» проходит.
- Запустить «Lint (shellcheck)», «Lint (markdownlint)», «Lint (actionlint)», «Security» проверки локально или в PR.
- Результат: зелёные базовые проверки открывают путь к сборкам пакетов.

Фаза 1 — Нормализация dev-сборок пакета
- Валидация SDK образа и параметров до вызова сборки:
  - В начале job добавить шаги `scripts/validate-sdk-image.sh` и (при tarball-пути) `scripts/validate-sdk-url.sh`.
- Строго задать образ SDK:
  - Пример: CONTAINER=ghcr.io/openwrt/sdk:x86_64-23.05.3.
- Собрать пакет через openwrt/gh-action-sdk@v6 с FEEDNAME=local, FEED_DIR=./, PACKAGES=openwrt-captive-monitor.
- Стадирование артефактов:
  - scripts/stage_artifacts.sh складывает *.ipk, sha256, и логи в artifacts/dev-<branch>.
  - Имя загружаемого артефакта: dev-<branch>-dev+<shortsha> (PKG_VERSION внутри ipk не переписывать!).
- Валидация версии .ipk:
  - В main: scripts/validate-ipk-version.sh main — версия в control должна содержать -dev (см. docs/ci/ipk-version-validation.md).
  - В PR/не-main: scripts/validate-ipk-version.sh pr — суффикса -dev быть не должно.
- Результат: воспроизводимая dev-сборка с версификацией и артефактами в CI.

Фаза 2 — Матрица таргетов, кеши, ускорение
- Ввести матрицу target/subtarget/arch (например: x86_64, mipsel_24kc, arm_cortex-a7 и т.д.).
- Реализовать кеширование:
  - docker pull заранее нужных SDK-образов с retry и ttl.
  - Кеш исходников feed (если применимо) — аккуратно, чтобы не загрязнять workspace.
- Управление параллелизмом и ресурсами:
  - concurrency: cancel-in-progress для PR и чёткие scopes для веток.
  - permissions: least-privilege для GITHUB_TOKEN.
- Результат: одновременные сборки под несколько архитектур с контролем ресурсов и быстрыми pov.

Фаза 3 — Тестирование и интеграции
- Модульные и интеграционные тесты для скриптов:
  - tests/run.sh и мок-скрипты уже есть — расширить покрытие для путей сборки и валидаций.
- Проверка ipk:
  - scripts/verify_package.sh: проверить наличие файлов, контрольных сумм, postinst/prerm, init-скриптов и т.д.
- Smoke-тесты в QEMU/VM (опционально):
  - scripts/run_openwrt_vm.sh — загрузка образа, установка ipk, запуск сервиса, базовые проверки логов.
- Результат: автоматическая регрессия по ключевым сценариям установки/запуска.

Фаза 4 — Подготовка к релизам
- Разделить dev и release пайплайны:
  - main/dev: с -dev в Version поля .ipk; release: без -dev, фиксированная версия из PACKAGE/Makefile.
- Отдельный workflow релиза по тэгу vX.Y.Z:
  - Проверка, что PKG_VERSION совпадает с тэгом; PKG_RELEASE — дата (YYYYMMDD[HHMM]).
  - build матрицы, загрузка артефактов, генерация release notes.
- Подпись артефактов (опционально):
  - cosign/sigstore или detached подписи sha256sum.sig.
- Результат: воспроизводимые релизы с полным аудит-трейлом и верификацией.

Фаза 5 — Документация и поддержка
- Актуализировать docs/packaging.md, docs/PACKAGES.md, добавить quick-start для локальной сборки через SDK.
- Раздел «Диагностика CI»: ссылки на scripts/diagnose-*.sh и «типовые ошибки».
- Гайд по совместимости с BusyBox ash (стиль скриптов: set -eu, pipefail условный, colors.sh, форматирование shfmt).

Готовые элементы и принципы (использовать)
- Валидация SDK-образа и URL уже реализована — включать эти шаги fail-fast в workflow перед openwrt/gh-action-sdk@v6.
- Версионирование .ipk уже стандартизировано — поддерживать правила для main и PR.
- Артефакты складывать под artifacts/<build-name> и загружать actions/upload-artifact@v5 с корректным именем.
- Не использовать apt для opkg-utils на Ubuntu 24.04; вместо этого scripts/setup-opkg-utils.sh и проверить opkg-build -h.

Критерии готовности (DoD)
- Lint и Security проверки зелёные («Lint (shfmt)», "Lint (shellcheck)", "Lint (markdownlint)", "Lint (actionlint)", Trivy, Dependency Review, ShellCheck Security Analysis).
- Dev job собирает пакет под минимум 2 архитектуры, проходит validate-sdk-* и validate-ipk.
- Артефакты корректно именуются и доступны для скачивания; содержат .ipk и sha256.
- Документация обновлена, быстрый сценарий локальной сборки задокументирован.

Команды для разработчиков (локально)
- Форматирование скриптов:
  - shfmt -w -s -i 4 -ci -sr .
- Установка opkg-utils (на Ubuntu 24.04):
  - ./scripts/setup-opkg-utils.sh && opkg-build -h
- Проверка версии .ipk (после сборки):
  - ./scripts/validate-ipk-version.sh pr path/to/*.ipk  # для PR
  - ./scripts/validate-ipk-version.sh main path/to/*.ipk  # для main

Примечания
- Соблюдать минимум прав для GITHUB_TOKEN и корректные concurrency/permissions в workflow (best practices GitHub Actions).
- Сохранять PKG_VERSION внутри файлов пакета неизменным при dev-сборках; маркеры dev — только в имени CI-артефакта и в Version поля control по правилам (main/PR).
