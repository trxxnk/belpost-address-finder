"""
Модуль для управления пулом веб-драйверов Selenium.
Реализует паттерн Singleton для эффективного использования ресурсов
и предотвращения создания избыточных экземпляров драйвера.
"""

import time
import threading
import atexit
from typing import List, Dict, Optional, Any
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from config import settings
from logger import get_configured_logger
from exceptions import WebDriverException

# Создание логгера для модуля
logger = get_configured_logger("core.utils.webdriver_pool", "webdriver.log")


class WebDriverPool:
    """
    Пул веб-драйверов Selenium.
    
    Реализует паттерн Singleton для обеспечения единственного экземпляра
    пула драйверов в приложении. Управляет созданием, использованием и
    освобождением драйверов.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """
        Реализация паттерна Singleton.
        
        Returns:
            WebDriverPool: Единственный экземпляр класса
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(WebDriverPool, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, max_drivers: int = None, ttl: int = None):
        """
        Инициализация пула драйверов.
        
        Args:
            max_drivers: Максимальное количество драйверов в пуле
            ttl: Время жизни неиспользуемого драйвера в секундах
        """
        if self._initialized:
            return
            
        # Загрузка настроек из конфигурации
        self.max_drivers = max_drivers or settings.selenium.max_drivers
        self.ttl = ttl or settings.selenium.driver_ttl
        
        self.drivers: List[webdriver.Chrome] = []
        self.in_use: Dict[webdriver.Chrome, float] = {}
        self._lock = threading.Lock()
        self._initialized = True
        
        # Запуск фонового потока для очистки неиспользуемых драйверов
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        
        # Регистрация функции очистки при завершении программы
        atexit.register(self.close_all)
        
        logger.info(f"Инициализирован пул веб-драйверов (max_drivers={self.max_drivers}, ttl={self.ttl})")
    
    def _create_driver(self) -> webdriver.Chrome:
        """
        Создание нового экземпляра драйвера.
        
        Returns:
            webdriver.Chrome: Новый экземпляр драйвера Chrome
        
        Raises:
            WebDriverException: При ошибке создания драйвера
        """
        try:
            chrome_options = Options()
            
            # Добавление опций из конфигурации
            for option in settings.selenium.chrome_options:
                chrome_options.add_argument(option)
            
            # Настройка размеров окна
            chrome_options.add_argument(
                f"--window-size={settings.selenium.window_width},{settings.selenium.window_height}"
            )
            
            # Установка и настройка драйвера
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Установка таймаутов
            driver.set_page_load_timeout(settings.belpost.timeout)
            driver.implicitly_wait(10)
            
            logger.debug("Создан новый экземпляр веб-драйвера")
            return driver
            
        except Exception as e:
            error_msg = f"Ошибка при создании веб-драйвера: {str(e)}"
            logger.error(error_msg)
            raise WebDriverException(error_msg)
    
    def get_driver(self) -> Optional[webdriver.Chrome]:
        """
        Получение драйвера из пула.
        
        Returns:
            webdriver.Chrome: Экземпляр драйвера из пула или новый
            None: Если достигнут лимит драйверов и все заняты
        
        Raises:
            WebDriverException: При ошибке получения драйвера
        """
        with self._lock:
            try:
                # Проверяем наличие свободных драйверов
                for driver in self.drivers:
                    if driver not in self.in_use:
                        self.in_use[driver] = time.time()
                        logger.debug("Получен существующий драйвер из пула")
                        return driver
                        
                # Если нет свободных и не достигнут лимит, создаем новый
                if len(self.drivers) < self.max_drivers:
                    driver = self._create_driver()
                    self.drivers.append(driver)
                    self.in_use[driver] = time.time()
                    logger.debug(f"Создан новый драйвер (всего: {len(self.drivers)})")
                    return driver
                    
                # Если достигнут лимит, логируем и возвращаем None
                logger.warning(f"Достигнут лимит драйверов ({self.max_drivers}). Нет свободных драйверов.")
                return None
                
            except Exception as e:
                error_msg = f"Ошибка при получении драйвера: {str(e)}"
                logger.error(error_msg)
                raise WebDriverException(error_msg)
    
    def release_driver(self, driver: webdriver.Chrome) -> None:
        """
        Возврат драйвера в пул.
        
        Args:
            driver: Драйвер для возврата в пул
        """
        with self._lock:
            if driver in self.in_use:
                del self.in_use[driver]
                logger.debug("Драйвер возвращен в пул")
            else:
                logger.warning("Попытка освободить драйвер, который не числится используемым")
    
    def _cleanup_loop(self) -> None:
        """
        Фоновый поток для периодической очистки неиспользуемых драйверов.
        """
        while True:
            time.sleep(60)  # Проверка каждую минуту
            self.cleanup()
    
    def cleanup(self) -> None:
        """
        Очистка неиспользуемых драйверов, превысивших TTL.
        """
        with self._lock:
            current_time = time.time()
            to_remove = []
            
            # Собираем список драйверов для удаления
            for driver in self.drivers:
                if driver not in self.in_use and current_time - self.in_use.get(driver, 0) > self.ttl:
                    to_remove.append(driver)
            
            # Удаляем драйверы
            for driver in to_remove:
                try:
                    self.drivers.remove(driver)
                    driver.quit()
                    logger.debug(f"Удален неиспользуемый драйвер (время простоя > {self.ttl}с)")
                except Exception as e:
                    logger.error(f"Ошибка при закрытии драйвера: {str(e)}")
            
            if to_remove:
                logger.info(f"Очищено {len(to_remove)} неиспользуемых драйверов. Осталось: {len(self.drivers)}")
    
    def close_all(self) -> None:
        """
        Закрытие всех драйверов.
        Вызывается при завершении работы приложения.
        """
        with self._lock:
            logger.info(f"Закрытие всех драйверов ({len(self.drivers)})")
            for driver in self.drivers:
                try:
                    driver.quit()
                except Exception as e:
                    logger.error(f"Ошибка при закрытии драйвера: {str(e)}")
            self.drivers = []
            self.in_use = {}


# Создание глобального экземпляра пула драйверов
driver_pool = WebDriverPool()


def get_driver_pool() -> WebDriverPool:
    """
    Получение экземпляра пула драйверов.
    
    Returns:
        WebDriverPool: Экземпляр пула драйверов
    """
    return driver_pool
