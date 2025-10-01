import flet as ft
from assets.styles import COLORS, TEXT_SIZES, PADDING, ICONS

def create_header():
    """Создает заголовок приложения"""
    return ft.Container(
        content=ft.Row([
            ft.Icon(ICONS["mail"], size=40, color=COLORS["primary"]),
            ft.Text(
                "Поиск почтовых индексов Белпочта",
                size=TEXT_SIZES["title"],
                weight=ft.FontWeight.BOLD
            )
        ]),
        padding=ft.padding.only(bottom=PADDING["medium"])
    )
