import flet as ft

# Цвета приложения
COLORS = {
    "primary": ft.Colors.BLUE,
    "secondary": ft.Colors.ORANGE,
    "success": ft.Colors.GREEN,
    "warning": ft.Colors.ORANGE,
    "error": ft.Colors.RED,
    "info": ft.Colors.BLUE_100,
    "match_bg": ft.Colors.GREEN_50,
    "default_bg": ft.Colors.GREY_100,
}

# Размеры текста
TEXT_SIZES = {
    "title": 24,
    "subtitle": 18,
    "body": 14,
    "small": 12,
}

# Отступы
PADDING = {
    "small": 10,
    "medium": 20,
    "large": 30,
}

# Настройки окна
WINDOW = {
    "width": 1200,
    "height": 800,
    "title": "Поиск адресов Белпочта",
    "theme_mode": ft.ThemeMode.LIGHT,
}

# Иконки
ICONS = {
    "search": ft.Icons.SEARCH,
    "mail": ft.Icons.MAIL,
    "location": ft.Icons.LOCATION_ON,
    "map": ft.Icons.MAP,
    "city": ft.Icons.LOCATION_CITY,
    "street": ft.Icons.STREETVIEW,
    "home": ft.Icons.HOME,
}

# Стили карточек
def get_result_card_style(is_match=False):
    return {
        "bgcolor": COLORS["match_bg"] if is_match else COLORS["default_bg"],
        "padding": PADDING["medium"],
        "border_radius": 10,
    }
