"""
Сервис для взаимодействия с API belpost.by.
Отвечает за запросы к сайту белпочты для получения почтовых индексов.
"""

from typing import List, Dict, Any, Optional, Callable
from utils.webdriver_pool import get_driver_pool
from business.parser import search_postal_code
from config import settings
from logger import get_logger
from exceptions import NetworkException, ParsingException, BelpostServiceException, WebDriverException

# Создание логгера для модуля
logger = get_logger("addr_corr.belpost_service", log_file="logs/belpost.log")


class BelpostService:
    """
    Сервис для взаимодействия с API belpost.by.
    Отвечает за запросы к сайту белпочты для получения почтовых индексов.
    """
    
    def __init__(self):
        """
        Инициализация сервиса Белпочты.
        """
        self.driver_pool = get_driver_pool()
        logger.info("Инициализирован сервис Белпочты")
    
    def search_postal_code(self, search_query: str, progress_callback: Optional[Callable[[str], None]] = None) -> List[List[str]]:
        """
        Поиск почтового индекса на сайте belpost.by
        
        Args:
            search_query: Строка запроса адреса
            progress_callback: Функция обратного вызова для отображения прогресса
            
        Returns:
            List[List[str]]: Список результатов поиска в формате
            [почтовый_код, область, район, город, улица, номера_домов]
            
        Raises:
            BelpostServiceException: При ошибках сервиса Белпочты
            WebDriverException: При ошибках работы с веб-драйвером
        """
        driver = None
        
        try:
            # Уведомление о начале инициализации драйвера
            if progress_callback:
                progress_callback("Инициализация драйвера браузера...")
            
            # Получение драйвера из пула
            driver = self.driver_pool.get_driver()
            if not driver:
                error_msg = "Не удалось получить веб-драйвер из пула"
                logger.error(error_msg)
                if progress_callback:
                    progress_callback(f"Ошибка: {error_msg}")
                raise WebDriverException(error_msg)
            
            # Уведомление о начале поиска
            if progress_callback:
                progress_callback("Поиск адреса на belpost.by...")
            
            # Выполнение поиска на belpost.by
            logger.info(f"Выполняется поиск адреса: {search_query}")
            raw_results = search_postal_code(driver, search_query)
            
            # Логирование результатов
            if raw_results:
                logger.info(f"Найдено {len(raw_results)} результатов для адреса: {search_query}")
            else:
                logger.warning(f"Не найдены результаты для адреса: {search_query}")
            
            return raw_results or []
            
        except NetworkException as e:
            error_msg = f"Ошибка сети при поиске на belpost.by: {str(e)}"
            logger.error(error_msg)
            if progress_callback:
                progress_callback(f"Ошибка: {error_msg}")
            raise BelpostServiceException(error_msg, details=str(e)) from e
            
        except ParsingException as e:
            error_msg = f"Ошибка парсинга при поиске на belpost.by: {str(e)}"
            logger.error(error_msg)
            if progress_callback:
                progress_callback(f"Ошибка: {error_msg}")
            raise BelpostServiceException(error_msg, details=str(e)) from e
            
        except WebDriverException as e:
            error_msg = f"Ошибка веб-драйвера при поиске на belpost.by: {str(e)}"
            logger.error(error_msg)
            if progress_callback:
                progress_callback(f"Ошибка: {error_msg}")
            raise
            
        except Exception as e:
            error_msg = f"Непредвиденная ошибка при поиске на belpost.by: {str(e)}"
            logger.error(error_msg)
            if progress_callback:
                progress_callback(f"Ошибка: {error_msg}")
            raise BelpostServiceException(error_msg) from e
            
        finally:
            # Возвращаем драйвер в пул
            if driver:
                self.driver_pool.release_driver(driver)
    
    def close(self):
        """
        Закрытие ресурсов сервиса.
        Освобождает все используемые ресурсы.
        """
        logger.info("Закрытие сервиса Белпочты")
        # Больше не нужно закрывать драйвер напрямую, 
        # так как этим занимается пул драйверов