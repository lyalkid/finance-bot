from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from typing import Optional

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu() -> ReplyKeyboardMarkup:
    """Главное меню с основными командами"""
    return ReplyKeyboardMarkup(
        keyboard=[
            # 💰 Баланс
            [KeyboardButton(text="/balance"), KeyboardButton(text="/setbalance")],

            # 📂 Категории
            [KeyboardButton(text="/categories")],
            [KeyboardButton(text="/addcategory"), KeyboardButton(text="/deletecategory")],

            # ➕ Доходы и расходы
            [KeyboardButton(text="/add_income"), KeyboardButton(text="/add_expense")],
            [KeyboardButton(text="/add_income_list"), KeyboardButton(text="/add_expense_list")],  # добавлено массовое добавление

            # 🎯 Желания
            [KeyboardButton(text="/add_wish"), KeyboardButton(text="/wishlist")],
            [KeyboardButton(text="/add_wishes"), KeyboardButton(text="/delete_wish")],
            [KeyboardButton(text="/buy_wish"), KeyboardButton(text="/edit_wish")],

            # 📊 Отчёты
            [KeyboardButton(text="/report"), KeyboardButton(text="/monthly"), KeyboardButton(text="/compare")],

            # 📜 История
            [KeyboardButton(text="/history")],

            # 🧹 Удаление
            [KeyboardButton(text="/delete_transactions")],

            # ℹ️ Справка и меню
            [KeyboardButton(text="/help"), KeyboardButton(text="/menu")]
        ],
        resize_keyboard=True
    )


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

def sort_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Сначала дешёвые"), 
             KeyboardButton(text="Сначала дорогие")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
