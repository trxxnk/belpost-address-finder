import re
import json
import pandas as pd
from typing import List, Dict, Any, Optional
from rapidfuzz import fuzz

from models.search_result import SearchResult
from models.dropdown_values import RegionType, StreetType, CityType

class AddressProcessor:
    """
    Сервис для обработки и фильтрации результатов поиска адресов
    """
    
    def __init__(self):
        self.abbr_dict = self._load_abbreviations()
        
        # Словарь для замены сокращений
        self.replace_dict = {
            "г.": "город",
            "аг.": "агрогородок", 
            "гп": "городской поселок",
            "д.": "деревня",
            "с/с": "сельский совет",
            "р-н": "район",
            "п.": "поселок",
            "рп": "рабочий поселок",
            "кп": "курортный поселок",
            "х.": "хутор",
            "пгт": "поселок городского типа",
        }
    
    def _load_abbreviations(self) -> Dict[str, str]:
        """Загрузка словаря аббревиатур"""
        try:
            with open('data/repositories/common/grouped_abbrs.json', 'r', encoding='utf-8') as f:
                grouped_dict = json.load(f)
                abbrs_dict = {}
                for fullname, abbrs in grouped_dict.items():
                    for abbr in abbrs:
                        abbrs_dict[abbr] = fullname
                return abbrs_dict
        except Exception as e:
            from logger import get_logger
            logger = get_logger("addr_corr.services.address_processor")
            logger.error(f"Ошибка загрузки аббревиатур: {e}")
            return {}
    
    def build_address(self, region: str = None, district: str = None, 
                     sovet: str = None,
                     city_type: str = None, city_name: str = None,
                     street_type:str = None, street_name: str = None, 
                     building: str = None,
                     spec_mode: bool = False) -> str:
        """Универсальный конструктор адреса"""
        parts = []
        
        # Проверяем, что значения не "НЕТ"
        if region and region != RegionType.NONE.value:
            region = region.lower().capitalize()
            parts.append(f"{region} область")
        if district:
            district = district.lower().capitalize()
            parts.append(f"{district} район")
        if sovet:
            sovet = sovet.lower().capitalize()
            parts.append(f"{sovet} сельсовет")
        if city_name and city_type != CityType.NONE.value:
            city_name = city_name.lower().capitalize()
            if city_type:
                parts.append(f"{city_type} {city_name}")
            else:
                parts.append(city_name)
        
        # Обработка улицы с учетом опции "ДРУГОЕ"
        if street_name:
            street_name = street_name.lower().capitalize()
            if street_type == StreetType.OTHER.value:
                # Если выбрано "ДРУГОЕ", добавляем только название улицы без типа
                parts.append(street_name)
            elif street_type != StreetType.NONE.value:
                # Если выбран конкретный тип, добавляем тип + название
                parts.append(f"{street_type} {street_name}")
        
        if building:
            parts.append(building)
            
        return ", ".join(parts) if not spec_mode else " ".join(parts).lower()
    
    def filter_addresses(self, df: pd.DataFrame, region: str = "", 
                        district: str = "", sovet: str = "", 
                        city: str = "") -> pd.DataFrame:
        """
        Фильтрация адресов по региону, району, сельсовету и городу
        
        Args:
            df: DataFrame с результатами поиска
            region: Название области
            district: Название района
            sovet: Название сельсовета
            city: Название населенного пункта
            
        Returns:
            pd.DataFrame: Отфильтрованный DataFrame
        """
        mask = pd.Series(True, index=df.index)
        
        # Фильтрация по области (если выбрана)
        if region and region != RegionType.NONE.value:
            mask &= df["Область"].astype(str).str.contains(region, case=False, na=False)
        
        # Фильтрация по району (если указан)
        if district:
            mask &= df["Район"].astype(str).str.contains(district, case=False, na=False)
        
        # Фильтрация по городу (если указан)
        if city:
            mask &= df["Город"].astype(str).str.contains(city, case=False, na=False)
            
        # Примечание: для сельсовета нет прямого соответствия в данных от belpost.by,
        # но можно попробовать найти его в названии населенного пункта или района
        if sovet:
            sovet_mask = (
                df["Город"].astype(str).str.contains(sovet, case=False, na=False) |
                df["Район"].astype(str).str.contains(sovet, case=False, na=False)
            )
            mask &= sovet_mask
            
        return df[mask]
    
    def add_similarity_scores(self, df: pd.DataFrame, target_string: str, 
                            column_name: str) -> pd.DataFrame:
        """Вычисление схожести с использованием rapidfuzz"""
        df = df.copy()
        scores = [fuzz.ratio(str(x).lower(), str(target_string).lower()) 
                 for x in df[column_name]]
        df['similarity_score'] = scores
        df.sort_values(by="similarity_score", ascending=False, inplace=True)
        return df
    
    def house_in_range(self, house: str, rule: str) -> bool:
        """Проверка принадлежности дома правилу из списка домов"""
        if not house or not rule:
            return False
            
        house = house.strip().upper()
        rule = rule.strip().upper()
        
        if rule == "ВСЕ":
            return True
            
        # Извлекаем номер дома
        house_match = re.match(r"(\d+)", house)
        if not house_match:
            return False
        house_num = int(house_match.group(1))
        
        # Разделяем правила через запятую
        parts = [p.strip().upper() for p in rule.split(",")]
        for part in parts:
            # Диапазон чёт/нечет
            m = re.match(r"\((\d+)-(\d+)\)", part)
            if m:
                start, end = int(m.group(1)), int(m.group(2))
                if house_num % 2 == start % 2 and start <= house_num <= end:
                    return True
                continue
                
            # Обычный диапазон
            m = re.match(r"^(\d+)-(\d+)$", part)
            if m:
                start, end = int(m.group(1)), int(m.group(2))
                if start <= house_num <= end:
                    return True
                continue
                
            # Конкретный номер
            if part == house.upper():
                return True
                
        return False
    
    def process_results(self, raw_results: List[List[str]], 
                       region: str = "", district: str = "", sovet: str = "",
                       city_type: str = "", city_name: str = "",
                       street_type: str = "", street_name: str = "", building: str = "",
                       progress_callback=None) -> List[SearchResult]:
        """
        Обработка результатов поиска
        
        Args:
            raw_results: Сырые результаты поиска от BelpostService
            region, district, sovet: Параметры для фильтрации по административному делению
            city_type, city_name: Параметры для фильтрации по населенному пункту
            street_type, street_name, building: Параметры для оценки схожести
            progress_callback: Функция обратного вызова для отображения прогресса
            
        Returns:
            List[SearchResult]: Отфильтрованные и отсортированные результаты поиска
        """
        if not raw_results:
            return []
        
        try:
            # Преобразование в DataFrame
            df = pd.DataFrame(raw_results, columns=[
                "Почтовый код", "Область", "Район", 
                "Город", "Улица", "Номер дома"
            ])

            if progress_callback:
                progress_callback("Фильтрация результатов...")
            
            # Фильтрация по административному делению и населенному пункту
            if region != RegionType.NONE.value or district or sovet or (city_name and city_type != CityType.NONE.value):
                df = self.filter_addresses(
                    df, 
                    region=region if region != RegionType.NONE.value else "", 
                    district=district, 
                    sovet=sovet, 
                    city=city_name if city_type != CityType.NONE.value else ""
                )

            if progress_callback:
                progress_callback("Вычисление схожести...")

            # Добавление оценок схожести для улицы с учетом опции "ДРУГОЕ"
            if street_name:
                # Если выбрано "ДРУГОЕ", ищем только по названию улицы без типа
                if street_type == StreetType.OTHER.value:
                    target_string = street_name
                # Если выбран конкретный тип (не "НЕТ"), ищем по типу + название
                elif street_type != StreetType.NONE.value:
                    target_string = f"{street_type} {street_name}"
                else:
                    target_string = ""
                
                if target_string:
                    df = self.add_similarity_scores(df, target_string, "Улица")
            
            # Проверка номера дома
            if building:
                df["house_match"] = df["Номер дома"].apply(
                    lambda r: self.house_in_range(building, r)
                )
            else:
                df["house_match"] = False

            if progress_callback:
                progress_callback("Формирование результатов...")
            
            # Преобразование в список результатов
            results:list[SearchResult] = []
            for _, row in df.iterrows():
                result = SearchResult(
                    postal_code=str(row["Почтовый код"]),
                    region=str(row["Область"]),
                    district=str(row["Район"]),
                    city=str(row["Город"]),
                    street=str(row["Улица"]),
                    house_numbers=str(row["Номер дома"]),
                    similarity_score=row.get("similarity_score", 0.0),
                    house_match=row.get("house_match", False)
                )
                results.append(result)
            
            # Сортировка результатов
            results.sort(key=lambda x: (x.house_match, x.similarity_score), reverse=True)
            
            return results[:10]  # Возвращаем топ-10 результатов
            
        except Exception as e:
            from logger import get_logger
            logger = get_logger("addr_corr.services.address_processor")
            logger.error(f"Ошибка обработки результатов: {e}")
            return []