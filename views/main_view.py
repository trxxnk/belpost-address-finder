"""
Главное представление приложения.
Отвечает за отображение UI и взаимодействие с пользователем.
"""

import flet as ft
from typing import List
import webbrowser

from models.search_result import SearchResult
from services.address_service import AddressService
from viewmodels.address_viewmodel import AddressViewModel
from assets.styles import PADDING, COLORS
from views.components import create_header, create_search_form, create_result_card
from models.dropdown_values import RegionType, CityType, StreetType
from logger import get_logger

# Создание логгера для модуля
logger = get_logger("addr_corr.views.main")


class MainView:
    """
    Главное представление приложения.
    Отвечает за отображение UI и взаимодействие с пользователем.
    """
    
    def __init__(self, page: ft.Page):
        """
        Инициализация главного представления
        
        Args:
            page: Страница Flet
        """
        self.page = page
        
        # Создание ViewModel
        address_service = AddressService()
        self.address_viewmodel = AddressViewModel(address_service)
        
        # Регистрация колбэков для обновления UI
        self.address_viewmodel.register_callback("is_searching", self._update_search_state)
        self.address_viewmodel.register_callback("results", self._display_results)
        self.address_viewmodel.register_callback("error_message", self._show_error)
        self.address_viewmodel.register_callback("current_search_query", self._update_search_query)
        
        # Настройка страницы
        self._setup_page()
        
        # Создание компонентов
        self._create_components()
        
        # Обработка закрытия приложения
        self._setup_window_events()
        
        logger.info("Инициализировано главное представление")
    
    def _setup_page(self):
        """Настройка параметров страницы"""
        self.page.title = "Поиск адресов Белпочта"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window.width = 1200
        self.page.window.height = 800
        self.page.padding = 20
        self.page.scroll = "auto"  # Включаем прокрутку страницы
    
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
        
        # Контейнер для результатов поиска (адаптивная сетка)
        self.results_grid = ft.ResponsiveRow(
            spacing=10,
            run_spacing=10,
        )
        
        # Кнопка для возврата вверх
        self.scroll_to_top_button = ft.FloatingActionButton(
            icon=ft.Icons.ARROW_UPWARD,
            bgcolor=COLORS["scroll_top_bg"],
            tooltip="Вернуться вверх",
            on_click=lambda e: self.page.scroll_to(0),
            visible=True
        )
        
        # Добавление компонентов на страницу
        self.page.add(
            ft.Container(
                content=ft.Column([
                    header,
                    search_form,
                    ft.Container(
                        content=ft.Column([
                            self.results_header,
                            self.results_grid
                        ]),
                        padding=ft.padding.only(top=PADDING["medium"], bottom=PADDING["large"])
                    )
                ]),
                expand=True
            ),
            self.scroll_to_top_button
        )
    
    def _update_progress(self, message: str):
        """Обновление индикатора прогресса"""
        if not self.form_controls or not self.page:
            return
            
        self.form_controls["progress_text"].value = message
        self.form_controls["progress_text"].visible = True
        self.form_controls["progress_ring"].visible = True
        self.page.update()
    
    def _open_search_url(self, e):
        """Открытие URL поиска в браузере"""
        search_url = self.address_viewmodel.get_search_url()
        if search_url:
            webbrowser.open(search_url)
    
    def _perform_search(self, e, region_dropdown, district_field, sovet_field,
                       city_type_dropdown, city_field, 
                       street_type_dropdown, street_field, 
                       house_field, progress_ring, progress_text):
        """Выполнение поиска адреса"""
        # Проверяем, не выполняется ли уже поиск
        if self.address_viewmodel.is_searching:
            return
        
        # Установка параметров поиска
        self.address_viewmodel.set_search_params(
            region=region_dropdown.value,
            district=district_field.value.strip() if district_field.value else "",
            sovet=sovet_field.value.strip() if sovet_field.value else "",
            city_type=city_type_dropdown.value,
            city_name=city_field.value.strip() if city_field.value else "",
            street_type=street_type_dropdown.value,
            street_name=street_field.value.strip() if street_field.value else "",
            building=house_field.value.strip() if house_field.value else ""
        )
        
        # Отключаем кнопку поиска
        self.form_controls["search_button"].disabled = True
        if self.page:
            self.page.update()
        
        # Показываем индикатор прогресса
        progress_ring.visible = True
        progress_text.visible = True
        progress_text.value = "Выполняется поиск..."
        if self.page:
            self.page.update()
        
        # Выполнение поиска
        self.address_viewmodel.search_address(
            progress_callback=self._update_progress
        )
    
    def _update_search_state(self):
        """Обновление состояния поиска в UI"""
        if not self.form_controls or not self.page:
            return
            
        self.form_controls["search_button"].disabled = self.address_viewmodel.is_searching
        
        if not self.address_viewmodel.is_searching:
            self.form_controls["progress_ring"].visible = False
            self.form_controls["progress_text"].visible = False
            
        if self.page:
            self.page.update()
    
    def _update_search_query(self):
        """Обновление строки поискового запроса в UI"""
        if not self.page:
            return
            
        self.results_header.disabled = not self.address_viewmodel.current_search_query
        self.results_header.text = f"Результаты поиска: {self.address_viewmodel.current_search_query}"
        
        if self.page:
            self.page.update()
    
    def _show_error(self):
        """Отображение ошибки в UI"""
        if not self.page:
            return
            
        if self.address_viewmodel.error_message:
            self.page.snack_bar = ft.SnackBar(content=ft.Text(self.address_viewmodel.error_message))
            self.page.snack_bar.open = True
            self.page.update()
    
    def _display_results(self):
        """Отображение результатов поиска в UI"""
        if not self.page:
            return
            
        # Очистка предыдущих результатов
        self.results_grid.controls.clear()
        
        results = self.address_viewmodel.results
        
        if not results:
            # Если результатов нет, показываем сообщение
            self.results_grid.controls.append(
                ft.Container(
                    content=ft.Card(
                        content=ft.Container(
                            content=ft.Text(
                                "Адреса не найдены. Попробуйте изменить запрос.",
                                size=16,
                                color=ft.Colors.ORANGE
                            ),
                            padding=20
                        )
                    ),
                    col={"sm": 12}  # На маленьких экранах занимает всю ширину
                )
            )
            if self.page:
                self.page.update()
            return
        
        # Ограничиваем до 9 результатов для сетки 3x3
        results = results[:9]
        
        # Отображение результатов с ранжированием в адаптивной сетке
        for i, result in enumerate(results):
            rank = i + 1  # Ранг начинается с 1
            result_card = create_result_card(result, rank)
            
            # Добавляем карточку в адаптивную сетку
            # col=4 означает 3 карточки в ряд (12/4=3) на больших экранах
            # col=6 означает 2 карточки в ряд (12/6=2) на средних экранах
            # col=12 означает 1 карточка в ряд на маленьких экранах
            self.results_grid.controls.append(
                ft.Container(
                    content=result_card,
                    padding=5,
                    col={"xs": 12, "sm": 6, "md": 6, "lg": 4, "xl": 4}
                )
            )
        
        # Обновляем страницу для отображения результатов
        if self.page:
            self.page.update()
        
        # Прокрутка к результатам
        if self.page:
            self.page.scroll_to(self.results_header)
    
    def _setup_window_events(self):
        """Настройка обработчиков событий окна"""
        def on_window_event(e):
            if e.data == "close":
                # Закрытие ViewModel и сервисов
                self.address_viewmodel.close()
                # Разрываем циклические ссылки при закрытии
                self._cleanup_references()
        
        self.page.on_window_event = on_window_event
    
    def _cleanup_references(self):
        """Очистка циклических ссылок"""
        # Очищаем ссылки на компоненты
        if hasattr(self, 'form_controls'):
            self.form_controls.clear()
        
        # Очищаем ссылки на результаты
        if hasattr(self, 'results_grid'):
            self.results_grid.controls.clear()
        
        # Очищаем ссылку на страницу
        self.page = None
        
        # Очищаем ссылки на ViewModel
        if hasattr(self, 'address_viewmodel'):
            self.address_viewmodel = None
        
        logger.info("Очищены ссылки главного представления")