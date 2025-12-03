# Локальное тестирование GitHub Actions с Act

## Обзор

`act` позволяет запускать GitHub Actions workflow локально в Docker контейнерах. Это полезно для:
- Быстрого тестирования изменений в workflow без push в репозиторий
- Отладки проблем в CI/CD pipeline
- Экономии времени на итерациях разработки

## Установка

`act` уже установлен в проекте через winget:

```powershell
winget install nektos.act
```

## Конфигурация

Файл `.actrc` содержит базовую конфигурацию:

```
# act configuration file
# Use GitHub's ubuntu-latest runner image
-P ubuntu-latest=catthehacker/ubuntu:act-latest
-P ubuntu-24.04=catthehacker/ubuntu:act-24.04
-P ubuntu-22.04=catthehacker/ubuntu:act-22.04
-P ubuntu-20.04=catthehacker/ubuntu:act-20.04

# Use smaller images for faster startup
--container-architecture linux/amd64

# Reuse containers for faster subsequent runs
--reuse

# Verbose output for debugging
--verbose
```

## Основные команды

### Просмотр доступных workflow

```powershell
# Список всех workflow и jobs
act --list

# Список workflow в конкретном файле
act -W .github/workflows/ci.yml --list
```

### Запуск workflow

```powershell
# Dry-run (показать что будет выполнено без реального запуска)
act -W .github/workflows/act-test.yml --job test -n

# Реальный запуск
act -W .github/workflows/act-test.yml --job test

# Запуск с конкретным событием
act push -W .github/workflows/ci.yml

# Запуск конкретного job из matrix
act -W .github/workflows/ci.yml --job lint --matrix linter:yamllint
```

### Полезные опции

```powershell
# Запуск без pull образов (если уже есть локально)
act --pull=false

# Запуск с переменными окружения
act --env-file .env.local

# Запуск с секретами
act --secret-file .secrets

# Интерактивный режим (для отладки)
act --interactive

# Показать только ошибки
act --quiet
```

## Примеры использования

### Тестирование линтеров

```powershell
# Тест всех линтеров
act -W .github/workflows/ci.yml --job lint

# Тест конкретного линтера
act -W .github/workflows/ci.yml --job lint --matrix linter:shellcheck

# Dry-run для проверки конфигурации
act -W .github/workflows/ci.yml --job lint -n
```

### Тестирование сборки пакетов

```powershell
# Простая сборка
act -W .github/workflows/build-simple.yml

# Сборка через SDK (требует больше ресурсов)
act -W .github/workflows/sdk-simple-build.yml --job build
```

### Отладка проблем

```powershell
# Запуск с максимальной детализацией
act -W .github/workflows/ci.yml --job lint --verbose

# Интерактивный режим для входа в контейнер
act -W .github/workflows/ci.yml --job lint --interactive

# Сохранение контейнера после выполнения
act -W .github/workflows/ci.yml --job lint --reuse
```

## Ограничения

### Что работает хорошо

- Простые bash команды и скрипты
- Линтеры (shellcheck, yamllint, markdownlint)
- Базовые Docker операции
- Тестирование логики workflow

### Что может не работать

- Actions, требующие доступ к GitHub API
- Сложные сетевые операции
- Операции, требующие специфичные GitHub secrets
- Workflow с большим количеством внешних зависимостей

### Обходные пути

```powershell
# Для workflow с внешними зависимостями - создать упрощенную версию
# Например, .github/workflows/act-test.yml вместо полного ci.yml

# Для тестирования отдельных шагов - выделить их в отдельный job
# Использовать условия для пропуска проблемных шагов в act
```

## Интеграция с проектом

### Быстрое тестирование изменений

```powershell
# 1. Внести изменения в workflow
# 2. Протестировать локально
act -W .github/workflows/ci.yml --job lint -n

# 3. Если dry-run успешен, запустить реально
act -W .github/workflows/ci.yml --job lint

# 4. Если все работает, сделать commit и push
```

### Отладка failed jobs

```powershell
# 1. Скопировать проблемный workflow локально
# 2. Упростить до минимального воспроизводимого случая
# 3. Запустить с act для отладки
act -W .github/workflows/debug.yml --interactive

# 4. Исправить проблему и протестировать
# 5. Применить исправление к основному workflow
```

## Полезные алиасы

Добавить в PowerShell `$PROFILE`:

```powershell
# Act алиасы
function act-list { act --list }
function act-dry { param($workflow, $job) act -W $workflow --job $job -n }
function act-run { param($workflow, $job) act -W $workflow --job $job }
function act-lint { act -W .github/workflows/ci.yml --job lint }
function act-test { act -W .github/workflows/act-test.yml --job test }
```

## Troubleshooting

### Docker проблемы

```powershell
# Проверить, что Docker запущен
docker info

# Очистить старые контейнеры act
docker container prune -f

# Обновить образы
docker pull catthehacker/ubuntu:act-24.04
```

### Проблемы с сетью

```powershell
# Если есть проблемы с загрузкой actions
act --pull=false  # использовать локальные образы

# Для workflow без внешних зависимостей
act -W .github/workflows/act-test.yml  # использовать простой тестовый workflow
```

### Проблемы с путями

```powershell
# Убедиться, что пути корректны для Windows
${PWD}  # PowerShell
%CD%    # CMD

# Проверить монтирование
act -W .github/workflows/act-test.yml --job test --verbose
```

## Рекомендации

1. **Начинать с простых workflow** - создать тестовый workflow для изучения act
2. **Использовать dry-run** - всегда проверять с `-n` перед реальным запуском
3. **Кэшировать образы** - использовать `--reuse` для ускорения повторных запусков
4. **Упрощать сложные workflow** - выделять проблемные части в отдельные jobs
5. **Документировать проблемы** - записывать известные ограничения для команды

## Интеграция в процесс разработки

```powershell
# Типичный workflow разработки:

# 1. Внести изменения в код или workflow
git checkout -b feature/my-changes

# 2. Протестировать локально с act
act-dry .github/workflows/ci.yml lint
act-run .github/workflows/ci.yml lint

# 3. Если тесты проходят, commit и push
git add .
git commit -m "feat: add new feature"
git push origin feature/my-changes

# 4. Создать PR
gh pr create --title "Feature: My Changes"
```

Это значительно ускоряет цикл разработки и уменьшает количество failed CI runs.