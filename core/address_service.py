from typing import List, Optional, Dict
from sqlalchemy.orm import Session

from models.search_result import SearchResult
from models.dropdown_values import RegionType, StreetType, CityType
from data.models import get_database_engine
from core.belpost_service import BelpostService
from core.address_processor import AddressProcessor
from core.address_parsing_service import AddressParsingService
from logger import get_configured_logger
from urllib.parse import quote

logger = get_configured_logger("core.address_service")

class AddressService:
    """
    Основной сервис для поиска адресов
    Объединяет функциональность запросов к belpost.by и обработки результатов
    """
    
    def __init__(self):
        self.engine = get_database_engine(echo=False)
        self.session = Session(self.engine)
        self.belpost_service = BelpostService()
        self.address_processor = AddressProcessor()
        self.parsing_service = AddressParsingService()
        self.region = RegionType.NONE.value
        self.district = ""
        self.sovet = ""
        self.city_name = ""
        self.city_type = CityType.NONE.value
        self.street_type = StreetType.NONE.value
        self.street_name = ""
        self.building = ""
    
    def build_address(self, region: str = None, district: str = None, 
                     sovet: str = None,
                     city_type: str = None, city_name: str = None,
                     street_type:str = None, street_name: str = None, 
                     building: str = None) -> str:
        """Универсальный конструктор адреса"""
        return self.address_processor.build_address(
            region, district, sovet, city_type, city_name,
            street_type, street_name, building
        )
    
    def search_address(self, search_query: str, progress_callback=None) -> List[SearchResult]:
        """
        Основная функция поиска адреса
        
        Args:
            search_query: Строка запроса адреса
            progress_callback: Функция обратного вызова для отображения прогресса
            
        Returns:
            List[SearchResult]: Результаты поиска
        """
        try:
            # Получение сырых результатов от belpost.by
            raw_results = self.belpost_service.search_postal_code(search_query, progress_callback)
            
            # Обработка результатов
            results = self.address_processor.process_results(
                raw_results,
                region=self.region,
                district=self.district,
                sovet=self.sovet,
                city_type=self.city_type,
                city_name=self.city_name,
                street_type=self.street_type,
                street_name=self.street_name,
                building=self.building,
                progress_callback=progress_callback
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return []
    
    def validate_search_params(self, region: str = None, district: str = None, 
                              sovet: str = None, city_type: str = None, 
                              city_name: str = None, street_type: str = None, 
                              street_name: str = None, **kwargs) -> bool:
        """
        Валидация параметров поиска
        
        Args:
            region: Область
            district: Район
            sovet: Сельсовет
            city_type: Тип населенного пункта
            city_name: Название населенного пункта
            street_type: Тип улицы
            street_name: Название улицы
            **kwargs: Дополнительные параметры
            
        Returns:
            bool: True, если параметры валидны, иначе False
        """
        # Проверка наличия минимально необходимых данных для поиска
        has_city = (city_type and city_type != CityType.NONE.value and 
                   city_name and city_name.strip())
        has_street = (street_type and street_type != StreetType.NONE.value and 
                     street_name and street_name.strip())
        has_region = region and region != RegionType.NONE.value
        has_district = district and district.strip()
        
        is_valid = has_city or has_street or has_region or has_district
        
        logger.debug(f"Валидация параметров поиска: has_city={has_city}, has_street={has_street}, "
                    f"has_region={has_region}, has_district={has_district}, result={is_valid}")
        
        return is_valid
    
    def get_search_url(self, search_query: str) -> str:
        """
        Получение URL для поиска на сайте Белпочты
        
        Args:
            search_query: Строка запроса для поиска
            
        Returns:
            str: URL для поиска
        """
        if not search_query:
            return ""
        
        encoded_query = quote(search_query)
        url = f"https://www.belpost.by/Uznatpochtovyykod28indek?search={encoded_query}"
        
        logger.debug(f"Сформирован URL для поиска: {url}")
        return url
    
    def parse_and_fill_address(self, full_address: str) -> Dict[str, str]:
        """
        Парсинг полного адреса и возврат структурированных данных
        
        Args:
            full_address: Полный адрес для парсинга
            
        Returns:
            Dict[str, str]: Словарь с компонентами адреса
        """
        if not full_address:
            return {}
        
        logger.info(f"Парсинг адреса через AddressService: '{full_address}'")
        
        try:
            parsed_data = self.parsing_service.parse_full_address(full_address)
            
            # Преобразуем результат в формат, удобный для UI
            result = {
                "region": parsed_data.get("region", ""),
                "district": parsed_data.get("district", ""),
                "sovet": parsed_data.get("selsovet", ""),
                "city_type": parsed_data.get("city_type", ""),
                "city_name": parsed_data.get("city_name", ""),
                "street_type": parsed_data.get("street_type", ""),
                "street_name": parsed_data.get("street_name", ""),
                "building": parsed_data.get("house_number", "")
            }
            
            # Очищаем пустые значения
            result = {k: v for k, v in result.items() if v}
            
            logger.info(f"Результат парсинга: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге адреса '{full_address}': {e}")
            return {}
    
    def close(self):
        """Закрытие ресурсов"""
        if self.session:
            self.session.close()
        self.belpost_service.close()