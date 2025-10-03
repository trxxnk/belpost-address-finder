import flet as ft
from models.dropdown_values import StreetType, CityType, RegionType
from core.address_service import AddressService
from logger import get_configured_logger

logger = get_configured_logger("addr_corr.views.components.search_form")


def create_search_form(on_search=None, on_parse=None):
    """
    Создает форму поиска адреса
    
    Args:
        on_search: Функция обработки поиска
        on_parse: Функция обработки парсинга адреса
    """
    
    # Инициализация сервиса для парсинга адресов
    address_service = AddressService()
    
    # Поле для ввода полного адреса
    full_address_field = ft.TextField(
        label="Введите полный адрес",
        hint_text="Например: город Минск, ул. Мира, 42а",
        width=600,
        multiline=False,
    )
    
    # Кнопка для парсинга адреса
    parse_button = ft.ElevatedButton(
        text="Разобрать адрес",
        icon=ft.Icons.PAGES,
        tooltip="Автоматически заполнить поля на основе введенного адреса"
    )
    
    # Компоненты формы
    # Область
    region_dropdown = ft.Dropdown(
        label="Область",
        options=[ft.dropdown.Option(key=rt.value, text=rt.value) for rt in RegionType],
        width=200,
        value=RegionType.NONE.value
    )
    
    # Район
    district_field = ft.TextField(
        label="Район",
        width=300,
        disabled=True
    )
    
    # Сельсовет
    sovet_field = ft.TextField(
        label="Сельсовет",
        width=300,
        disabled=True
    )
    
    # Тип населенного пункта
    city_type_dropdown = ft.Dropdown(
        label="Тип населенного пункта",
        options=[ft.dropdown.Option(key=ct.value, text=ct.value) for ct in CityType],
        width=200,
        value=CityType.NONE.value
    )
    
    # Название населенного пункта
    city_field = ft.TextField(
        label="Название населенного пункта",
        width=300,
        disabled=True
    )
    
    # Тип улицы
    street_type_dropdown = ft.Dropdown(
        label="Тип улицы",
        options=[ft.dropdown.Option(key=st.value, text=st.value) for st in StreetType],
        width=200,
        value=StreetType.NONE.value
    )
    
    # Название улицы
    street_field = ft.TextField(
        label="Название улицы",
        width=300,
        disabled=True
    )
    
    # Номер дома
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
    
    # Функции для управления состоянием полей
    def on_region_change(e):
        check = region_dropdown.value == RegionType.NONE.value
        district_field.disabled = check
        if district_field.disabled:
            district_field.value = ""
        sovet_field.disabled = check
        if sovet_field.disabled:
            sovet_field.value = ""
        e.page.update()
    
    def on_city_type_change(e):
        city_field.disabled = city_type_dropdown.value == CityType.NONE.value
        if city_field.disabled:
            city_field.value = ""
        e.page.update()
    
    def on_street_type_change(e):
        # Если выбрано "ДРУГОЕ" или не "НЕТ", то поле ввода улицы доступно
        street_field.disabled = street_type_dropdown.value == StreetType.NONE.value
        if street_field.disabled:
            street_field.value = ""
        e.page.update()
    
    # Функция для парсинга адреса и заполнения полей
    def parse_address(e):
        address = full_address_field.value
        if not address:
            e.page.add(ft.SnackBar(content=ft.Text("Введите адрес для разбора")))
            e.page.update()
            return
        
        # Очищаем все поля формы при нажатии кнопки "Разобрать"
        region_dropdown.value = RegionType.NONE.value
        district_field.value = ""
        district_field.disabled = True
        sovet_field.value = ""
        sovet_field.disabled = True
        city_type_dropdown.value = CityType.NONE.value
        city_field.value = ""
        city_field.disabled = True
        street_type_dropdown.value = StreetType.NONE.value
        street_field.value = ""
        street_field.disabled = True
        house_field.value = ""
        e.page.update()
        
        # Показываем индикатор прогресса
        progress_ring.visible = True
        progress_text.value = "Разбор адреса..."
        progress_text.visible = True
        e.page.update()
        
        try:
            # Используем AddressService для парсинга адреса
            parsed_data = address_service.parse_and_fill_address(address)
            
            if parsed_data:
                if "region" in parsed_data and parsed_data["region"]:
                    region_value, _ = parsed_data["region"].split(" ")
                    region_dropdown.value = region_value.upper()
                    on_region_change(e)  # Активируем поля района и сельсовета
                    e.page.update()
                
                # Обработка района
                if "district" in parsed_data and parsed_data["district"] and not district_field.disabled:
                    district_field.value = parsed_data["district"].title()

                # Обработка сельсовета
                if "sovet" in parsed_data and parsed_data["sovet"] and not sovet_field.disabled:
                    sovet_field.value = parsed_data["sovet"].title()
                
                # Обработка типа города
                if "city_type" in parsed_data and parsed_data["city_type"]:
                    city_type_dropdown.value = parsed_data["city_type"]
                    on_city_type_change(e)  # Активируем поле города
                
                # Обработка названия города
                if "city_name" in parsed_data and parsed_data["city_name"] and not city_field.disabled:
                    city_field.value = parsed_data["city_name"].title()
                
                # Обработка типа улицы
                if "street_type" in parsed_data and parsed_data["street_type"]:
                    street_type_dropdown.value = parsed_data["street_type"]
                    on_street_type_change(e)  # Активируем поле улицы
                
                # Обработка названия улицы
                if "street_name" in parsed_data and parsed_data["street_name"] and not street_field.disabled:
                    street_field.value = parsed_data["street_name"].title()
                
                # Обработка номера дома
                if "building" in parsed_data and parsed_data["building"]:
                    house_field.value = parsed_data["building"]
                
                e.page.add(ft.SnackBar(content=ft.Text("Адрес успешно разобран")))
            else:
                e.page.add(ft.SnackBar(content=ft.Text("Не удалось разобрать адрес")))
        
        except Exception as ex:
            logger.error(f"Исключение при разборе адреса: {ex}")
            e.page.add(ft.SnackBar(content=ft.Text(f"Ошибка при разборе адреса: {str(ex)}")))
        
        finally:
            # Скрываем индикатор прогресса
            progress_ring.visible = False
            progress_text.visible = False
            e.page.update()
    
    # Привязка обработчиков изменения значений
    region_dropdown.on_change = on_region_change
    city_type_dropdown.on_change = on_city_type_change
    street_type_dropdown.on_change = on_street_type_change
    
    # Привязка обработчика парсинга адреса
    parse_button.on_click = parse_address
    
    # Привязка обработчика поиска, если он предоставлен
    if on_search:
        search_button.on_click = lambda e: on_search(
            e, 
            region_dropdown,
            district_field,
            sovet_field,
            city_type_dropdown, 
            city_field, 
            street_type_dropdown, 
            street_field, 
            house_field,
            progress_ring,
            progress_text
        )
    
    # Создание формы
    search_form = ft.Card(
        content=ft.Container(
            content=ft.Column([
                # Секция ввода полного адреса
                ft.Container(
                    content=ft.Column([
                        ft.Text("Быстрый ввод адреса", size=16, weight=ft.FontWeight.BOLD),
                        ft.Row([
                            full_address_field,
                            parse_button
                        ]),
                        ft.Divider()
                    ]),
                    padding=ft.padding.only(bottom=10)
                ),
                
                # Секция детального ввода
                ft.Text("Детальный ввод", size=16, weight=ft.FontWeight.BOLD),
                ft.Row([
                    region_dropdown,
                    district_field
                ]),
                ft.Row([
                    sovet_field
                ]),
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
    )
    
    return search_form, {
        "full_address": full_address_field,
        "parse_button": parse_button,
        "region": region_dropdown,
        "district": district_field,
        "sovet": sovet_field,
        "city_type": city_type_dropdown,
        "city": city_field,
        "street_type": street_type_dropdown,
        "street": street_field,
        "house": house_field,
        "search_button": search_button,
        "progress_ring": progress_ring,
        "progress_text": progress_text
    }