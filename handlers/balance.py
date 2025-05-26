from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command  # <-- Добавьте этот импорт
from states import Form
from utils.database import execute, fetchone
from keyboards import main_menu, cancel_button

router = Router()

@router.message(Command("setbalance"))
async def set_balance_start(message: types.Message, state: FSMContext):
    await state.set_state(Form.SET_BALANCE)
    await message.answer("Введите ваш текущий баланс:", reply_markup=cancel_button())

@router.message(Form.SET_BALANCE)
async def set_balance_finish(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())
    
    try:
        balance = float(message.text)
        execute("UPDATE users SET balance = ? WHERE user_id = ?", 
               (balance, message.from_user.id))
        await message.answer(f"✅ Баланс установлен: {balance} ₽", reply_markup=main_menu())
    except ValueError:
        await message.answer("❌ Введите число!")
    await state.clear()

@router.message(Command("balance"))
async def show_balance(message: types.Message):
    balance = fetchone("SELECT balance FROM users WHERE user_id = ?", 
                      (message.from_user.id,))[0]
    await message.answer(f"🏦 Текущий баланс: {balance} ₽")