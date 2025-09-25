import flet as ft
from assets.styles import COLORS, ICONS

def create_scroll_to_top_button(on_click=None):
    """
    Создает кнопку для прокрутки страницы вверх
    
    Args:
        on_click: Функция обработки нажатия
        
    Returns:
        ft.FloatingActionButton: Кнопка для прокрутки вверх
    """
    button = ft.FloatingActionButton(
        icon=ICONS["arrow_up"],
        bgcolor=COLORS["scroll_top_bg"],
        tooltip="Вернуться вверх",
        on_click=on_click,
        visible=False  # Изначально скрыта
    )
    
    return button
