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
from config import settings


class EmojiFormatter(logging.Formatter):
    """
    Кастомный форматтер для добавления эмодзи к уровням логирования
    """
    
    # Словарь соответствия уровней логирования и эмодзи
    EMOJI_MAP = {
        'DEBUG': '🐛',
        'INFO': 'ℹ️ ',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🔥'
    }
    
    def __init__(self, fmt=None, datefmt=None, style='%', use_emoji=True):
        """
        Инициализация форматтера
        
        Args:
            fmt: Формат сообщения
            datefmt: Формат даты
            style: Стиль форматирования
            use_emoji: Использовать ли эмодзи (по умолчанию True)
        """
        super().__init__(fmt, datefmt, style)
        self.use_emoji = use_emoji
    
    def format(self, record):
        # Создаем копию записи, чтобы не изменять оригинал
        record_copy = logging.makeLogRecord(record.__dict__)
        
        # Добавляем эмодзи к названию уровня, если включено
        if self.use_emoji:
            emoji = self.EMOJI_MAP.get(record_copy.levelname, '')
            if emoji:
                record_copy.levelname = f"{emoji} {record_copy.levelname}"
        
        # Вызываем стандартное форматирование
        return super().format(record_copy)


def setup_logger(
    name: str,
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    max_bytes: int = 10485760,  # 10 MB
    backup_count: int = 5,
    console: bool = True,
    propagate: bool = False,
    use_emoji: bool = True,
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
        use_emoji: Использовать эмодзи в логах

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
    formatter = EmojiFormatter(log_format, use_emoji=use_emoji)

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
    use_emoji: bool = True,
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
        use_emoji: Использовать эмодзи в логах

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
    formatter = EmojiFormatter(log_format, use_emoji=use_emoji)

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


def get_configured_logger(name: str, log_file_name: Optional[str] = None) -> logging.Logger:
    """
    Получение логгера с настройками из config.py.
    
    Args:
        name: Имя логгера
        log_file_name: Имя файла лога (например, "belpost.log"). 
                      Если не указано, логирование только в консоль.
    
    Returns:
        logging.Logger: Настроенный логгер с параметрами из конфигурации
    """
    log_config = settings.logging
    
    # Определение пути к файлу лога
    log_file = None
    if log_file_name:
        log_dir = os.path.dirname(log_config.log_file)
        if log_dir:
            log_file = os.path.join(log_dir, log_file_name)
    
    return setup_logger(
        name=name,
        log_level=log_config.log_level,
        log_file=log_file,
        log_format=log_config.log_format,
        max_bytes=log_config.max_bytes,
        backup_count=log_config.backup_count,
        console=log_config.console,
        use_emoji=log_config.use_emoji
    )


# Создание основных логгеров приложения с настройками из конфигурации
def create_app_loggers() -> Dict[str, logging.Logger]:
    """
    Создание основных логгеров приложения с настройками из config.py

    Returns:
        Dict[str, logging.Logger]: Словарь с логгерами
    """
    log_config = settings.logging
    app_config = settings
    
    # Получение директории для логов из пути к файлу лога
    log_dir = os.path.dirname(log_config.log_file)
    
    # Создание директории для логов
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # Создание логгеров для разных компонентов
    loggers = {
        "app": setup_logger(
            f"{app_config.app_name}.app",
            log_level=log_config.log_level,
            log_file=os.path.join(log_dir, "app.log") if log_dir else None,
            log_format=log_config.log_format,
            max_bytes=log_config.max_bytes,
            backup_count=log_config.backup_count,
            console=log_config.console,
            use_emoji=log_config.use_emoji,
        ),
        "parser": setup_logger(
            f"{app_config.app_name}.parser",
            log_level=log_config.log_level,
            log_file=os.path.join(log_dir, "parser.log") if log_dir else None,
            log_format=log_config.log_format,
            max_bytes=log_config.max_bytes,
            backup_count=log_config.backup_count,
            console=log_config.console,
            use_emoji=log_config.use_emoji,
        ),
        "belpost": setup_logger(
            f"{app_config.app_name}.belpost",
            log_level=log_config.log_level,
            log_file=os.path.join(log_dir, "belpost.log") if log_dir else None,
            log_format=log_config.log_format,
            max_bytes=log_config.max_bytes,
            backup_count=log_config.backup_count,
            console=log_config.console,
            use_emoji=log_config.use_emoji,
        ),
        "webdriver": setup_logger(
            f"{app_config.app_name}.webdriver",
            log_level=log_config.log_level,
            log_file=os.path.join(log_dir, "webdriver.log") if log_dir else None,
            log_format=log_config.log_format,
            max_bytes=log_config.max_bytes,
            backup_count=log_config.backup_count,
            console=log_config.console,
            use_emoji=log_config.use_emoji,
        ),
        "ui": setup_logger(
            f"{app_config.app_name}.ui",
            log_level=log_config.log_level,
            log_file=os.path.join(log_dir, "ui.log") if log_dir else None,
            log_format=log_config.log_format,
            max_bytes=log_config.max_bytes,
            backup_count=log_config.backup_count,
            console=log_config.console,
            use_emoji=log_config.use_emoji,
        ),
    }

    return loggers


# Создание основного логгера приложения с настройками из конфигурации
def create_main_app_logger() -> logging.Logger:
    """
    Создание основного логгера приложения с настройками из config.py
    
    Returns:
        logging.Logger: Настроенный логгер приложения
    """
    log_config = settings.logging
    
    return setup_logger(
        name="addr_corr",
        log_level=log_config.log_level,
        log_file=log_config.log_file,
        log_format=log_config.log_format,
        max_bytes=log_config.max_bytes,
        backup_count=log_config.backup_count,
        console=log_config.console,
        use_emoji=log_config.use_emoji
    )


# Создание основного логгера приложения
app_logger = create_main_app_logger()
