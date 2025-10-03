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
    # Цвета для ранжирования
    "gold": "#FFD700",
    "silver": "#C0C0C0",
    "bronze": "#CD7F32",
    # Цвета для кнопки возврата наверх
    "scroll_top_bg": ft.Colors.BLUE_GREY_100,
    "scroll_top_icon": ft.Colors.BLUE_GREY_800,
}

# Размеры текста
TEXT_SIZES = {
    "title": 24,
    "subtitle": 18,
    "body": 14,
    "small": 12,
    "rank": 16,
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
    "arrow_up": ft.Icons.ARROW_UPWARD,
    "rank": ft.Icons.STAR,
}

# Стили карточек
def get_result_card_style(is_match=False, similarity_score=None):
    """
    Возвращает стиль карточки на основе качества совпадения
    
    Args:
        is_match: Точное совпадение дома
        similarity_score: Score совпадения адреса
        
    Returns:
        dict: Стили карточки
    """
    # Определяем цвет фона на основе качества совпадения
    if is_match:
        bgcolor = COLORS["match_bg"]  # Зеленый для точного совпадения дома
    elif similarity_score and similarity_score >= 70:
        bgcolor = ft.Colors.BLUE_50   # Светло-синий для хорошего совпадения
    elif similarity_score and similarity_score >= 50:
        bgcolor = ft.Colors.ORANGE_50 # Светло-оранжевый для среднего совпадения
    else:
        bgcolor = COLORS["default_bg"]
    
    return {
        "bgcolor": bgcolor,
        "padding": PADDING["medium"],
        "border_radius": 10,
    }

# Стили для ранжирования
def get_rank_style(rank):
    """
    Возвращает стиль для отображения ранга результата
    
    Args:
        rank: Порядковый номер результата (1-9)
        
    Returns:
        dict: Словарь со стилями
    """
    if rank == 1:
        return {
            "color": COLORS["gold"],
            "icon": ICONS["rank"],
            "size": TEXT_SIZES["rank"],
            "weight": ft.FontWeight.BOLD,
        }
    elif rank == 2:
        return {
            "color": COLORS["silver"],
            "icon": ICONS["rank"],
            "size": TEXT_SIZES["rank"],
            "weight": ft.FontWeight.BOLD,
        }
    elif rank == 3:
        return {
            "color": COLORS["bronze"],
            "icon": ICONS["rank"],
            "size": TEXT_SIZES["rank"],
            "weight": ft.FontWeight.BOLD,
        }
    else:
        return {
            "color": ft.Colors.GREY,
            "icon": None,
            "size": TEXT_SIZES["small"],
            "weight": ft.FontWeight.NORMAL,
        }