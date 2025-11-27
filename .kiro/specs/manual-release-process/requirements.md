# Requirements Document

## Introduction

Текущий процесс релиза автоматически создает теги и релизы при каждом коммите в main ветку через workflow `auto-version-tag.yml`. Это приводит к избыточному количеству релизов и усложняет контроль над версионированием. Необходимо перейти на ручной процесс выпуска релизов, где разработчик явно инициирует создание релиза.

## Glossary

- **Auto-version workflow**: Автоматический workflow, который создает теги версий при каждом push в main
- **Manual release**: Ручной процесс создания релиза, инициируемый разработчиком
- **Release workflow**: Workflow для сборки и публикации релиза
- **Version tag**: Git тег в формате vYYYY.M.D.N
- **Simple Release Build**: Workflow для сборки универсального пакета без SDK

## Requirements

### Requirement 1

**User Story:** Как разработчик, я хочу вручную инициировать создание релиза, чтобы контролировать когда и какие изменения публикуются.

#### Acceptance Criteria

1. WHEN разработчик запускает release workflow вручную THEN система SHALL создать новый тег версии на основе текущей даты
2. WHEN разработчик запускает release workflow THEN система SHALL собрать пакет и опубликовать релиз на GitHub
3. WHEN разработчик коммитит в main THEN система SHALL NOT создавать автоматический релиз
4. WHEN разработчик указывает кастомную версию THEN система SHALL использовать указанную версию вместо автоматической

### Requirement 2

**User Story:** Как разработчик, я хочу чтобы VERSION файл и Makefile обновлялись автоматически при создании релиза, чтобы не делать это вручную.

#### Acceptance Criteria

1. WHEN release workflow запускается THEN система SHALL обновить VERSION файл с новой версией
2. WHEN VERSION файл обновляется THEN система SHALL обновить PKG_VERSION в Makefile
3. WHEN версия обновляется THEN система SHALL создать коммит с изменениями
4. WHEN коммит создается THEN система SHALL создать тег на этом коммите

### Requirement 3

**User Story:** Как разработчик, я хочу отключить автоматическое создание тегов, чтобы избежать избыточных релизов.

#### Acceptance Criteria

1. WHEN код коммитится в main THEN система SHALL NOT запускать auto-version-tag workflow
2. WHEN auto-version workflow отключен THEN существующие релизы SHALL остаться доступными
3. WHEN auto-version workflow отключен THEN ручной release workflow SHALL продолжать работать

### Requirement 4

**User Story:** Как разработчик, я хочу использовать простую сборку без SDK для универсального пакета, чтобы избежать проблем с toolchain.

#### Acceptance Criteria

1. WHEN release workflow собирает пакет THEN система SHALL использовать Simple Release Build workflow
2. WHEN пакет собирается THEN система SHALL NOT использовать OpenWrt SDK
3. WHEN пакет собирается THEN система SHALL создать .ipk файл с arch=all
4. WHEN сборка завершается THEN система SHALL прикрепить пакет к GitHub релизу

### Requirement 5

**User Story:** Как разработчик, я хочу иметь возможность создать релиз с кастомным сообщением, чтобы описать изменения.

#### Acceptance Criteria

1. WHEN разработчик запускает release workflow THEN система SHALL позволить указать release notes
2. WHEN release notes указаны THEN система SHALL использовать их в описании релиза
3. WHEN release notes не указаны THEN система SHALL использовать автоматическое описание
