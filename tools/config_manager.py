#!/usr/bin/env python3
"""
Менеджер конфигурации для автоматизации captive порталов.

Этот модуль предоставляет класс ConfigManager для загрузки, валидации
и управления конфигурациями различных типов captive порталов.

Автор: OpenWrt Captive Monitor Project
Версия: 1.0.0
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import jsonschema
from jsonschema import validate, ValidationError
import logging
from datetime import datetime


class ConfigManager:
    """
    Менеджер конфигурации для captive порталов.

    Обеспечивает загрузку, валидацию и управление конфигурациями
    различных типов captive порталов.
    """

    def __init__(self, config_dir: Optional[str] = None, schema_path: Optional[str] = None):
        """
        Инициализация менеджера конфигурации.

        Args:
            config_dir: Директория с конфигурационными файлами
            schema_path: Путь к JSON схеме валидации
        """
        self.logger = logging.getLogger(__name__)

        # Определяем пути
        self.tools_dir = Path(__file__).parent
        self.config_dir = Path(config_dir) if config_dir else self.tools_dir / "configs"
        self.schema_path = Path(schema_path) if schema_path else self.tools_dir / "portal_config_schema.json"

        # Создаем директорию конфигураций если не существует
        self.config_dir.mkdir(exist_ok=True)

        # Загружаем схему валидации
        self.schema = self._load_schema()

        # Кэш загруженных конфигураций
        self._config_cache: Dict[str, Dict[str, Any]] = {}

    def _load_schema(self) -> Dict[str, Any]:
        """Загружает JSON схему для валидации конфигураций."""
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            self.logger.debug(f"Загружена схема валидации: {self.schema_path}")
            return schema
        except FileNotFoundError:
            self.logger.error(f"Файл схемы не найден: {self.schema_path}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Ошибка парсинга схемы: {e}")
            raise

    def load_config(self, portal_type: str, force_reload: bool = False) -> Dict[str, Any]:
        """
        Загружает конфигурацию для указанного типа портала.

        Args:
            portal_type: Тип портала (например: 'conn4.com', 'mikrotik')
            force_reload: Принудительная перезагрузка из файла

        Returns:
            Словарь с конфигурацией портала

        Raises:
            FileNotFoundError: Если файл конфигурации не найден
            ValidationError: Если конфигурация не прошла валидацию
        """
        # Проверяем кэш
        if not force_reload and portal_type in self._config_cache:
            self.logger.debug(f"Конфигурация {portal_type} загружена из кэша")
            return self._config_cache[portal_type]

        # Ищем файл конфигурации
        config_file = self._find_config_file(portal_type)
        if not config_file:
            raise FileNotFoundError(f"Конфигурация для портала '{portal_type}' не найдена")

        # Загружаем конфигурацию
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Валидируем конфигурацию
            self.validate_config(config)

            # Сохраняем в кэш
            self._config_cache[portal_type] = config

            self.logger.info(f"Загружена конфигурация для портала: {portal_type}")
            return config

        except json.JSONDecodeError as e:
            self.logger.error(f"Ошибка парсинга конфигурации {config_file}: {e}")
            raise

    def _find_config_file(self, portal_type: str) -> Optional[Path]:
        """
        Ищет файл конфигурации для указанного типа портала.

        Проверяет следующие варианты имен файлов:
        - {portal_type}.json
        - {portal_type}_config.json
        - portal_{portal_type}.json
        """
        possible_names = [
            f"{portal_type}.json",
            f"{portal_type}_config.json",
            f"portal_{portal_type}.json"
        ]

        for name in possible_names:
            config_file = self.config_dir / name
            if config_file.exists():
                return config_file

        return None

    def validate_config(self, config: Dict[str, Any]) -> None:
        """
        Валидирует конфигурацию против JSON схемы.

        Args:
            config: Конфигурация для валидации

        Raises:
            ValidationError: Если конфигурация не соответствует схеме
        """
        try:
            validate(instance=config, schema=self.schema)
            self.logger.debug("Конфигурация прошла валидацию")
        except ValidationError as e:
            self.logger.error(f"Ошибка валидации конфигурации: {e.message}")
            raise

    def list_available_configs(self) -> List[str]:
        """
        Возвращает список доступных типов порталов.

        Returns:
            Список строк с типами порталов
        """
        configs = []

        for config_file in self.config_dir.glob("*.json"):
            # Извлекаем тип портала из имени файла
            name = config_file.stem

            # Убираем суффиксы _config и префиксы portal_
            if name.endswith("_config"):
                name = name[:-7]
            elif name.startswith("portal_"):
                name = name[7:]

            configs.append(name)

        return sorted(configs)

    def create_config_template(self, portal_type: str, output_file: Optional[str] = None) -> str:
        """
        Создает шаблон конфигурации для нового типа портала.

        Args:
            portal_type: Тип портала
            output_file: Путь к выходному файлу (опционально)

        Returns:
            Путь к созданному файлу шаблона
        """
        template = {
            "portal_type": portal_type,
            "auth_method": "form_submission",
            "detection": {
                "url_patterns": [f"*{portal_type}*"],
                "title_patterns": [],
                "content_patterns": []
            },
            "form_config": {
                "action": "/login",
                "method": "POST",
                "required_fields": {
                    "username": "Имя пользователя",
                    "password": "Пароль"
                },
                "optional_fields": {},
                "hidden_fields": {}
            },
            "success_indicators": [
                {
                    "type": "internet_check",
                    "value": "http://www.google.com/generate_204",
                    "timeout": 10
                }
            ],
            "retry_config": {
                "max_attempts": 3,
                "delay_seconds": 5,
                "backoff_multiplier": 1.5
            },
            "timeouts": {
                "page_load": 30,
                "auth_request": 15,
                "verification": 10
            },
            "metadata": {
                "name": f"Шаблон для {portal_type}",
                "description": f"Конфигурация для captive портала {portal_type}",
                "version": "1.0.0",
                "author": "OpenWrt Captive Monitor",
                "created": datetime.now().isoformat(),
                "tested_versions": []
            }
        }

        # Определяем путь к выходному файлу
        if not output_file:
            output_file = self.config_dir / f"{portal_type}_template.json"
        else:
            output_file = Path(output_file)

        # Сохраняем шаблон
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Создан шаблон конфигурации: {output_file}")
        return str(output_file)

    def merge_config_overrides(self, config: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
        """
        Объединяет конфигурацию с переопределениями.

        Args:
            config: Базовая конфигурация
            overrides: Переопределения параметров

        Returns:
            Объединенная конфигурация
        """
        merged = config.copy()

        def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
            """Рекурсивное объединение словарей."""
            result = base.copy()

            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value

            return result

        merged = deep_merge(merged, overrides)

        # Валидируем результат
        self.validate_config(merged)

        self.logger.debug("Конфигурация объединена с переопределениями")
        return merged

    def get_config_info(self, portal_type: str) -> Dict[str, Any]:
        """
        Возвращает информацию о конфигурации портала.

        Args:
            portal_type: Тип портала

        Returns:
            Словарь с метаданными конфигурации
        """
        config = self.load_config(portal_type)

        info = {
            "portal_type": config.get("portal_type", portal_type),
            "auth_method": config.get("auth_method", "unknown"),
            "has_javascript": "javascript_config" in config,
            "required_fields": list(config.get("form_config", {}).get("required_fields", {}).keys()),
            "success_indicators_count": len(config.get("success_indicators", [])),
            "metadata": config.get("metadata", {})
        }

        return info


def main():
    """Основная функция для CLI использования."""
    import argparse

    parser = argparse.ArgumentParser(description="Менеджер конфигурации captive порталов")
    parser.add_argument("--config-dir", help="Директория с конфигурациями")
    parser.add_argument("--schema", help="Путь к JSON схеме")
    parser.add_argument("--verbose", "-v", action="store_true", help="Подробный вывод")

    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")

    # Команда list
    list_parser = subparsers.add_parser("list", help="Список доступных конфигураций")

    # Команда load
    load_parser = subparsers.add_parser("load", help="Загрузить конфигурацию")
    load_parser.add_argument("portal_type", help="Тип портала")
    load_parser.add_argument("--pretty", action="store_true", help="Красивый вывод JSON")

    # Команда validate
    validate_parser = subparsers.add_parser("validate", help="Валидировать конфигурацию")
    validate_parser.add_argument("config_file", help="Путь к файлу конфигурации")

    # Команда template
    template_parser = subparsers.add_parser("template", help="Создать шаблон конфигурации")
    template_parser.add_argument("portal_type", help="Тип портала")
    template_parser.add_argument("--output", "-o", help="Выходной файл")

    # Команда info
    info_parser = subparsers.add_parser("info", help="Информация о конфигурации")
    info_parser.add_argument("portal_type", help="Тип портала")

    args = parser.parse_args()

    # Настройка логирования
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')

    try:
        # Создаем менеджер конфигурации
        manager = ConfigManager(config_dir=args.config_dir, schema_path=args.schema)

        if args.command == "list":
            configs = manager.list_available_configs()
            if configs:
                print("Доступные конфигурации:")
                for config in configs:
                    print(f"  - {config}")
            else:
                print("Конфигурации не найдены")

        elif args.command == "load":
            config = manager.load_config(args.portal_type)
            if args.pretty:
                print(json.dumps(config, indent=2, ensure_ascii=False))
            else:
                print(json.dumps(config, ensure_ascii=False))

        elif args.command == "validate":
            with open(args.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            manager.validate_config(config)
            print(f"✅ Конфигурация {args.config_file} валидна")

        elif args.command == "template":
            output_file = manager.create_config_template(args.portal_type, args.output)
            print(f"✅ Создан шаблон: {output_file}")

        elif args.command == "info":
            info = manager.get_config_info(args.portal_type)
            print(f"Информация о портале: {args.portal_type}")
            print(f"  Метод авторизации: {info['auth_method']}")
            print(f"  JavaScript логика: {'Да' if info['has_javascript'] else 'Нет'}")
            print(f"  Обязательные поля: {', '.join(info['required_fields'])}")
            print(f"  Индикаторы успеха: {info['success_indicators_count']}")

            metadata = info.get('metadata', {})
            if metadata:
                print(f"  Название: {metadata.get('name', 'Не указано')}")
                print(f"  Версия: {metadata.get('version', 'Не указано')}")

        else:
            parser.print_help()

    except Exception as e:
        print(f"❌ Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
