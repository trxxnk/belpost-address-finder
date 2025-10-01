"""
Модуль для парсинга данных с сайта Белпочты.
Предоставляет функции для поиска почтовых индексов по адресам.
"""

import csv
import time
import os
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException as SeleniumWebDriverException

from utils.webdriver_pool import get_driver_pool
from config import settings
from logger import get_logger
from exceptions import ParsingException, NetworkException, WebDriverException

# Создание логгера для модуля
logger = get_logger("addr_corr.parser", log_file="logs/parser.log")


def search_postal_code(driver: webdriver.Chrome, address: str) -> List[List[str]]:
    """
    Поиск почтового индекса на сайте Белпочты
    
    Args:
        driver: Экземпляр Selenium WebDriver
        address: Адрес для поиска
    
    Returns:
        List[List[str]]: Список строк с информацией о почтовых индексах
        
    Raises:
        NetworkException: При ошибках сети
        ParsingException: При ошибках парсинга
    """
    try:
        # Кодирование адреса для URL
        encoded_address = quote(address)
        url = f"{settings.belpost.search_url}?search={encoded_address}"
        
        logger.info(f"Поиск индекса для адреса: {address}")
        logger.debug(f"Открываем URL: {url}")
        
        try:
            driver.get(url)
        except SeleniumWebDriverException as e:
            raise NetworkException(f"Ошибка при открытии URL", url=url) from e
        
        # Ожидание загрузки страницы и появления результатов поиска
        wait = WebDriverWait(driver, settings.belpost.timeout)
        
        # Ожидание появления таблицы
        logger.debug("Ожидание результатов поиска...")
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        except TimeoutException:
            logger.warning(f"Таблица не найдена в течение времени ожидания ({settings.belpost.timeout}с)")
            return []
        
        # Сохранение HTML для отладки
        if settings.debug:
            debug_dir = 'debug'
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
                
            debug_file = os.path.join(debug_dir, 'debug_page_source.html')
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            logger.debug(f"Сохранен исходный код страницы в {debug_file}")
        
        # Поиск всех таблиц на странице
        tables = driver.find_elements(By.TAG_NAME, "table")
        
        if not tables:
            logger.warning(f"Таблицы не найдены для адреса: {address}")
            return []
        
        # Используем первую таблицу, если она одна
        if len(tables) == 1:
            result_table = tables[0]
        else:
            # Поиск таблицы с данными о почтовых индексах
            result_table = None
            for table in tables:
                # Получение заголовков
                try:
                    headers = table.find_elements(By.TAG_NAME, "th")
                    if headers:
                        header_texts = [header.text.strip().lower() for header in headers]
                        
                        # Проверка, является ли это нужной таблицей
                        if any('индекс' in header.lower() or 'код' in header.lower() for header in header_texts):
                            result_table = table
                            break
                except NoSuchElementException:
                    continue
        
        if not result_table:
            logger.warning("Не удалось идентифицировать нужную таблицу")
            return []
        
        # Получение всех строк из таблицы
        all_rows = result_table.find_elements(By.TAG_NAME, "tr")
        
        # Получение строк данных (пропуск заголовка)
        rows = all_rows[1:] if len(all_rows) > 1 else []
        
        # Ограничение до максимального количества строк из настроек
        max_results = settings.belpost.max_results
        rows = rows[:max_results]
        
        result = []
        for row in rows:
            try:
                cols = row.find_elements(By.TAG_NAME, "td")
                if cols:
                    # Извлечение текста из каждой колонки
                    row_data = [col.text.strip() for col in cols]
                    result.append(row_data)
            except NoSuchElementException:
                continue
        
        logger.info(f"Найдено {len(result)} результатов для адреса: {address}")
        return result
    
    except NetworkException as e:
        logger.error(f"Ошибка сети при поиске индекса: {str(e)}")
        raise
    except Exception as e:
        error_msg = f"Ошибка при парсинге адреса '{address}': {str(e)}"
        logger.error(error_msg)
        raise ParsingException(error_msg, source="belpost.by") from e


def search_multiple_addresses(addresses: List[str]) -> Dict[str, List[List[str]]]:
    """
    Поиск почтовых индексов для нескольких адресов
    
    Args:
        addresses: Список адресов для поиска
    
    Returns:
        Dict[str, List[List[str]]]: Словарь с результатами поиска для каждого адреса
        
    Raises:
        WebDriverException: При ошибках работы с веб-драйвером
    """
    results = {}
    driver = None
    driver_pool = get_driver_pool()
    
    try:
        # Получаем драйвер из пула
        driver = driver_pool.get_driver()
        if not driver:
            raise WebDriverException("Не удалось получить веб-драйвер из пула")
        
        logger.info(f"Начало поиска индексов для {len(addresses)} адресов")
        
        for address in addresses:
            try:
                address_results = search_postal_code(driver, address)
                results[address] = address_results
                
                # Небольшая пауза между запросами для снижения нагрузки на сервер
                time.sleep(1)
            except (NetworkException, ParsingException) as e:
                logger.warning(f"Ошибка при обработке адреса '{address}': {str(e)}")
                results[address] = []
    
    except WebDriverException as e:
        logger.error(f"Ошибка веб-драйвера: {str(e)}")
        raise
    except Exception as e:
        error_msg = f"Непредвиденная ошибка при обработке адресов: {str(e)}"
        logger.error(error_msg)
        raise ParsingException(error_msg) from e
    
    finally:
        # Возвращаем драйвер в пул
        if driver:
            driver_pool.release_driver(driver)
    
    return results


def save_to_csv(data: List[List[str]], filename: str = 'postal_codes.csv') -> bool:
    """
    Сохранение данных в CSV файл
    
    Args:
        data: Список строк для сохранения
        filename: Имя выходного файла
        
    Returns:
        bool: True, если данные успешно сохранены, иначе False
    """
    if not data:
        logger.warning("Нет данных для сохранения в CSV")
        return False
    
    try:
        # Создание директории для файла, если её нет
        output_dir = os.path.dirname(filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Запись заголовка на основе структуры данных
            if data and len(data) > 0:
                if len(data[0]) == 6:
                    writer.writerow(['Почтовый код', 'Область', 'Район', 'Город', 'Улица', 'Номер дома'])
                else:
                    writer.writerow([f'Колонка_{i+1}' for i in range(len(data[0]))])
            
            # Запись строк данных
            for row in data:
                writer.writerow(row)
        
        logger.info(f"Данные успешно сохранены в {filename}")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при сохранении в CSV: {str(e)}")
        return False


def save_multiple_results_to_csv(results: Dict[str, List[List[str]]], filename: str = 'all_postal_codes.csv') -> bool:
    """
    Сохранение результатов для нескольких адресов в CSV
    
    Args:
        results: Словарь с результатами поиска для каждого адреса
        filename: Имя выходного файла
        
    Returns:
        bool: True, если данные успешно сохранены, иначе False
    """
    if not results:
        logger.warning("Нет результатов для сохранения в CSV")
        return False
    
    try:
        # Создание директории для файла, если её нет
        output_dir = os.path.dirname(filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Запись заголовка
            writer.writerow(['Исходный адрес', 'Почтовый код', 'Область', 'Район', 'Город', 'Улица', 'Номер дома'])
            
            # Запись данных для каждого адреса
            for address, address_results in results.items():
                if not address_results:
                    # Если результатов нет, записываем строку с исходным адресом и пустыми полями
                    writer.writerow([address] + [''] * 6)
                else:
                    # Записываем все найденные результаты для адреса
                    for row in address_results:
                        writer.writerow([address] + row)
        
        logger.info(f"Все результаты успешно сохранены в {filename}")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при сохранении результатов: {str(e)}")
        return False


def get_postal_code(address: str) -> Optional[str]:
    """
    Получение почтового индекса для адреса
    
    Args:
        address: Адрес для поиска
        
    Returns:
        Optional[str]: Почтовый индекс или None, если не найден
        
    Raises:
        WebDriverException: При ошибках работы с веб-драйвером
        NetworkException: При ошибках сети
        ParsingException: При ошибках парсинга
    """
    driver = None
    driver_pool = get_driver_pool()
    
    try:
        # Получаем драйвер из пула
        driver = driver_pool.get_driver()
        if not driver:
            raise WebDriverException("Не удалось получить веб-драйвер из пула")
        
        results = search_postal_code(driver, address)
        if results:
            return results[0][0]  # Возвращаем первый найденный индекс
        else:
            return None
    
    finally:
        # Возвращаем драйвер в пул
        if driver:
            driver_pool.release_driver(driver)


def main():
    """
    Основная функция для демонстрации работы модуля
    """
    try:
        # Примеры адресов
        addresses = [
            "город Минск улица Октябрьская 10/2",
            "город Минск проспект Независимости 4",
            "город Витебск улица Ленина 26/2"
        ]
        
        logger.info("Запуск демонстрационного поиска индексов")
        
        # Поиск индексов для нескольких адресов
        results = search_multiple_addresses(addresses)
        
        # Сохранение всех результатов
        output_file = 'output_example/postal_codes.csv'
        save_multiple_results_to_csv(results, filename=output_file)
        
        # Вывод результатов
        for address, address_results in results.items():
            if address_results:
                logger.info(f"Результаты для адреса '{address}': найдено {len(address_results)} результатов")
                for row in address_results:
                    logger.info(f"Индекс: {row[0]}, Адрес: {row[3]}, {row[4]}, {row[5]}")
            else:
                logger.warning(f"Для адреса '{address}' результаты не найдены")
    
    except Exception as e:
        logger.error(f"Ошибка в функции main: {str(e)}")


if __name__ == "__main__":
    main()