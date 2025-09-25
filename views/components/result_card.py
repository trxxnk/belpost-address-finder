import flet as ft
from models import SearchResult
from assets.styles import COLORS, TEXT_SIZES, ICONS, get_result_card_style, get_rank_style

def create_result_card(result: SearchResult, rank: int = 0) -> ft.Card:
    """
    Создает карточку с результатом поиска
    
    Args:
        result: Объект с данными результата поиска
        rank: Порядковый номер результата (1-9)
        
    Returns:
        ft.Card: Карточка результата
    """
    
    card_style = get_result_card_style(result.house_match)
    rank_style = get_rank_style(rank)
    
    # Создаем компонент для отображения ранга
    rank_container = ft.Container(
        content=ft.Row(
            [
                ft.Icon(rank_style["icon"], color=rank_style["color"]) if rank_style["icon"] else ft.Container(),
                ft.Text(
                    f"#{rank}",
                    size=rank_style["size"],
                    weight=rank_style["weight"],
                    color=rank_style["color"]
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=5
        ),
        margin=ft.margin.only(bottom=5),
        visible=rank > 0
    )
    
    return ft.Card(
        content=ft.Container(
            content=ft.Column([
                # Ранг результата
                rank_container,
                
                # Основная информация
                ft.Row([
                    ft.Text(
                        f"Почтовый индекс: {result.postal_code}",
                        size=TEXT_SIZES["subtitle"],
                        weight=ft.FontWeight.BOLD,
                        color=COLORS["primary"]
                    ),
                    ft.Chip(
                        label=ft.Text("Точное совпадение"),
                        bgcolor=COLORS["success"],
                        visible=result.house_match
                    ) if result.house_match else ft.Container(),
                    ft.Chip(
                        label=ft.Text(f"Схожесть: {result.similarity_score:.1f}%"),
                        bgcolor=COLORS["info"],
                        visible=result.similarity_score > 0
                    ) if result.similarity_score > 0 else ft.Container()
                ]),
                ft.Divider(),
                ft.Row([
                    ft.Icon(ICONS["location"], color=COLORS["error"]),
                    ft.Text(f"Регион: {result.region}", size=TEXT_SIZES["body"])
                ]),
                ft.Row([
                    ft.Icon(ICONS["map"], color=COLORS["secondary"]),
                    ft.Text(f"Район: {result.district}", size=TEXT_SIZES["body"])
                ]),
                ft.Row([
                    ft.Icon(ICONS["city"], color=COLORS["primary"]),
                    ft.Text(f"Город: {result.city}", size=TEXT_SIZES["body"])
                ]),
                ft.Row([
                    ft.Icon(ICONS["street"], color=COLORS["success"]),
                    ft.Text(f"Улица: {result.street}", size=TEXT_SIZES["body"])
                ]),
                ft.Row([
                    ft.Icon(ICONS["home"], color=ft.Colors.PURPLE),
                    ft.Text(f"Номера домов: {result.house_numbers}", size=TEXT_SIZES["body"])
                ]),
            ]),
            padding=card_style["padding"],
            bgcolor=card_style["bgcolor"],
            border_radius=card_style["border_radius"]
        ),
        elevation=3 if rank <= 3 else 1  # Выделяем топ-3 результата тенью
    )