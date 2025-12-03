# Requirements Document

## Introduction

Данная спецификация описывает оптимизацию Docker образов OpenWrt SDK для работы на Windows с Docker Desktop. Текущие образы работают, но имеют проблемы с размером (3.55GB вместо целевых 2GB) и недостаточно документированы для пользователей Windows.

## Glossary

- **Docker Desktop**: Приложение Docker для Windows, использующее WSL2 backend для запуска Linux контейнеров
- **OpenWrt SDK**: Software Development Kit для сборки пакетов OpenWrt
- **WSL2**: Windows Subsystem for Linux версии 2
- **Multi-stage build**: Техника Docker для создания минимальных образов путем использования нескольких стадий сборки
- **Image layer**: Слой файловой системы Docker образа
- **Build context**: Набор файлов, доступных Docker при сборке образа

## Requirements

### Requirement 1

**User Story:** Как разработчик на Windows, я хочу собирать Docker образы OpenWrt SDK локально, чтобы тестировать изменения перед отправкой в CI/CD.

#### Acceptance Criteria

1. WHEN a user runs the build script on Windows THEN the system SHALL successfully build the Docker image using Docker Desktop
2. WHEN the build completes THEN the system SHALL display clear progress information and final image size
3. WHEN the build fails THEN the system SHALL provide diagnostic information about the failure
4. WHEN a user mounts the workspace directory THEN the system SHALL correctly access files from Windows filesystem

### Requirement 2

**User Story:** Как системный администратор, я хочу минимизировать размер Docker образов, чтобы сократить время загрузки и использование дискового пространства.

#### Acceptance Criteria

1. WHEN the Docker image is built THEN the system SHALL produce an image smaller than 2GB
2. WHEN cleaning up build artifacts THEN the system SHALL remove all temporary files and package manager caches
3. WHEN extracting the SDK THEN the system SHALL exclude unnecessary files from the final image
4. WHEN installing dependencies THEN the system SHALL use minimal package sets without recommended packages

### Requirement 3

**User Story:** Как разработчик, я хочу точно измерять размер Docker образов, чтобы контролировать их соответствие требованиям.

#### Acceptance Criteria

1. WHEN the build script checks image size THEN the system SHALL correctly parse the size in bytes
2. WHEN the image exceeds 2GB limit THEN the system SHALL report a warning with actual size
3. WHEN the image is within limits THEN the system SHALL confirm compliance
4. WHEN displaying size information THEN the system SHALL show both human-readable and byte values

### Requirement 4

**User Story:** Как пользователь Windows, я хочу иметь документацию по использованию Docker образов на Windows, чтобы быстро начать работу.

#### Acceptance Criteria

1. WHEN a user reads the documentation THEN the system SHALL provide Windows-specific setup instructions
2. WHEN a user encounters path issues THEN the documentation SHALL explain Windows path conversion for volume mounts
3. WHEN a user needs to run bash scripts THEN the documentation SHALL explain how to use WSL or Docker exec
4. WHEN a user wants to build locally THEN the documentation SHALL provide PowerShell command examples

### Requirement 5

**User Story:** Как разработчик, я хочу оптимизировать слои Docker образа, чтобы максимально использовать кэширование и минимизировать размер.

#### Acceptance Criteria

1. WHEN building the image THEN the system SHALL combine related RUN commands to reduce layer count
2. WHEN installing packages THEN the system SHALL clean up caches in the same layer
3. WHEN copying files THEN the system SHALL use .dockerignore to exclude unnecessary files
4. WHEN the SDK is extracted THEN the system SHALL remove archive files in the same layer

### Requirement 6

**User Story:** Как CI/CD инженер, я хочу валидировать содержимое Docker образов, чтобы убедиться в наличии всех необходимых компонентов.

#### Acceptance Criteria

1. WHEN the image is built THEN the system SHALL verify presence of the SDK directory
2. WHEN testing the image THEN the system SHALL check availability of build tools
3. WHEN validating the image THEN the system SHALL confirm correct permissions for the builder user
4. WHEN the validation fails THEN the system SHALL report specific missing components
