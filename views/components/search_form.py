import flet as ft
from db.models import StreetType, CityType

def create_search_form(on_search=None):
    """Создает форму поиска адреса"""
    
    # Компоненты формы
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
    
    # Привязка обработчика поиска, если он предоставлен
    if on_search:
        search_button.on_click = lambda e: on_search(
            e, 
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
        "city_type": city_type_dropdown,
        "city": city_field,
        "street_type": street_type_dropdown,
        "street": street_field,
        "house": house_field,
        "search_button": search_button,
        "progress_ring": progress_ring,
        "progress_text": progress_text
    }
