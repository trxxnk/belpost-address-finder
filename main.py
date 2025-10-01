import flet as ft
from ui.main_view import MainView

def main(page: ft.Page):
    """
    Точка входа в приложение.
    Создает главное представление и инициализирует интерфейс.
    """
    MainView(page)

if __name__ == "__main__":
    ft.app(target=main)
