import flet as ft
from typing import List

from models import SearchResult
from services import AddressService
from assets.styles import PADDING
from views.components import create_header, create_search_form, create_result_card

class MainView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.address_service = AddressService()
        self.results_column = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            height=500
        )
        
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
        
        # Блок результатов
        results_header = ft.Text(
            "Результаты поиска:",
            size=18,
            weight=ft.FontWeight.BOLD
        )
        
        results_container = ft.Container(
            content=ft.Column([
                results_header,
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
    
    def _perform_search(self, e, city_type_dropdown, city_field, 
                       street_type_dropdown, street_field, 
                       house_field, progress_ring, progress_text):
        """Выполнение поиска адреса"""
        if not city_field.value or not city_field.value.strip():
            self.page.add(
                ft.SnackBar(content=ft.Text("Введите название населенного пункта"))
            )
            return
        if not street_field.value or not street_field.value.strip():
            self.page.add(
                ft.SnackBar(content=ft.Text("Введите название улицы"))
            )
            return
        
        # Очистка предыдущих результатов
        self.results_column.controls.clear()
        self.form_controls["search_button"].disabled = True
        self.page.update()
        
        try:
            # Формируем строку адреса
            self.address_service.city_type = city_type_dropdown.value.lower()
            self.address_service.city_name = city_field.value.strip()
            self.address_service.street_type = street_type_dropdown.value.lower()
            self.address_service.street_name = street_field.value.strip()
            self.address_service.building = house_field.value.strip()
            
            address_query = self.address_service.build_address(
                city_type=self.address_service.city_type,
                city_name=self.address_service.city_name,
                street_type=self.address_service.street_type,
                street_name=self.address_service.street_name,
                building=self.address_service.building
            )
            
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
