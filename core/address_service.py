from typing import List, Optional
from sqlalchemy.orm import Session

from models.search_result import SearchResult
from models.dropdown_values import RegionType, StreetType, CityType
from data.models import get_database_engine
from core.belpost_service import BelpostService
from core.address_processor import AddressProcessor
from logger import get_configured_logger

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
    
    def close(self):
        """Закрытие ресурсов"""
        if self.session:
            self.session.close()
        self.belpost_service.close()