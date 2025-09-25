import csv
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import quote


def setup_driver():
    """
    Настройка и конфигурация Chrome WebDriver
    
    Returns:
        WebDriver: Настроенный экземпляр Chrome WebDriver
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Запуск в фоновом режиме
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Настройка Chrome WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver


def search_postal_code(driver: webdriver.Chrome, address: str):
    """
    Поиск почтового индекса на сайте Белпочты
    
    Args:
        driver (WebDriver): Экземпляр Selenium WebDriver
        address (str): Адрес для поиска
    
    Returns:
        list: Список строк с информацией о почтовых индексах
    """
    try:
        # Кодирование адреса для URL
        encoded_address = quote(address)
        url = f"https://www.belpost.by/Uznatpochtovyykod28indek?search={encoded_address}"
        
        print(f"[DEBUG] Открываем URL: {url}")
        driver.get(url)
        
        # Ожидание загрузки страницы и появления результатов поиска
        wait = WebDriverWait(driver, 15)
        
        # Ожидание появления таблицы
        print("[DEBUG] Ожидание результатов поиска...")
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        except:
            print("[DEBUG] Таблица не найдена в течение времени ожидания")
            return []
        
        # Сохранение HTML для отладки
        if not os.path.exists('debug'):
            os.makedirs('debug')
            
        with open('debug/debug_page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        
        # Поиск всех таблиц на странице
        tables = driver.find_elements(By.TAG_NAME, "table")
        
        if not tables:
            print(f"[DEBUG] Таблицы не найдены для адреса: {address}")
            return []
        
        # Используем первую таблицу, если она одна
        if len(tables) == 1:
            result_table = tables[0]
        else:
            # Поиск таблицы с данными о почтовых индексах
            result_table = None
            for table in tables:
                # Получение заголовков
                headers = table.find_elements(By.TAG_NAME, "th")
                if headers:
                    header_texts = [header.text.strip().lower() for header in headers]
                    
                    # Проверка, является ли это нужной таблицей
                    if any('индекс' in header.lower() or 'код' in header.lower() for header in header_texts):
                        result_table = table
                        break
        
        if not result_table:
            print("[DEBUG] Не удалось идентифицировать нужную таблицу")
            return []
        
        # Получение всех строк из таблицы
        all_rows = result_table.find_elements(By.TAG_NAME, "tr")
        
        # Получение строк данных (пропуск заголовка)
        rows = all_rows[1:] if len(all_rows) > 1 else []
        
        # Ограничение до первых 10 строк
        rows = rows[:10]
        
        result = []
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if cols:
                # Извлечение текста из каждой колонки
                row_data = [col.text.strip() for col in cols]
                result.append(row_data)
        
        return result
    
    except Exception as e:
        print(f"[DEBUG] Ошибка при парсинге: {e}")
        return []


def search_multiple_addresses(addresses:list[str]):
    """
    Поиск почтовых индексов для нескольких адресов
    
    Args:
        addresses (list): Список адресов для поиска
    
    Returns:
        dict: Словарь с результатами поиска для каждого адреса
    """
    results = {}
    driver = None
    
    try:
        # Создаем драйвер один раз для всех запросов
        driver = setup_driver()
        
        for address in addresses:
            print(f"\n[DEBUG] Поиск индекса для адреса: {address}")
            address_results = search_postal_code(driver, address)
            results[address] = address_results
            
            # Небольшая пауза между запросами
            time.sleep(1)
    
    except Exception as e:
        print(f"[DEBUG] Ошибка при обработке адресов: {e}")
    
    finally:
        # Закрываем драйвер после обработки всех адресов
        if driver:
            driver.quit()
    
    return results


def save_to_csv(data:list[list[str]], filename:str='postal_codes.csv'):
    """
    Сохранение данных в CSV файл
    
    Args:
        data (list): Список строк для сохранения
        filename (str): Имя выходного файла
    """
    if not data:
        print("[DEBUG] Нет данных для сохранения")
        return
    
    try:
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
        
        print(f"[DEBUG] Данные успешно сохранены в {filename}")
    
    except Exception as e:
        print(f"[DEBUG] Ошибка при сохранении в CSV: {e}")


def save_multiple_results_to_csv(results, filename='all_postal_codes.csv'):
    """
    Сохранение результатов для нескольких адресов в CSV
    
    Args:
        results (dict): Словарь с результатами поиска для каждого адреса
        filename (str): Имя выходного файла
    """
    if not results:
        print("[DEBUG] Нет результатов для сохранения")
        return
    
    try:
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
        
        print(f"[DEBUG] Все результаты успешно сохранены в {filename}")
    
    except Exception as e:
        print(f"[DEBUG] Ошибка при сохранении результатов: {e}")


def get_postal_code(address:str):
    """
    Получение почтового индекса для адреса
    
    Args:
        address (str): Адрес для поиска
        
    Returns:
        str: Почтовый индекс или None, если не найден
    """
    driver = None
    try:
        driver = setup_driver()
        results = search_postal_code(driver, address)
        if results:
            return results[0][0]  # Возвращаем первый найденный индекс
        else:
            return None
    finally:
        if driver:
            driver.quit()


def main():
    # Примеры адресов
    addresses = [
        "город Минск улица Октябрьская 10/2",
        "город Минск проспект Независимости 4",
        "город Витебск улица Ленина 26/2"
    ]
    
    # Поиск индексов для нескольких адресов
    results = search_multiple_addresses(addresses)
    
    # Сохранение всех результатов
    save_multiple_results_to_csv(results, filename='output_example/postal_codes.csv')
    
    # Вывод результатов
    for address, address_results in results.items():
        print(f"\nРезультаты для адреса: {address}")
        if address_results:
            print(f"Найдено {len(address_results)} результатов")
            for row in address_results:
                print(f"Индекс: {row[0]}, Адрес: {row[3]}, {row[4]}, {row[5]}")
        else:
            print("Результаты не найдены")


if __name__ == "__main__":
    main()