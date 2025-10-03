import flet as ft
from models.search_result import SearchResult
from ui.assets.styles import COLORS, TEXT_SIZES, ICONS, get_result_card_style, get_rank_style

def _get_score_color(score: float):
    """Определяет цвет чипа на основе score совпадения"""
    if score >= 90:
        return COLORS["success"]  # Зеленый для отличного совпадения
    elif score >= 70:
        return COLORS["info"]     # Синий для хорошего совпадения
    elif score >= 50:
        return COLORS["warning"]  # Оранжевый для среднего совпадения
    else:
        return COLORS["error"]     # Красный для слабого совпадения

def _create_status_chips(result: SearchResult):
    """Создает чипы со статусом совпадения и score"""
    chips = []
    
    # Статус совпадения дома
    if result.house_match:
        chips.append(ft.Chip(
            label=ft.Text("🏠 Точное совпадение дома", size=TEXT_SIZES["small"]),
            bgcolor=COLORS["success"]
        ))
    elif result.similarity_score > 0:
        chips.append(ft.Chip(
            label=ft.Text("❓ Дом не найден", size=TEXT_SIZES["small"]),
            bgcolor=COLORS["warning"]
        ))
    
    # Score совпадения
    if result.similarity_score > 0:
        chips.append(ft.Chip(
            label=ft.Text(f"🎯 Score: {result.similarity_score:.1f}%", size=TEXT_SIZES["small"]),
            bgcolor=_get_score_color(result.similarity_score)
        ))
    
    return ft.Row(
        chips,
        wrap=True,
        spacing=8,
        visible=len(chips) > 0
    )

def create_result_card(result: SearchResult, rank: int = 0) -> ft.Card:
    """
    Создает карточку с результатом поиска
    
    Args:
        result: Объект с данными результата поиска
        rank: Порядковый номер результата (1-9)
        
    Returns:
        ft.Card: Карточка результата
    """
    
    card_style = get_result_card_style(result.house_match, result.similarity_score)
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
                    )
                ]),
                
                # Статус совпадения и score
                _create_status_chips(result),
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
                    ft.Text(f"Диапазон домов Белпочты: {result.house_numbers}", size=TEXT_SIZES["body"])
                ]),
                
                # Дополнительная информация о статусе дома
                ft.Container(
                    content=ft.Text(
                        f"📋 {'✅ Дом найден в диапазоне' if result.house_match else '❌ Дом не найден в диапазоне домов'}",
                        size=TEXT_SIZES["small"],
                        color=COLORS["success"] if result.house_match else COLORS["warning"],
                        weight=ft.FontWeight.W_500,
                        text_align=ft.TextAlign.CENTER
                    ),
                    alignment=ft.alignment.center,
                    visible=result.similarity_score > 0
                )
            ]),
            padding=card_style["padding"],
            bgcolor=card_style["bgcolor"],
            border_radius=card_style["border_radius"]
        ),
        elevation=3 if rank <= 3 else 1  # Выделяем топ-3 результата тенью
    )