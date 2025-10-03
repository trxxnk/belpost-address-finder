"""
Сервис для парсинга и обработки адресов.
Централизует всю логику парсинга, предобработки и классификации адресов.
"""

import re
from typing import Dict, Any, Tuple, Optional
from core.utils.postal_client import PostalClient
from core.address_processor import AddressProcessor
from config import settings
from logger import get_configured_logger
from rapidfuzz import fuzz, process

logger = get_configured_logger("core.address_parsing_service")


class AddressParsingService:
    """
    Сервис для парсинга и обработки адресов.
    Содержит всю бизнес-логику работы с адресами.
    """
    
    # Константы для предобработки сокращений
    ABBREVIATION_MAPPINGS = {
        r"(?<!\w)г\.?(?!\w)": "город",
        r"(?<!\w)обл\.?(?!\w)": "область",
        r"(?<!\w)р-н(?!\w)": "район",
        r"(?<!\w)рн(?!\w)": "район",
        r"(?<!\w)аг\.?(?!\w)": "агрогородок",
        r"(?<!\w)гп\.?(?!\w)": "городской поселок",
        r"(?<!\w)п\.?(?!\w)": "поселок",
        r"(?<!\w)рп\.?(?!\w)": "рабочий поселок",
        r"(?<!\w)кп\.?(?!\w)": "курортный поселок",
        r"(?<!\w)х\.?(?!\w)": "хутор",
        r"(?<!\w)пгт(?!\w)": "поселок городского типа",
        r"(?<!\w)мкр\.?(?!\w)": "микрорайон",
        r"(?<!\w)с/с(?!\w)": "сельсовет",
        r"(?<!\w)с\.?(?!\w)": "село",
        r"(?<!\w)ул\.?(?!\w)": "улица",
        r"(?<!\w)пр-т(?!\w)": "проспект",
        r"(?<!\w)пер\.?(?!\w)": "переулок",
    }
    
    # Константы для классификации типов населенных пунктов
    CITY_TYPE_MAPPINGS = {
        r"(?<!\w)(город|г\.?)(?!\w)": "ГОРОД",
        r"(?<!\w)(агрогородок|аг\.?)(?!\w)": "АГРОГОРОДОК",
        r"(?<!\w)(деревня|д\.?)(?!\w)": "ДЕРЕВНЯ",
        r"(?<!\w)(поселок|п\.?)(?!\w)": "ПОСЕЛОК",
        r"(?<!\w)(городской поселок|гп\.?)(?!\w)": "ГОРОДСКОЙ ПОСЕЛОК",
        r"(?<!\w)(курортный поселок|кп\.?)(?!\w)": "КУРОРТНЫЙ ПОСЕЛОК",
        r"(?<!\w)(хутор|х\.?)(?!\w)": "ХУТОР",
        r"(?<!\w)(рабочий поселок|рп\.?)(?!\w)": "РАБОЧИЙ ПОСЕЛОК",
        r"(?<!\w)(село|с\.?)(?!\w)": "СЕЛО",
        r"(?<!\w)(сельсовет|с/с)(?!\w)": "СЕЛЬСОВЕТ"
    }
    
    # Константы для классификации типов улиц
    STREET_TYPE_MAPPINGS = {
        r"(?<!\w)(улица|ул\.?)(?!\w)": "УЛИЦА",
        r"(?<!\w)(проспект|пр-т|пр\.?)(?!\w)": "ПРОСПЕКТ",
        r"(?<!\w)(переулок|пер\.?)(?!\w)": "ПЕРЕУЛОК",
        r"(?<!\w)(проезд|пр-д)(?!\w)": "ПРОЕЗД",
        r"(?<!\w)(тракт)(?!\w)": "ТРАКТ",
        r"(?<!\w)(бульвар|б-р)(?!\w)": "БУЛЬВАР",
        r"(?<!\w)(тупик)(?!\w)": "ТУПИК",
        r"(?<!\w)(площадь|пл\.?)(?!\w)": "ПЛОЩАДЬ",
        r"(?<!\w)(кольцо)(?!\w)": "КОЛЬЦО",
        r"(?<!\w)(набережная|наб\.?)(?!\w)": "НАБЕРЕЖНАЯ",
        r"(?<!\w)(шоссе|ш\.?)(?!\w)": "ШОССЕ",
        r"(?<!\w)(микрорайон|мкр\.?)(?!\w)": "МИКРОРАЙОН"
    }
    
    # Константы для маппинга областей
    REGION_MAPPINGS = {
        "минск": "МИНСКАЯ",
        "брест": "БРЕСТСКАЯ",
        "витебск": "ВИТЕБСКАЯ",
        "гомель": "ГОМЕЛЬСКАЯ",
        "гродно": "ГРОДНЕНСКАЯ",
        "могилев": "МОГИЛЕВСКАЯ"
    }
    
    # Список областных центров
    MAJOR_CITIES = ["минск", "брест", "витебск", "гомель", "гродно", "могилев"]
    
    def __init__(self):
        self.postal_client = PostalClient()
        self.address_processor = AddressProcessor()
        logger.info("Инициализирован AddressParsingService")
    
    def preprocess_address(self, address: str) -> str:
        """
        Предобработка адреса - замена сокращений на полные слова.
        
        Args:
            address: Исходный адрес
            
        Returns:
            str: Предобработанный адрес
        """
        if not address:
            return ""
        
        preprocessed = address
        for pattern, replacement in self.ABBREVIATION_MAPPINGS.items():
            preprocessed = re.sub(pattern, replacement, preprocessed, flags=re.IGNORECASE)
        
        logger.debug(f"Предобработка: '{address}' -> '{preprocessed}'")
        return preprocessed
    
    def extract_selsovet(self, address: str) -> Tuple[Optional[str], str]:
        """
        Извлекает название сельсовета из адреса.
        
        Args:
            address: Адрес для обработки
            
        Returns:
            Tuple[Optional[str], str]: (название_сельсовета, очищенный_адрес)
        """
        if not address:
            return None, address
        
        text = address
        
        # Ищем "X сельсовет"
        match_left = re.search(r'(\w+)\s+сельсовет', text)
        # Ищем "сельсовет Y"
        match_right = re.search(r'сельсовет\s+(\w+)', text)
        
        if not match_left and not match_right:
            return None, address
        
        selsovet_name = None
        cleaned_address = address
        
        if match_left:
            left_word = match_left.group(1)
            if left_word != "район":  # если это не "район"
                selsovet_name = left_word
                cleaned_address = re.sub(rf'\b{left_word}\s+сельсовет\b', '', cleaned_address, flags=re.IGNORECASE)
        
        if selsovet_name is None and match_right:
            right_word = match_right.group(1)
            selsovet_name = right_word
            cleaned_address = re.sub(rf'\bсельсовет\s+{right_word}\b', '', cleaned_address, flags=re.IGNORECASE)
        
        cleaned_address = re.sub(r'\s{2,}', ' ', cleaned_address).strip()
        
        logger.debug(f"Извлечение сельсовета: '{address}' -> сельсовет='{selsovet_name}', адрес='{cleaned_address}'")
        return selsovet_name, cleaned_address
    
    def classify_city_type(self, city_raw: str) -> Optional[str]:
        """
        Определяет тип населенного пункта по ключевым словам.
        
        Args:
            city_raw: Сырое название города
            
        Returns:
            Optional[str]: Тип города или None
        """
        if not city_raw:
            return None
        
        for pattern, city_type in self.CITY_TYPE_MAPPINGS.items():
            if re.search(pattern, city_raw, re.IGNORECASE):
                logger.debug(f"Определен тип города: '{city_raw}' -> '{city_type}'")
                return city_type
        
        # Если тип не определен, но город - один из областных центров
        if any(city in city_raw.lower() for city in self.MAJOR_CITIES):
            logger.debug(f"Областной центр: '{city_raw}' -> 'ГОРОД'")
            return "ГОРОД"
        
        return None
    
    def classify_street_type(self, street_raw: str) -> Optional[str]:
        """
        Определяет тип улицы по ключевым словам.
        
        Args:
            street_raw: Сырое название улицы
            
        Returns:
            Optional[str]: Тип улицы или None
        """
        if not street_raw:
            return None
        
        for pattern, street_type in self.STREET_TYPE_MAPPINGS.items():
            if re.search(pattern, street_raw, re.IGNORECASE):
                logger.debug(f"Определен тип улицы: '{street_raw}' -> '{street_type}'")
                return street_type
        
        return None
    
    def map_region(self, region_raw: str) -> Optional[str]:
        """
        Маппинг области в стандартное название.
        
        Args:
            region_raw: Сырое название области
            
        Returns:
            Optional[str]: Стандартное название области или None
        """
        if not region_raw:
            return None
        
        # Более агрессивное удаление слов "область" и вариантов
        region_clean = re.sub(r"\s*(область|обл\.?)\s*", " ", region_raw, flags=re.IGNORECASE).strip()
        logger.debug(f"Очистка области: '{region_raw}' -> '{region_clean}'")
        
        # Проверяем совпадение с ключевыми словами областей
        for key, value in self.REGION_MAPPINGS.items():
            region_lower = region_clean.lower()
            if key in region_lower:
                logger.debug(f"Маппинг области найден: '{region_raw}' -> '{region_clean}' -> '{value}'")
                return value
        
        logger.debug(f"Маппинг области не найден для: '{region_raw}' -> '{region_clean}'")
        return None
    
    def clean_text_from_type(self, text: str, type_mappings: Dict[str, str]) -> str:
        """
        Очищает текст от типовых слов.
        
        Args:
            text: Исходный текст
            type_mappings: Словарь паттернов для очистки
            
        Returns:
            str: Очищенный текст
        """
        if not text:
            return ""
        
        cleaned = text
        for pattern in type_mappings.keys():
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
        
        return cleaned
    
    def parse_full_address(self, full_address: str) -> Dict[str, Any]:
        """
        Полный парсинг адреса с извлечением всех компонентов.
        
        Args:
            full_address: Полный адрес для парсинга
            
        Returns:
            Dict[str, Any]: Словарь с компонентами адреса
        """
        if not full_address:
            return {}
        
        logger.info(f"Начало парсинга адреса: '{full_address}'")
        
        try:
            result = self._preprocess_and_parse_address_components(full_address)
            corrected_result = self._correct_street_if_needed(result)
            
            # Объединяем результаты, но сохраняем изначальные значения district и region
            final_result = result.copy()
            
            # Обновляем поля из корректированного результата, но только если они не пустые
            for key, value in corrected_result.items():
                if value is not None:  # Обновляем только если значение не None
                    final_result[key] = value
                    
            logger.info(f"Парсинг завершен успешно: {final_result}")
            return final_result
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге адреса '{full_address}': {e}")
            return {}
    
    def _preprocess_and_parse_address_components(self, address: str) -> Dict[str, Any]:
        """
        Парсинг компонентов адреса без коррекции.
        
        Args:
            address: Адрес для парсинга
            
        Returns:
            Dict[str, Any]: Словарь с компонентами адреса
        """
        preprocessed_address = self.preprocess_address(address)
        selsovet_name, address_no_selsovet = self.extract_selsovet(preprocessed_address)
        parsed_address = self.postal_client.parse_address(address_no_selsovet) 
        if not parsed_address:
            logger.warning("Нет ответа от сервиса парсинга")
            return {}
        
        result = {
            "selsovet": selsovet_name,
            "region": None,
            "district": None,
            "city_type": None,
            "city_name": None,
            "street_type": None,
            "street_name": None,
            "house_number": None
        }
        
        if "state" in parsed_address:
            region_mapped = self.map_region(parsed_address["state"])
            # Сохраняем оригинальное значение если маппинг не удался
            if region_mapped is not None:
                result["region"] = region_mapped
            else:
                # Если маппинг не удался, сохраняем оригинальное значение из микросервиса
                result["region"] = parsed_address["state"]
                logger.debug(f"Маппинг области не удался, сохраняем оригинальное значение: '{parsed_address['state']}'")
        
        if "state_district" in parsed_address:
            district_clean = re.sub(r"(?<!\w)(район|р-н|рн)\.?(?!\w)", "", 
                                 parsed_address["state_district"], flags=re.IGNORECASE).strip()
            # Сохраняем очищенное значение района или оригинальное если пустое
            if district_clean:
                result["district"] = district_clean
            else:
                # Если очистка убрала все, сохраняем оригинальное значение
                result["district"] = parsed_address["state_district"]
                logger.debug(f"Очистка района убрала все содержимое, сохраняем оригинальное: '{parsed_address['state_district']}'")
        
        city_raw = parsed_address.get("city", "") or parsed_address.get("house", "")
        if city_raw:
            city_type = self.classify_city_type(city_raw)
            city_name = self.clean_text_from_type(city_raw, self.CITY_TYPE_MAPPINGS)
            result["city_type"] = city_type
            result["city_name"] = city_name
        
        if "road" in parsed_address:
            street_raw = parsed_address["road"]
            street_type = self.classify_street_type(street_raw)
            street_name = self.clean_text_from_type(street_raw, self.STREET_TYPE_MAPPINGS)
            result["street_type"] = street_type
            result["street_name"] = street_name
        
        if "house_number" in parsed_address:
            house_clean = re.sub(r"(?<!\w)(дом|д\.?)(?!\w)", "", 
                               parsed_address["house_number"], flags=re.IGNORECASE).strip()
            result["house_number"] = house_clean
        
        return result
    
    def correct_street_name(self, input_street: str, correct_streets_file: str, threshold: int = 80) -> str:
        """
        Исправляет опечатки в названии улицы с использованием fuzzy matching.
        
        Args:
            input_street (str): Входное название улицы для проверки
            correct_streets_file (str): Путь к файлу с корректными названиями улиц
            threshold (int): Пороговое значение совпадения (0-100), по умолчанию 80
        
        Returns:
        str: Исправленное название улицы или исходное, если совпадение слабое
        """
        try:
            with open(correct_streets_file, 'r', encoding='utf-8') as file:
                correct_streets = [line.strip().lower() for line in file if line.strip()]
            
            if not correct_streets:
                return input_street
            
            best_match, score, _ = process.extractOne(input_street.lower(), correct_streets, scorer=fuzz.token_sort_ratio)
            
            if score >= threshold:
                logger.debug(f"Исправление улицы: '{input_street}' -> '{best_match}' (score: {score}%)")
                return best_match.lower().capitalize()
            else:
                logger.debug(f"Нет совпадения: '{input_street}' -> '{best_match}' (score: {score}%)")
                return input_street
                
        except FileNotFoundError:
            logger.error(f"Файл {correct_streets_file} не найден")
            return input_street
        except Exception as e:
            logger.error(f"Произошла ошибка: {e}")
            return input_street
    
    def _correct_street_if_needed(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Коррекция улицы, если это необходимо.
        
        Args:
            result: Результат парсинга адреса
            
        Returns:
            Dict[str, Any]: Обновленные данные улицы или пустой словарь
        """
        try:
            # Строим временный адрес для коррекции
            temp_address = self.address_processor.build_address(
                region=result.get("region"),
                district=result.get("district"),
                sovet=result.get("selsovet"),
                city_type=result.get("city_type"),
                city_name=result.get("city_name"),
                street_type=result.get("street_type"),
                street_name=result.get("street_name"),
                spec_mode=True
            )
            
            corrected_street_name = self.correct_street_name(temp_address, settings.data.street_book_file, threshold=80)
            corrected_address_components = self._preprocess_and_parse_address_components(corrected_street_name)
            corrected_address_components.update({"house_number": result.get("house_number")})
            return corrected_address_components
            
        except Exception as e:
            logger.error(f"Ошибка при коррекции улицы: {e}")
            return {}
