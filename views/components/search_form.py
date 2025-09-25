import flet as ft
import re
from rapidfuzz import fuzz, process
from models import StreetType, CityType, RegionType
from services.postal_client import PostalClient

def create_search_form(on_search=None, on_parse=None):
    """
    Создает форму поиска адреса
    
    Args:
        on_search: Функция обработки поиска
        on_parse: Функция обработки парсинга адреса
    """
    
    # Инициализация клиента для парсинга адресов
    postal_client = PostalClient()
    
    # Поле для ввода полного адреса
    full_address_field = ft.TextField(
        label="Введите полный адрес",
        hint_text="Например: город Минск ул. Октябрьская д 10/2",
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
            # Вызов микросервиса для парсинга адреса
            # Предобработка: заменяем сокращения на полные слова
            abbr_replace_dict = {
                r"(?<!\w)г\.?(?!\w)": "город",
                r"(?<!\w)обл\.?(?!\w)": "область",
                r"(?<!\w)р-н(?!\w)": "район",
                r"(?<!\w)рн(?!\w)": "район",
                # r"(?<!\w)д\.?(?!\w)": "деревня",
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
                # r"(?<!\w)дом(?!\w)": "дом",
            }
            preprocessed_address = address
            for pattern, replacement in abbr_replace_dict.items():
                preprocessed_address = re.sub(pattern, replacement, preprocessed_address, flags=re.IGNORECASE)
            parsed_address = postal_client.parse_address(preprocessed_address)
            
            if parsed_address:
                # Обработка области (state)
                if "state" in parsed_address:
                    # Очищаем значение от слов "область", "обл." и т.д.
                    oblast_raw = parsed_address["state"]
                    oblast_clean = re.sub(r"(?<!\w)(область|обл\.?)(?!\w)", "", oblast_raw, flags=re.IGNORECASE).strip()
                    
                    # Словарь соответствия областей и их значений в перечислении
                    oblast_mapping = {
                        "минск": "МИНСКАЯ",
                        "брест": "БРЕСТСКАЯ",
                        "витебск": "ВИТЕБСКАЯ",
                        "гомель": "ГОМЕЛЬСКАЯ",
                        "гродно": "ГРОДНЕНСКАЯ",
                        "могилев": "МОГИЛЕВСКАЯ"
                    }
                    
                    # Определяем область по ключевым словам
                    for key, value in oblast_mapping.items():
                        if key in oblast_clean.lower():
                            region_dropdown.value = value
                            on_region_change(e)  # Активируем поля района и сельсовета
                            break
                
                # Обработка района (state_district)
                if "state_district" in parsed_address and not district_field.disabled:
                    district_raw = parsed_address["state_district"]
                    # Удаляем слова "район", "р-н", "рн"
                    district_clean = re.sub(r"(?<!\w)(район|р-н|рн)\.?(?!\w)", "", district_raw, flags=re.IGNORECASE).strip()
                    district_field.value = district_clean.title()  # Первая буква заглавная
                
                # Обработка города (city)
                if "city" in parsed_address:
                    city_raw = parsed_address["city"]
                    
                    # Определяем тип населенного пункта по ключевым словам
                    city_type_mapping = {
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
                    
                    city_type_detected = None
                    for pattern, city_type in city_type_mapping.items():
                        if re.search(pattern, city_raw, re.IGNORECASE):
                            city_type_detected = city_type
                            break
                    
                    # Если тип не определен, но город - один из областных центров
                    if not city_type_detected:
                        major_cities = ["минск", "брест", "витебск", "гомель", "гродно", "могилев"]
                        if any(city in city_raw.lower() for city in major_cities):
                            city_type_detected = "ГОРОД"
                    
                    # Если тип определен, устанавливаем его
                    if city_type_detected:
                        city_type_dropdown.value = city_type_detected
                        on_city_type_change(e)  # Активируем поле города
                    else:
                        # Если тип не определен, но есть название города, используем "ДРУГОЕ"
                        city_type_dropdown.value = "ДРУГОЕ" if hasattr(CityType, "OTHER") else "ГОРОД"
                        on_city_type_change(e)
                    
                    # Очищаем название города от типа
                    for pattern in city_type_mapping.keys():
                        city_raw = re.sub(pattern, "", city_raw, flags=re.IGNORECASE).strip()
                    
                    # Устанавливаем название города
                    if not city_field.disabled:
                        city_field.value = city_raw.title()  # Первая буква заглавная
                
                # Обработка улицы (road)
                if "road" in parsed_address:
                    road_raw = parsed_address["road"]
                    
                    # Определяем тип улицы по ключевым словам
                    street_type_mapping = {
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
                    
                    street_type_detected = None
                    for pattern, street_type in street_type_mapping.items():
                        if re.search(pattern, road_raw, re.IGNORECASE):
                            street_type_detected = street_type
                            break
                    
                    # Если тип определен, устанавливаем его
                    if street_type_detected:
                        street_type_dropdown.value = street_type_detected
                        on_street_type_change(e)  # Активируем поле улицы
                    else:
                        # Если тип не определен, но есть название улицы, используем "ДРУГОЕ"
                        street_type_dropdown.value = "ДРУГОЕ" if hasattr(StreetType, "OTHER") else "УЛИЦА"
                        on_street_type_change(e)
                    
                    # Очищаем название улицы от типа
                    for pattern in street_type_mapping.keys():
                        road_raw = re.sub(pattern, "", road_raw, flags=re.IGNORECASE).strip()
                    
                    # Устанавливаем название улицы
                    if not street_field.disabled:
                        street_field.value = road_raw.title()  # Первая буква заглавная
                
                # Обработка номера дома (house_number)
                if "house_number" in parsed_address:
                    house_number = parsed_address["house_number"]
                    # Удаляем слова "дом", "д.", "д"
                    house_clean = re.sub(r"(?<!\w)(дом|д\.?)(?!\w)", "", house_number, flags=re.IGNORECASE).strip()
                    house_field.value = house_clean
                
                e.page.add(ft.SnackBar(content=ft.Text("Адрес успешно разобран")))
            else:
                e.page.add(ft.SnackBar(content=ft.Text("Не удалось разобрать адрес")))
        
        except Exception as ex:
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