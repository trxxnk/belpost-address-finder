"""
Модуль централизованной конфигурации приложения.
Использует простую реализацию без зависимости от Pydantic.
"""

import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()


class DatabaseConfig:
    """Настройки базы данных"""
    def __init__(self):
        self.user = os.getenv("MYSQL_USER", "root")
        self.password = os.getenv("MYSQL_PASSWORD", "")
        self.host = os.getenv("MYSQL_HOST", "localhost")
        self.port = os.getenv("MYSQL_PORT", "3306")
        self.database = os.getenv("MYSQL_DB", "addr_corr")
        self.echo = os.getenv("MYSQL_ECHO", "false").lower() == "true"
    
    @property
    def connection_string(self) -> str:
        """Строка подключения к базе данных"""
        return f"mysql+mysqlconnector://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class BelpostConfig:
    """Настройки для работы с Белпочтой"""
    def __init__(self):
        self.base_url = os.getenv("BELPOST_BASE_URL", "https://www.belpost.by")
        self.search_endpoint = os.getenv("BELPOST_SEARCH_ENDPOINT", "/Uznatpochtovyykod28indek")
        self.timeout = int(os.getenv("BELPOST_TIMEOUT", "30"))
        self.max_results = int(os.getenv("BELPOST_MAX_RESULTS", "10"))
    
    @property
    def search_url(self) -> str:
        """URL для поиска почтового индекса"""
        return f"{self.base_url}{self.search_endpoint}"


class SeleniumConfig:
    """Настройки для Selenium"""
    def __init__(self):
        self.headless = os.getenv("SELENIUM_HEADLESS", "true").lower() == "true"
        self.max_drivers = int(os.getenv("SELENIUM_MAX_DRIVERS", "3"))
        self.driver_ttl = int(os.getenv("SELENIUM_DRIVER_TTL", "300"))
        self.window_width = int(os.getenv("SELENIUM_WINDOW_WIDTH", "1920"))
        self.window_height = int(os.getenv("SELENIUM_WINDOW_HEIGHT", "1080"))
        
        # Стандартные опции Chrome
        self.chrome_options = [
            "--headless" if self.headless else "",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ]
        # Удаление пустых опций
        self.chrome_options = [opt for opt in self.chrome_options if opt]
        
        # Добавление пользовательских опций из переменной окружения
        custom_options = os.getenv("SELENIUM_CHROME_OPTIONS", "")
        if custom_options:
            self.chrome_options.extend(custom_options.split(","))


class LoggingConfig:
    """Настройки логирования"""
    def __init__(self):
        self.level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.file_path = os.getenv("LOG_FILE_PATH", "logs/app.log")
        self.console = os.getenv("LOG_CONSOLE", "true").lower() == "true"
        self.format = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.max_bytes = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10 MB
        self.backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))
        
        # Проверка уровня логирования
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.level not in allowed_levels:
            print(f"Неверный уровень логирования: {self.level}. Используется INFO.")
            self.level = "INFO"


class UIConfig:
    """Настройки пользовательского интерфейса"""
    def __init__(self):
        self.title = os.getenv("UI_TITLE", "Поиск адресов Белпочта")
        self.window_width = int(os.getenv("UI_WINDOW_WIDTH", "1200"))
        self.window_height = int(os.getenv("UI_WINDOW_HEIGHT", "800"))
        self.theme_mode = os.getenv("UI_THEME_MODE", "LIGHT").upper()
        self.max_results = int(os.getenv("UI_MAX_RESULTS", "9"))
        
        # Проверка режима темы
        allowed_modes = ["LIGHT", "DARK", "SYSTEM"]
        if self.theme_mode not in allowed_modes:
            print(f"Неверный режим темы: {self.theme_mode}. Используется LIGHT.")
            self.theme_mode = "LIGHT"


class AppConfig:
    """Общие настройки приложения"""
    def __init__(self):
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.environment = os.getenv("ENVIRONMENT", "development").lower()
        self.app_name = os.getenv("APP_NAME", "addr_corr")
        
        # Проверка окружения
        allowed_environments = ["development", "testing", "production"]
        if self.environment not in allowed_environments:
            print(f"Неверное окружение: {self.environment}. Используется development.")
            self.environment = "development"
        
        # Вложенные настройки
        self.db = DatabaseConfig()
        self.belpost = BelpostConfig()
        self.selenium = SeleniumConfig()
        self.logging = LoggingConfig()
        self.ui = UIConfig()


# Создание глобального экземпляра настроек
settings = AppConfig()


def get_settings() -> AppConfig:
    """
    Функция для получения настроек приложения.
    
    Returns:
        AppConfig: Настройки приложения
    """
    return settings


def reload_settings() -> AppConfig:
    """
    Перезагрузка настроек из переменных окружения
    
    Returns:
        AppConfig: Обновленные настройки приложения
    """
    global settings
    load_dotenv()
    settings = AppConfig()
    return settings