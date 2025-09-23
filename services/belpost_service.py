from typing import List, Dict, Any, Optional
from parser import setup_driver, search_postal_code

class BelpostService:
    """
    Сервис для взаимодействия с API belpost.by
    Отвечает за запросы к сайту белпочты для получения почтовых индексов
    """
    
    def __init__(self):
        self.driver = None
    
    def initialize_driver(self):
        """Инициализация веб-драйвера"""
        if not self.driver:
            self.driver = setup_driver()
    
    def search_postal_code(self, search_query: str, progress_callback=None) -> List[List[str]]:
        """
        Поиск почтового индекса на сайте belpost.by
        
        Args:
            search_query: Строка запроса адреса
            progress_callback: Функция обратного вызова для отображения прогресса
            
        Returns:
            List[List[str]]: Список результатов поиска в формате
            [почтовый_код, область, район, город, улица, номера_домов]
        """
        try:
            if progress_callback:
                progress_callback("Инициализация драйвера браузера...")
                
            self.initialize_driver()

            if progress_callback:
                progress_callback("Поиск адреса на belpost.by...")

            # Выполнение поиска на belpost.by
            raw_results = search_postal_code(self.driver, search_query)
            return raw_results or []
            
        except Exception as e:
            print(f"Ошибка при поиске на belpost.by: {e}")
            return []
    
    def close(self):
        """Закрытие ресурсов веб-драйвера"""
        if self.driver:
            self.driver.quit()
            self.driver = None
