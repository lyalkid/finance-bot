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
        "/add_expense - добавить расход\n"
        "/categories - мои категории\n"
        "/add_wish - добавить желание\n"
        "/wishlist - список желаний\n"
        "/delete_wish - удалить желание",
        reply_markup=main_menu()
    )