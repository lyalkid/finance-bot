from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram import types
from typing import Optional

def main_menu() -> types.ReplyKeyboardMarkup:
    """Главное меню с основными командами"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="/balance"),
        types.KeyboardButton(text="/add_income"),
    )
    builder.row(
        types.KeyboardButton(text="/add_expense"),
        types.KeyboardButton(text="/categories"),
    )
    builder.row(
        types.KeyboardButton(text="/add_wish"),
        types.KeyboardButton(text="/wishlist"),
    )
    builder.row(
        types.KeyboardButton(text="/delete_wish"),
        types.KeyboardButton(text="/deletecategory"),
    )
    return builder.as_markup(resize_keyboard=True)


def cancel_button() -> types.ReplyKeyboardMarkup:
    """Кнопка отмены действия"""
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def category_type_keyboard() -> types.ReplyKeyboardMarkup:
    """Клавиатура выбора типа категории (доход/расход)"""
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Доход"), types.KeyboardButton(text="Расход")],
            [types.KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )


def dynamic_list_keyboard(items: list[str], cancel: bool = True) -> types.ReplyKeyboardMarkup:
    """Динамическая клавиатура для списков (категории, желания)"""
    builder = ReplyKeyboardBuilder()
    for item in items:
        builder.add(types.KeyboardButton(text=item))
    if cancel:
        builder.add(types.KeyboardButton(text="❌ Отмена"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def wishlist_pagination(page: int, total_pages: int) -> types.InlineKeyboardMarkup:
    """Инлайн-клавиатура для пагинации вишлиста"""
    builder = InlineKeyboardBuilder()
    
    if page > 1:
        builder.button(
            text="⬅️ Назад", 
            callback_data=f"wishlist_page_{page-1}"
        )
    if page < total_pages:
        builder.button(
            text="➡️ Вперед", 
            callback_data=f"wishlist_page_{page+1}"
        )
        
    return builder.as_markup()

def skip_button():
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="⏭ Пропустить")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )