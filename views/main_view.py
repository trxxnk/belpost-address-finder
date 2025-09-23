import flet as ft
from typing import List
import urllib.parse
import webbrowser

from models import SearchResult
from services import AddressService
from assets.styles import PADDING, COLORS
from views.components import create_header, create_search_form, create_result_card
from models import RegionType, CityType, StreetType

class MainView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.address_service = AddressService()
        self.results_column = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            height=500
        )
        
        # Текущий поисковый запрос
        self.current_search_query = ""
        
        # Настройка страницы
        self._setup_page()
        
        # Создание компонентов
        self._create_components()
        
        # Обработка закрытия приложения
        self._setup_window_events()
    
    def _setup_page(self):
        """Настройка параметров страницы"""
        self.page.title = "Поиск адресов Белпочта"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window.width = 1200
        self.page.window.height = 800
        self.page.padding = 20
    
    def _create_components(self):
        """Создание компонентов интерфейса"""
        # Заголовок
        header = create_header()
        
        # Форма поиска
        search_form, self.form_controls = create_search_form(on_search=self._perform_search)
        
        # Блок результатов с кликабельным заголовком
        self.results_header = ft.TextButton(
            text="Результаты поиска:",
            style=ft.ButtonStyle(
                color=COLORS["primary"],
                overlay_color=ft.Colors.TRANSPARENT,
            ),
            on_click=self._open_search_url,
            tooltip="Нажмите, чтобы открыть результаты в браузере",
            disabled=True
        )
        
        results_container = ft.Container(
            content=ft.Column([
                self.results_header,
                self.results_column
            ]),
            padding=ft.padding.only(top=PADDING["medium"])
        )
        
        # Добавление компонентов на страницу
        self.page.add(
            ft.Column([
                header,
                search_form,
                results_container
            ])
        )
    
    def _update_progress(self, message: str):
        """Обновление индикатора прогресса"""
        self.form_controls["progress_text"].value = message
        self.form_controls["progress_text"].visible = True
        self.form_controls["progress_ring"].visible = True
        self.page.update()
    
    def _generate_search_url(self, query: str) -> str:
        """Генерация URL для поиска на belpost.by"""
        # Базовый URL для поиска на сайте белпочты
        base_url = "https://www.belpost.by/Uznatpochtovyykod28indek"
        
        # Кодируем параметры запроса
        encoded_query = urllib.parse.quote(query)
        
        # Формируем полный URL
        search_url = f"{base_url}?search={encoded_query}"
        
        return search_url
    
    def _open_search_url(self, e):
        """Открытие URL поиска в браузере"""
        if self.current_search_query:
            search_url = self._generate_search_url(self.current_search_query)
            webbrowser.open(search_url)
    
    def _perform_search(self, e, region_dropdown, district_field, sovet_field,
                       city_type_dropdown, city_field, 
                       street_type_dropdown, street_field, 
                       house_field, progress_ring, progress_text):
        """Выполнение поиска адреса"""
        # Проверка наличия минимально необходимых данных для поиска
        has_city = city_type_dropdown.value != CityType.NONE.value and city_field.value and city_field.value.strip()
        has_street = street_type_dropdown.value != StreetType.NONE.value and street_field.value and street_field.value.strip()
        has_region = region_dropdown.value != RegionType.NONE.value
        has_district = district_field.value and district_field.value.strip()
        
        if not (has_city or has_street or has_region or has_district):
            self.page.add(
                ft.SnackBar(content=ft.Text("Укажите хотя бы один параметр для поиска"))
            )
            return
        
        # Очистка предыдущих результатов
        self.results_column.controls.clear()
        self.form_controls["search_button"].disabled = True
        self.page.update()
        
        try:
            # Формируем параметры поиска
            self.address_service.region = region_dropdown.value
            self.address_service.district = district_field.value.strip() if district_field.value else ""
            self.address_service.sovet = sovet_field.value.strip() if sovet_field.value else ""
            self.address_service.city_type = city_type_dropdown.value
            self.address_service.city_name = city_field.value.strip() if city_field.value else ""
            self.address_service.street_type = street_type_dropdown.value
            self.address_service.street_name = street_field.value.strip() if street_field.value else ""
            self.address_service.building = house_field.value.strip() if house_field.value else ""
            
            # Формируем строку адреса для поиска
            address_query = self.address_service.build_address(
                region=self.address_service.region,
                district=self.address_service.district,
                sovet=self.address_service.sovet,
                city_type=self.address_service.city_type,
                city_name=self.address_service.city_name,
                street_type=self.address_service.street_type,
                street_name=self.address_service.street_name,
                building=self.address_service.building
            )
            
            # Если строка адреса пустая (все поля "НЕТ" или пустые), выдаем ошибку
            if not address_query:
                self.page.add(
                    ft.SnackBar(content=ft.Text("Укажите хотя бы один параметр для поиска"))
                )
                self.form_controls["search_button"].disabled = False
                self.page.update()
                return
            
            # Сохраняем текущий поисковый запрос для генерации URL
            self.current_search_query = address_query
            
            # Активируем кнопку заголовка результатов
            self.results_header.disabled = False
            self.results_header.text = f"Результаты поиска: {address_query}"
            
            # Поиск
            results = self.address_service.search_address(
                address_query,
                progress_callback=self._update_progress
            )
            
            # Скрытие прогресса
            progress_ring.visible = False
            progress_text.visible = False
            
            self._display_results(results)
            
        except Exception as e:
            progress_ring.visible = False
            progress_text.visible = False
            self.results_column.controls.append(
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
            self.form_controls["search_button"].disabled = False
            self.page.update()
    
    def _display_results(self, results: List[SearchResult]):
        """Отображение результатов поиска"""
        if not results:
            self.results_column.controls.append(
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
            for result in results:
                result_card = create_result_card(result)
                self.results_column.controls.append(result_card)
    
    def _setup_window_events(self):
        """Настройка обработчиков событий окна"""
        def on_window_event(e):
            if e.data == "close":
                self.address_service.close()
        
        self.page.on_window_event = on_window_event