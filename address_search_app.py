import os
import re
import json
import pandas as pd
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

import flet as ft
from sqlalchemy.orm import Session
from rapidfuzz import fuzz

from db.models import (StreetType, CityType, Address, BelpostAddress,
                       get_database_engine, get_database_url)
from parser import setup_driver, search_postal_code


@dataclass
class SearchResult:
    postal_code: str
    region: str
    district: str
    city: str
    street: str
    house_numbers: str
    similarity_score: float = 0.0
    house_match: bool = False


class AddressSearchApp:
    def __init__(self):
        self.engine = get_database_engine(echo=False)
        self.session = Session(self.engine)
        self.driver = None
        self.abbr_dict = self._load_abbreviations()
        
        self.region = ""
        self.district = ""
        self.sovet = ""
        self.city_name = ""
        self.city_type = ""
        self.street_type = ""
        self.street_name = ""
        self.building = ""
        
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
            with open('db/grouped_abbrs.json', 'r', encoding='utf-8') as f:
                grouped_dict = json.load(f)
                abbrs_dict = {}
                for fullname, abbrs in grouped_dict.items():
                    for abbr in abbrs:
                        abbrs_dict[abbr] = fullname
                return abbrs_dict
        except Exception as e:
            print(f"Ошибка загрузки аббревиатур: {e}")
            return {}

    def build_address(self, region: str = None, district: str = None, 
                     sovet: str = None,
                     city_type: str = None, city_name: str = None,
                     street_type:str = None, street_name: str = None, 
                     building: str = None) -> str:
        """Универсальный конструктор адреса"""
        parts = []
        
        if region:
            parts.append(f"{region} область")
        if district:
            parts.append(f"{district} район")
        if sovet:
            parts.append(f"{sovet} сельсовет")
        if city_name:
            if city_type:
                parts.append(f"{city_type} {city_name}")
            else:
                parts.append(city_name)
        if street_name:
            if street_type:
                parts.append(f"{street_type} {street_name}")
            else:
                parts.append(street_name)
        if building:
            parts.append(building)
            
        return ", ".join(parts)

    def filter_addresses(self, df: pd.DataFrame, region: str, 
                        district: str, city: str) -> pd.DataFrame:
        """Фильтрация адресов по региону, району и городу"""
        mask = (
            (df["Область"].astype(str).str.contains(region, case=False, na=False) if region else True) &
            (df["Район"].astype(str).str.contains(district, case=False, na=False) if district else True) &
            (df["Город"].astype(str).str.contains(city, case=False, na=False) if city else True)
        )
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

    def search_address(self, search_query: str, progress_callback=None) -> List[SearchResult]:
        """Основная функция поиска адреса"""
        try:
            if progress_callback:
                progress_callback("Инициализация драйвера браузера...")
                
            if not self.driver:
                self.driver = setup_driver()

            if progress_callback:
                progress_callback("Поиск адреса на belpost.by...")

            # Поиск на belpost.by
            raw_results = search_postal_code(self.driver, search_query)
            print(raw_results)
            if not raw_results:
                return []
                
            # Преобразование в DataFrame
            df = pd.DataFrame(raw_results, columns=[
                "Почтовый код", "Область", "Район", 
                "Город", "Улица", "Номер дома"
            ])

            if progress_callback:
                progress_callback("Фильтрация результатов...")
            
            region = self.region
            district = self.district
            city = self.city_name
            street = self.street_name
            street_type = self.street_type
            building = self.building
            
            # Фильтрация
            if region or district or city:
                df = self.filter_addresses(df, region, district, city)

            if progress_callback:
                progress_callback("Вычисление схожести...")

            # Добавление оценок схожести
            if street:
                target_string = street_type + " " + street
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
            results = []
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
            print(f"Ошибка поиска: {e}")
            return []

    def close(self):
        """Закрытие ресурсов"""
        if self.session:
            self.session.close()
        if self.driver:
            self.driver.quit()


def main(page: ft.Page):
    page.title = "Поиск адресов Белпочта"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 1200
    page.window.height = 800
    page.padding = 20
    
    # Создание экземпляра приложения
    app = AddressSearchApp()
    
    # Компоненты интерфейса
    city_type_dropdown = ft.Dropdown(
        label="Тип населенного пункта",
        options=[ft.dropdown.Option(key=ct.value, text=ct.value) for ct in CityType],
        width=200
    )
    city_field = ft.TextField(
        label="Название населенного пункта",
        width=300
    )
    street_type_dropdown = ft.Dropdown(
        label="Тип улицы",
        options=[ft.dropdown.Option(key=st.value, text=st.value) for st in StreetType],
        width=200
    )
    street_field = ft.TextField(
        label="Название улицы",
        width=300
    )
    house_field = ft.TextField(
        label="Номер дома",
        width=150
    )
    search_button = ft.ElevatedButton(
        text="Найти",
        icon=ft.Icons.SEARCH
    )
    progress_ring = ft.ProgressRing(visible=False)
    progress_text = ft.Text("", visible=False)
    results_column = ft.Column(
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
        height=500
    )
    def update_progress(message: str):
        progress_text.value = message
        progress_text.visible = True
        progress_ring.visible = True
        page.update()
    def perform_search(e=None):
        if not city_field.value or not city_field.value.strip():
            page.add(
                ft.SnackBar(content=ft.Text("Введите название населенного пункта"))
            )
            return
        if not street_field.value or not street_field.value.strip():
            page.add(
                ft.SnackBar(content=ft.Text("Введите название улицы"))
            )
            return
        # Очистка предыдущих результатов
        results_column.controls.clear()
        search_button.disabled = True
        page.update()
        try:
            # Формируем строку адреса
            app.city_type = city_type_dropdown.value.lower()
            app.city_name = city_field.value.strip()
            app.street_type = street_type_dropdown.value.lower()
            app.street_name = street_field.value.strip()
            app.building = house_field.value.strip()
            address_query = app.build_address(
                city_type=app.city_type,
                city_name=app.city_name,
                street_type=app.street_type,
                street_name=app.street_name,
                building=app.building
            )
            # Поиск
            results = app.search_address(
                address_query,
                progress_callback=update_progress
            )
            # Скрытие прогресса
            progress_ring.visible = False
            progress_text.visible = False
            if not results:
                results_column.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Text(
                                "Адреса не найдены. Попробуйте изменить запрос.",
                                size=16,
                                color=ft.Colors.ORANGE
                            ),
                            padding=20
                        )
                    )
                )
            else:
                # Отображение результатов
                for i, result in enumerate(results):
                    card_color = ft.Colors.GREEN_50 if result.house_match else ft.Colors.GREY_100
                    result_card = ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(
                                        f"Почтовый индекс: {result.postal_code}",
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.BLUE
                                    ),
                                    ft.Chip(
                                        label=ft.Text("Точное совпадение"),
                                        bgcolor=ft.Colors.GREEN,
                                        visible=result.house_match
                                    ) if result.house_match else ft.Container(),
                                    ft.Chip(
                                        label=ft.Text(f"Схожесть: {result.similarity_score:.1f}%"),
                                        bgcolor=ft.Colors.BLUE_100,
                                        visible=result.similarity_score > 0
                                    ) if result.similarity_score > 0 else ft.Container()
                                ]),
                                ft.Divider(),
                                ft.Row([
                                    ft.Icon(ft.Icons.LOCATION_ON, color=ft.Colors.RED),
                                    ft.Text(f"Регион: {result.region}", size=14)
                                ]),
                                ft.Row([
                                    ft.Icon(ft.Icons.MAP, color=ft.Colors.ORANGE),
                                    ft.Text(f"Район: {result.district}", size=14)
                                ]),
                                ft.Row([
                                    ft.Icon(ft.Icons.LOCATION_CITY, color=ft.Colors.BLUE),
                                    ft.Text(f"Город: {result.city}", size=14)
                                ]),
                                ft.Row([
                                    ft.Icon(ft.Icons.STREETVIEW, color=ft.Colors.GREEN),
                                    ft.Text(f"Улица: {result.street}", size=14)
                                ]),
                                ft.Row([
                                    ft.Icon(ft.Icons.HOME, color=ft.Colors.PURPLE),
                                    ft.Text(f"Номера домов: {result.house_numbers}", size=14)
                                ]),
                            ]),
                            padding=20,
                            bgcolor=card_color,
                            border_radius=10
                        )
                    )
                    results_column.controls.append(result_card)
        except Exception as e:
            progress_ring.visible = False
            progress_text.visible = False
            results_column.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Text(
                            f"Ошибка при поиске: {str(e)}",
                            size=16,
                            color=ft.Colors.RED
                        ),
                        padding=20
                    )
                )
            )
        finally:
            search_button.disabled = False
            page.update()
    # Привязка событий
    search_button.on_click = perform_search
    # Основной макет
    page.add(
        ft.Column([
            # Заголовок
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.MAIL, size=40, color=ft.Colors.BLUE),
                    ft.Text(
                        "Поиск почтовых индексов Белпочта",
                        size=24,
                        weight=ft.FontWeight.BOLD
                    )
                ]),
                padding=ft.padding.only(bottom=20)
            ),
            # Блок ввода адреса
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            city_type_dropdown,
                            city_field
                        ]),
                        ft.Row([
                            street_type_dropdown,
                            street_field
                        ]),
                        ft.Row([
                            house_field,
                            search_button
                        ]),
                        ft.Row([
                            progress_ring,
                            progress_text
                        ]),
                    ]),
                    padding=20
                )
            ),
            # Результаты поиска
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Результаты поиска:",
                        size=18,
                        weight=ft.FontWeight.BOLD
                    ),
                    results_column
                ]),
                padding=ft.padding.only(top=20)
            )
        ])
    )
    # Обработка закрытия приложения
    def on_window_event(e):
        if e.data == "close":
            app.close()
    page.on_window_event = on_window_event


if __name__ == "__main__":
    ft.app(target=main)