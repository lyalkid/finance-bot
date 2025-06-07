from aiogram import Router, types
from aiogram.filters import Command
from utils.database import execute
from keyboards import main_menu

router = Router()

@router.message(Command("start", "help"))
async def start(message: types.Message):
    execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
    await message.answer(
        "💰 Финансовый менеджер\n\n"
        "Основные команды:\n"
        "/setbalance - установить баланс\n"
        "/addcategory - добавить категорию\n"
        "/deletecategory - удалить категорию\n"
        "/balance - текущий баланс\n"
        "/add_income - добавить доход\n"
        "/add_income_list - массовое добавление доходов\n"
        "/add_expense - добавить расход\n"
        "/add_expense_list - массовое добавление расходов\n"
        "/delete_transactions - удаление транзакций\n"
        "/report - отчёт за период\n"
        "/monthly - автоотчёт за месяц\n"
        "/compare - сравнение месяцев\n"
        "/categories - мои категории\n"
        "/add_wish - добавить желание\n"
        "/add_wishes - массовое добавление желаний\n"
        "/wishlist - список желаний\n"
        "/delete_wish - удалить желание\n"
        "/buy_wish - купить желание из вишлиста\n"
        "/edit_wish - редактировать желание\n"
        "/history - история транзакций\n"
        "/help - справка\n"
        "/menu - показать меню\n",
        reply_markup=main_menu()
    )
