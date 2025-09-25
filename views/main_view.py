import flet as ft
from typing import List
import urllib.parse
import webbrowser
import threading
import time

from models import SearchResult
from services import AddressService
from assets.styles import PADDING, COLORS
from views.components import create_header, create_search_form, create_result_card, create_scroll_to_top_button
from models import RegionType, CityType, StreetType

class MainView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.address_service = AddressService()
        
        # Контейнер для результатов поиска
        self.results_container = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO
        )
        
        # Текущий поисковый запрос
        self.current_search_query = ""
        
        # Флаг, указывающий, выполняется ли поиск в данный момент
        self.is_searching = False
        
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
        
        # Кнопка для прокрутки вверх
        self.scroll_to_top_button = ft.FloatingActionButton(
            icon=ft.Icons.ARROW_UPWARD,
            bgcolor=COLORS["scroll_top_bg"],
            tooltip="Вернуться вверх",
            on_click=lambda e: self.page.scroll_to(0, duration=300),
            visible=False
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
                            self.results_container
                        ]),
                        padding=ft.padding.only(top=PADDING["medium"], bottom=PADDING["large"])
                    )
                ]),
                expand=True,  # Растягиваем контейнер на всю доступную ширину
                width=self.page.window.width - 40,  # Учитываем отступы страницы
            ),
            self.scroll_to_top_button
        )
        
        # # Обработчик прокрутки
        # def on_scroll(e):
        #     # Если прокручено вниз больше чем на 300 пикселей, показываем кнопку
        #     if self.page.scroll > 300:
        #         if not self.scroll_to_top_button.visible:
        #             self.scroll_to_top_button.visible = True
        #             self.page.update()
        #     else:
        #         if self.scroll_to_top_button.visible:
        #             self.scroll_to_top_button.visible = False
        #             self.page.update()
        
        # Устанавливаем обработчик прокрутки
        # self.page.on_scroll = on_scroll
    
    def _update_progress(self, message: str):
        """Обновление индикатора прогресса"""
        if not self.form_controls:
            return
            
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
        # Проверяем, не выполняется ли уже поиск
        if self.is_searching:
            return
            
        # Проверка наличия минимально необходимых данных для поиска
        has_city = city_type_dropdown.value != CityType.NONE.value and city_field.value and city_field.value.strip()
        has_street = street_type_dropdown.value != StreetType.NONE.value and street_field.value and street_field.value.strip()
        has_region = region_dropdown.value != RegionType.NONE.value
        has_district = district_field.value and district_field.value.strip()
        
        if not (has_city or has_street or has_region or has_district):
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Укажите хотя бы один параметр для поиска"))
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        # Устанавливаем флаг выполнения поиска
        self.is_searching = True
        
        # Очистка предыдущих результатов
        self.results_container.controls.clear()
        
        # Отключаем кнопку поиска
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
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Укажите хотя бы один параметр для поиска"))
                self.page.snack_bar.open = True
                self.page.update()
                self.is_searching = False
                self.form_controls["search_button"].disabled = False
                self.page.update()
                return
            
            # Сохраняем текущий поисковый запрос для генерации URL
            self.current_search_query = address_query
            
            # Активируем кнопку заголовка результатов
            self.results_header.disabled = False
            self.results_header.text = f"Результаты поиска: {address_query}"
            self.page.update()
            
            # Показываем индикатор прогресса
            progress_ring.visible = True
            progress_text.visible = True
            progress_text.value = "Выполняется поиск..."
            self.page.update()
            
            # Поиск
            results = self.address_service.search_address(
                address_query,
                progress_callback=self._update_progress
            )
            
            # Скрытие прогресса
            progress_ring.visible = False
            progress_text.visible = False
            self.page.update()
            
            # Отображение результатов
            self._display_results(results)
            
        except Exception as e:
            # Обработка ошибок
            progress_ring.visible = False
            progress_text.visible = False
            
            error_card = ft.Card(
                content=ft.Container(
                    content=ft.Text(
                        f"Ошибка при поиске: {str(e)}",
                        size=16,
                        color=ft.Colors.RED
                    ),
                    padding=20
                )
            )
            
            self.results_container.controls.append(error_card)
            self.page.update()
            
        finally:
            # Сбрасываем флаг выполнения поиска
            self.is_searching = False
            
            # Разблокируем кнопку поиска
            self.form_controls["search_button"].disabled = False
            self.page.update()
    
    def _display_results(self, results: List[SearchResult]):
        """Отображение результатов поиска в сетке 3x3"""
        if not results:
            # Если результатов нет, показываем сообщение
            self.results_container.controls.append(
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
            self.page.update()
            return
        
        # Ограничиваем до 9 результатов для сетки 3x3
        results = results[:9]
        
        # Вычисляем доступную ширину для карточек
        # Вычитаем отступы страницы и отступы между карточками
        available_width = self.page.width - 40  # Отступы страницы 20px с каждой стороны
        card_width = (available_width - 40) / 3  # 20px отступ между карточками (2 отступа на 3 карточки)
        
        # Создаем сетку 3x3
        grid_rows = []
        current_row = []
        
        for i, result in enumerate(results):
            rank = i + 1  # Ранг начинается с 1
            result_card = create_result_card(result, rank)
            
            # Ограничиваем ширину карточки
            card_container = ft.Container(
                content=result_card,
                width=card_width,
                margin=ft.margin.only(right=10, bottom=10)
            )
            
            # Добавляем карточку в текущую строку
            current_row.append(card_container)
            
            # Если строка содержит 3 карточки или это последний результат, добавляем строку в сетку
            if len(current_row) == 3 or i == len(results) - 1:
                # Если в последней строке меньше 3 карточек, добавляем пустые контейнеры
                while len(current_row) < 3:
                    current_row.append(ft.Container(width=card_width))
                
                # Добавляем строку в сетку
                grid_rows.append(
                    ft.Row(
                        controls=current_row,
                        alignment=ft.MainAxisAlignment.START,
                        spacing=10
                    )
                )
                
                # Начинаем новую строку
                current_row = []
        
        # Добавляем все строки в контейнер результатов
        for row in grid_rows:
            self.results_container.controls.append(row)
        
        # Обновляем страницу
        self.page.update()
        
        # Прокручиваем к результатам с небольшой задержкой
        def delayed_scroll():
            time.sleep(0.3)  # Небольшая задержка для завершения рендеринга
            self.page.scroll_to(self.results_header, duration=300)
            self.page.update()
        
        # Запускаем прокрутку в отдельном потоке
        threading.Thread(target=delayed_scroll).start()
    
    def _setup_window_events(self):
        """Настройка обработчиков событий окна"""
        def on_window_event(e):
            if e.data == "close":
                self.address_service.close()
        
        self.page.on_window_event = on_window_event