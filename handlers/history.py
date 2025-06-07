from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.database import fetchall, fetchone
from utils.formating import format_amount
from collections import defaultdict
from datetime import datetime

router = Router()

ITEMS_PER_PAGE = 10

@router.message(Command("history"))
async def show_history_start(message: types.Message):
    # При старте показываем выбор фильтра
    await send_filter_choice(message)

async def send_filter_choice(message: types.Message, page: int = 1):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📥 Все", callback_data=f"history_filter_all_{page}"),
            InlineKeyboardButton(text="➕ Доходы", callback_data=f"history_filter_income_{page}"),
            InlineKeyboardButton(text="➖ Расходы", callback_data=f"history_filter_expense_{page}"),
        ]
    ])
    await message.answer("Выберите тип транзакций для просмотра:", reply_markup=keyboard)

async def show_history_page(message: types.Message, user_id: int, page: int, filter_type: str = "all", edit: bool = False):
    offset = (page - 1) * ITEMS_PER_PAGE

    # Формируем условие фильтра
    if filter_type == "all":
        where_clause = "WHERE t.user_id = ?"
        params = (user_id, ITEMS_PER_PAGE, offset)
    else:
        where_clause = "WHERE t.user_id = ? AND c.type = ?"
        params = (user_id, filter_type, ITEMS_PER_PAGE, offset)

    query = f'''
        SELECT 
            t.amount,
            c.name as category,
            c.type,
            t.description,
            strftime('%d.%m.%Y', t.created_at) as date
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        {where_clause}
        ORDER BY t.created_at DESC
        LIMIT ? OFFSET ?
    '''

    transactions = fetchall(query, params)

    if filter_type == "all":
        total_count = fetchone("SELECT COUNT(*) FROM transactions WHERE user_id = ?", (user_id,))[0]
    else:
        total_count = fetchone("SELECT COUNT(*) FROM transactions t JOIN categories c ON t.category_id = c.id WHERE t.user_id = ? AND c.type = ?", (user_id, filter_type))[0]

    total_pages = (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE or 1

    if not transactions:
        return await message.answer("\U0001F4ED Нет транзакций.")

    grouped = defaultdict(list)
    total_income = 0.0
    total_expense = 0.0

    for amount, category, type_, description, date_str in transactions:
        grouped[date_str].append((float(amount), category, type_, description))

    lines = [f"\U0001F4DE История транзакций (стр. {page}/{total_pages}) — Фильтр: {filter_type}:\n"]

    for date_str in sorted(grouped.keys(), key=lambda d: datetime.strptime(d, "%d.%m.%Y"), reverse=True):
        lines.append(f"\n {date_str}")
        for amount, category, type_, description in grouped[date_str]:
            type_label = "Доход" if type_ == "income" else "Расход"
            lines.append(f"  {type_label:<6} | {category:<30} | {format_amount(amount)} ₽")
            if description:
                lines.append(f"    📝 {description}")
            if type_ == 'income':
                total_income += amount
            else:
                total_expense += amount
    
    lines.append("\nИтоги:")
    lines.append(f"{'Общий доход':<20}: {format_amount(total_income)} ₽")
    lines.append(f"{'Общий расход':<20}: {format_amount(total_expense)} ₽")
    lines.append(f"{'Баланс':<20}: {format_amount(total_income - total_expense)} ₽")

    # Кнопки пагинации с сохранением фильтра
    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"history_page_{filter_type}_{page - 1}"))
    if page < total_pages:
        buttons.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"history_page_{filter_type}_{page + 1}"))

    markup = InlineKeyboardMarkup(inline_keyboard=[buttons] if buttons else [])

    if edit:
        await message.edit_text("\n".join(lines), reply_markup=markup)
    else:
        await message.answer("\n".join(lines), reply_markup=markup)


@router.callback_query(lambda c: c.data.startswith("history_filter_"))
async def handle_filter_selection(callback: types.CallbackQuery):
    # Формат callback_data: history_filter_{filter}_{page}
    _, _, filter_type, page_str = callback.data.split("_")
    page = int(page_str)
    await show_history_page(
        message=callback.message,
        user_id=callback.from_user.id,
        page=page,
        filter_type=filter_type,
        edit=True
    )
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("history_page_"))
async def handle_history_pagination(callback: types.CallbackQuery):
    # Формат callback_data: history_page_{filter}_{page}
    _, _, filter_type, page_str = callback.data.split("_")
    page = int(page_str)
    await show_history_page(
        message=callback.message,
        user_id=callback.from_user.id,
        page=page,
        filter_type=filter_type,
        edit=True
    )
    await callback.answer()
