"""
ViewModel для управления поиском адресов.
Отвечает за состояние поиска и взаимодействие с сервисами.
"""

from typing import List, Optional, Callable, Dict, Any
from models.search_result import SearchResult
from models.dropdown_values import RegionType, CityType, StreetType
from services.address_service import AddressService
from logger import get_logger
from exceptions import BelpostServiceException, NetworkException, ParsingException, ValidationException
from .base_viewmodel import BaseViewModel


class AddressViewModel(BaseViewModel):
    """
    ViewModel для управления поиском адресов.
    Отвечает за состояние поиска и взаимодействие с сервисами.
    """
    
    def __init__(self, address_service: AddressService):
        """
        Инициализация ViewModel для поиска адресов
        
        Args:
            address_service: Сервис для работы с адресами
        """
        super().__init__()
        self.address_service = address_service
        self.logger = get_logger("addr_corr.viewmodels.address")
        
        # Состояние поиска
        self.results: List[SearchResult] = []
        self.is_searching = False
        self.current_search_query = ""
        self.error_message = ""
        
        # Параметры поиска
        self.region = RegionType.NONE.value
        self.district = ""
        self.sovet = ""
        self.city_type = CityType.NONE.value
        self.city_name = ""
        self.street_type = StreetType.NONE.value
        self.street_name = ""
        self.building = ""
        
        self.logger.info("Инициализирован AddressViewModel")
    
    def set_search_params(self, **kwargs) -> None:
        """
        Установка параметров поиска
        
        Args:
            **kwargs: Параметры поиска (region, district, sovet и т.д.)
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                self.notify(key)
                self.logger.debug(f"Установлен параметр поиска {key}: {value}")
    
    def validate_search_params(self) -> bool:
        """
        Валидация параметров поиска
        
        Returns:
            bool: True, если параметры валидны, иначе False
        """
        # Проверка наличия минимально необходимых данных для поиска
        has_city = (self.city_type != CityType.NONE.value and 
                   self.city_name and self.city_name.strip())
        has_street = (self.street_type != StreetType.NONE.value and 
                     self.street_name and self.street_name.strip())
        has_region = self.region != RegionType.NONE.value
        has_district = self.district and self.district.strip()
        
        if not (has_city or has_street or has_region or has_district):
            self.error_message = "Укажите хотя бы один параметр для поиска"
            self.notify("error_message")
            return False
        
        return True
    
    def search_address(self, progress_callback: Optional[Callable[[str], None]] = None) -> None:
        """
        Выполнение поиска адреса
        
        Args:
            progress_callback: Функция обратного вызова для отображения прогресса
        """
        # Проверяем, не выполняется ли уже поиск
        if self.is_searching:
            self.logger.warning("Попытка запуска поиска во время выполнения другого поиска")
            return
        
        # Валидация параметров
        if not self.validate_search_params():
            return
        
        self.is_searching = True
        self.notify("is_searching")
        
        # Очистка предыдущих результатов и ошибок
        self.results = []
        self.notify("results")
        self.error_message = ""
        self.notify("error_message")
        
        try:
            # Формирование строки адреса
            self.current_search_query = self.address_service.build_address(
                region=self.region,
                district=self.district,
                sovet=self.sovet,
                city_type=self.city_type,
                city_name=self.city_name,
                street_type=self.street_type,
                street_name=self.street_name,
                building=self.building
            )
            self.notify("current_search_query")
            
            # Проверка, что строка адреса не пустая
            if not self.current_search_query:
                self.error_message = "Укажите хотя бы один параметр для поиска"
                self.notify("error_message")
                self.is_searching = False
                self.notify("is_searching")
                return
            
            # Выполнение поиска
            self.logger.info(f"Выполняется поиск адреса: {self.current_search_query}")
            self.results = self.address_service.search_address(
                self.current_search_query,
                progress_callback=progress_callback
            )
            self.notify("results")
            
            self.logger.info(f"Найдено {len(self.results)} результатов")
            
        except (BelpostServiceException, NetworkException, ParsingException) as e:
            self.error_message = f"Ошибка при поиске: {str(e)}"
            self.logger.error(self.error_message)
            self.notify("error_message")
            
        except ValidationException as e:
            self.error_message = f"Ошибка валидации: {str(e)}"
            self.logger.error(self.error_message)
            self.notify("error_message")
            
        except Exception as e:
            self.error_message = f"Непредвиденная ошибка: {str(e)}"
            self.logger.error(f"Непредвиденная ошибка при поиске: {str(e)}", exc_info=True)
            self.notify("error_message")
            
        finally:
            self.is_searching = False
            self.notify("is_searching")
    
    def clear_results(self) -> None:
        """
        Очистка результатов поиска
        """
        self.results = []
        self.notify("results")
        self.current_search_query = ""
        self.notify("current_search_query")
        self.error_message = ""
        self.notify("error_message")
        self.logger.debug("Результаты поиска очищены")
    
    def clear_error(self) -> None:
        """
        Очистка сообщения об ошибке
        """
        self.error_message = ""
        self.notify("error_message")
    
    def get_search_url(self) -> str:
        """
        Получение URL для поиска на сайте Белпочты
        
        Returns:
            str: URL для поиска
        """
        if not self.current_search_query:
            return ""
        
        from urllib.parse import quote
        encoded_query = quote(self.current_search_query)
        return f"https://www.belpost.by/Uznatpochtovyykod28indek?search={encoded_query}"
    
    def close(self) -> None:
        """
        Закрытие ресурсов ViewModel
        """
        self.clear_all_callbacks()
        if hasattr(self, 'address_service'):
            self.address_service.close()
        self.logger.info("AddressViewModel закрыт")
