import flet as ft
from models import StreetType, CityType, RegionType

def create_search_form(on_search=None):
    """Создает форму поиска адреса"""
    
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
    
    # Привязка обработчиков изменения значений
    region_dropdown.on_change = on_region_change
    city_type_dropdown.on_change = on_city_type_change
    street_type_dropdown.on_change = on_street_type_change
    
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