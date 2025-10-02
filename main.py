import flet as ft
from ui.main_view import MainView

def main(page: ft.Page):
    MainView(page)

if __name__ == "__main__":
    ft.app(target=main)
