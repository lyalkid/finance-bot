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
    await show_history_page(message=message, user_id=message.from_user.id, page=1)


async def show_history_page(message: types.Message, user_id: int, page: int, edit: bool = False):
    offset = (page - 1) * ITEMS_PER_PAGE

    transactions = fetchall('''
        SELECT 
            t.amount,
            c.name as category,
            c.type,
            t.description,
            strftime('%d.%m.%Y', t.created_at) as date
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        WHERE t.user_id = ?
        ORDER BY t.created_at DESC
        LIMIT ? OFFSET ?
    ''', (user_id, ITEMS_PER_PAGE, offset))

    total_count = fetchone("SELECT COUNT(*) FROM transactions WHERE user_id = ?", (user_id,))[0]
    total_pages = (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE or 1

    if not transactions:
        return await message.answer("\U0001F4ED Нет транзакций.")

    grouped = defaultdict(list)
    total_income = 0.0
    total_expense = 0.0

    for amount, category, type_, description, date_str in transactions:
        grouped[date_str].append((float(amount), category, type_, description))

    lines = [f"\U0001F4DE История транзакций (стр. {page}/{total_pages}):\n"]

    for date_str in sorted(grouped.keys(), key=lambda d: datetime.strptime(d, "%d.%m.%Y")):
        lines.append(f"\n {date_str}")
        for amount, category, type_, description in grouped[date_str]:
            type_label = "Доход" if type_ == "income" else "Расход"
            lines.append(f"  {type_label:<6} | {category:<30} | {format_amount(amount)} ₽")

            if type_ == 'income':
                total_income += amount
            else:
                total_expense += amount
    
    lines.append("\nИтоги:")
    lines.append(f"{'Общий доход':<20}: {format_amount(total_income)} ₽")
    lines.append(f"{'Общий расход':<20}: {format_amount(total_expense)} ₽")
    lines.append(f"{'Баланс':<20}: {format_amount(total_income - total_expense)} ₽")

    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"history_page_{page - 1}"))
    if page < total_pages:
        buttons.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"history_page_{page + 1}"))

    markup = InlineKeyboardMarkup(inline_keyboard=[buttons] if buttons else [])

    if edit:
        await message.edit_text("\n".join(lines), reply_markup=markup)
    else:
        await message.answer("\n".join(lines), reply_markup=markup)


@router.callback_query(lambda c: c.data.startswith("history_page_"))
async def handle_history_pagination(callback: types.CallbackQuery):
    page = int(callback.data.split("_")[-1])
    await show_history_page(
        message=callback.message,
        user_id=callback.from_user.id,
        page=page,
        edit=True
    )
    await callback.answer()
