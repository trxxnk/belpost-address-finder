"""
Модуль для настройки логирования в приложении.
Предоставляет функции для создания и настройки логгеров
с различными уровнями логирования и обработчиками.
"""

import os
import logging
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional, Dict, Any


def setup_logger(
    name: str,
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    max_bytes: int = 10485760,  # 10 MB
    backup_count: int = 5,
    console: bool = True,
    propagate: bool = False,
) -> logging.Logger:
    """
    Настройка логгера с выводом в файл и консоль

    Args:
        name: Имя логгера
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Путь к файлу логов
        log_format: Формат сообщений лога
        max_bytes: Максимальный размер файла лога перед ротацией
        backup_count: Количество сохраняемых файлов лога
        console: Включить вывод в консоль
        propagate: Передавать ли записи родительским логгерам

    Returns:
        logging.Logger: Настроенный логгер
    """
    # Преобразование строкового уровня логирования в константу
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Получение или создание логгера
    logger = logging.getLogger(name)
    
    # Очистка существующих обработчиков, если они есть
    if logger.handlers:
        logger.handlers.clear()
    
    # Установка уровня логирования
    logger.setLevel(level)
    logger.propagate = propagate

    # Создание форматтера
    formatter = logging.Formatter(log_format)

    # Добавление обработчика вывода в консоль
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)

    # Добавление обработчика вывода в файл, если указан путь
    if log_file:
        # Создание директории для логов, если её нет
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # Создание обработчика для файла с ротацией по размеру
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

    return logger


def setup_daily_logger(
    name: str,
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    backup_count: int = 30,
    console: bool = True,
    propagate: bool = False,
) -> logging.Logger:
    """
    Настройка логгера с ежедневной ротацией файлов

    Args:
        name: Имя логгера
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Путь к файлу логов
        log_format: Формат сообщений лога
        backup_count: Количество сохраняемых файлов лога
        console: Включить вывод в консоль
        propagate: Передавать ли записи родительским логгерам

    Returns:
        logging.Logger: Настроенный логгер
    """
    # Преобразование строкового уровня логирования в константу
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Получение или создание логгера
    logger = logging.getLogger(name)
    
    # Очистка существующих обработчиков, если они есть
    if logger.handlers:
        logger.handlers.clear()
    
    # Установка уровня логирования
    logger.setLevel(level)
    logger.propagate = propagate

    # Создание форматтера
    formatter = logging.Formatter(log_format)

    # Добавление обработчика вывода в консоль
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)

    # Добавление обработчика вывода в файл, если указан путь
    if log_file:
        # Создание директории для логов, если её нет
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # Создание обработчика для файла с ежедневной ротацией
        file_handler = TimedRotatingFileHandler(
            log_file,
            when="midnight",
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        file_handler.suffix = "%Y-%m-%d"
        logger.addHandler(file_handler)

    return logger


# Словарь для хранения логгеров
_loggers: Dict[str, logging.Logger] = {}


def get_logger(name: str, **kwargs: Any) -> logging.Logger:
    """
    Получение логгера по имени. Если логгер с таким именем уже существует,
    возвращает его, иначе создает новый.

    Args:
        name: Имя логгера
        **kwargs: Дополнительные параметры для setup_logger

    Returns:
        logging.Logger: Логгер
    """
    if name not in _loggers:
        _loggers[name] = setup_logger(name, **kwargs)
    return _loggers[name]


# Создание основных логгеров приложения
def create_app_loggers(
    app_name: str = "addr_corr",
    log_dir: str = "logs",
    log_level: str = "INFO",
    console: bool = True,
) -> Dict[str, logging.Logger]:
    """
    Создание основных логгеров приложения

    Args:
        app_name: Имя приложения
        log_dir: Директория для файлов логов
        log_level: Уровень логирования
        console: Включить вывод в консоль

    Returns:
        Dict[str, logging.Logger]: Словарь с логгерами
    """
    # Создание директории для логов
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # Создание логгеров для разных компонентов
    loggers = {
        "app": setup_logger(
            f"{app_name}.app",
            log_level=log_level,
            log_file=os.path.join(log_dir, "app.log"),
            console=console,
        ),
        "parser": setup_logger(
            f"{app_name}.parser",
            log_level=log_level,
            log_file=os.path.join(log_dir, "parser.log"),
            console=console,
        ),
        "db": setup_logger(
            f"{app_name}.db",
            log_level=log_level,
            log_file=os.path.join(log_dir, "db.log"),
            console=console,
        ),
        "api": setup_logger(
            f"{app_name}.api",
            log_level=log_level,
            log_file=os.path.join(log_dir, "api.log"),
            console=console,
        ),
        "ui": setup_logger(
            f"{app_name}.ui",
            log_level=log_level,
            log_file=os.path.join(log_dir, "ui.log"),
            console=console,
        ),
    }

    return loggers


# Создание основного логгера приложения
app_logger = get_logger("addr_corr", log_file="logs/app.log")
