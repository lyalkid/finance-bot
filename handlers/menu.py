from aiogram import Router, types, F
from aiogram.filters import Command

router = Router()

@router.message(Command("menu"))
async def show_main_menu(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="💰 Баланс", callback_data="menu_balance")],
        [types.InlineKeyboardButton(text="📂 Категории", callback_data="menu_categories")],
        [types.InlineKeyboardButton(text="➕ Доход / Расход", callback_data="menu_money")],
        [types.InlineKeyboardButton(text="🎯 Вишлист", callback_data="menu_wishlist")],
        [types.InlineKeyboardButton(text="📊 Отчёты", callback_data="menu_reports")],
        [types.InlineKeyboardButton(text="🧹 Удаление", callback_data="menu_delete")],
        [types.InlineKeyboardButton(text="ℹ️ Справка", callback_data="menu_help")]
    ])
    await message.answer("📋 Главное меню:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("menu_"))
async def menu_callback(callback: types.CallbackQuery):
    section = callback.data.split("_")[1]

    sections = {
        "balance": [
            "/balance – Текущий баланс",
            "/setbalance – Установить баланс"
        ],
        "categories": [
            "/categories – Все категории",
            "/addcategory – Добавить категорию",
            "/deletecategory – Удалить категорию"
        ],
        "money": [
            "/add_income – Добавить доход",
            "/add_expense – Добавить расход"
        ],
        "wishlist": [
            "/add_wish – Добавить желание",
            "/add_wishes – Массовое добавление",
            "/wishlist – Показать список",
            "/delete_wish – Удалить желание",
            "/buy_wish – Отметить как купленное"
            "/edit_wish – Изменить"
        ],
        "reports": [
            "/report – За период",
            "/monthly – За текущий месяц",
            "/compare – Сравнение месяцев"
        ],
        "delete": [
            "/delete_transactions – Удалить транзакции"
        ],
        "help": [
            "/help – Справка по всем командам"
        ]
    }

    text = "📎 Команды:\n" + "\n".join(sections.get(section, []))
    await callback.message.edit_text(text, reply_markup=None)
    await callback.answer()
