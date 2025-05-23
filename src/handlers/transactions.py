from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command  # <-- Добавьте этот импорт
from states import Form
from utils.database import execute, fetchone, fetchall
from keyboards import main_menu, cancel_button, dynamic_list_keyboard, skip_button


router = Router()

# ==================== Обработчики доходов ====================
@router.message(Command("add_income"))
async def add_income_start(message: types.Message, state: FSMContext):
    """Начало добавления дохода"""
    await state.set_state(Form.ADD_INCOME_AMOUNT)
    await message.answer("💰 Введите сумму дохода:", reply_markup=cancel_button())

@router.message(Form.ADD_INCOME_AMOUNT)
async def process_income_amount(message: types.Message, state: FSMContext):
    """Обработка суммы дохода"""
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())
    
    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            raise ValueError
        
        # Проверяем наличие категорий доходов
        categories = fetchall(
            "SELECT name FROM categories WHERE user_id = ? AND type = 'income'",
            (message.from_user.id,)
        )
        
        if not categories:
            await state.clear()
            return await message.answer("❌ Нет категорий доходов! Сначала создайте их через /addcategory")
        
        await state.update_data(amount=amount)
        await message.answer(
            "📋 Выберите категорию:",
            reply_markup=dynamic_list_keyboard([name for (name,) in categories])
        )
        await state.set_state(Form.ADD_INCOME_CATEGORY)
        
    except ValueError:
        await message.answer("❌ Введите корректную сумму!")

@router.message(Form.ADD_INCOME_CATEGORY)
async def process_income_category(message: types.Message, state: FSMContext):
    """Обработка категории дохода"""
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())
    
    # Проверяем существование категории
    category = fetchone(
        "SELECT id FROM categories WHERE user_id = ? AND name = ? AND type = 'income'",
        (message.from_user.id, message.text)
    )
    
    if not category:
        await state.clear()
        return await message.answer("❌ Категория не найдена!", reply_markup=main_menu())
    
    await state.update_data(category_id=category[0], category_name=message.text)
    await state.set_state(Form.ADD_INCOME_DESCRIPTION)
    await message.answer(
        "📝 Откуда доход? (Например: 'Аванс за проект')\n"
        "Можно пропустить ➡️",
        reply_markup=skip_button()
    )

@router.message(Form.ADD_INCOME_DESCRIPTION)
async def process_income_description(message: types.Message, state: FSMContext):
    """Обработка описания дохода"""
    data = await state.get_data()
    description = message.text if message.text != "⏭ Пропустить" else None
    
    try:
        # Добавляем транзакцию
        execute(
            """INSERT INTO transactions 
            (user_id, amount, category_id, description) 
            VALUES (?, ?, ?, ?)""",
            (message.from_user.id, data['amount'], data['category_id'], description)
        )
        
        # Обновляем баланс
        execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (data['amount'], message.from_user.id)
        )
        
        # Получаем новый баланс
        new_balance = fetchone(
            "SELECT balance FROM users WHERE user_id = ?",
            (message.from_user.id,)
        )[0]
        
        # Формируем сообщение
        response = (
            f"✅ Доход добавлен!\n"
            f"💵 Сумма: {data['amount']} ₽\n"
            f"📂 Категория: {data['category_name']}\n"
            f"🏦 Новый баланс: {new_balance} ₽"
        )
        
        if description:
            response += f"\n📝 Описание: {description}"
        
        await message.answer(response, reply_markup=main_menu())
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    finally:
        await state.clear()




# ==================== Обработчики расходов ====================
@router.message(Command("add_expense"))
async def add_expense_start(message: types.Message, state: FSMContext):
    """Начало добавления расхода"""
    await state.set_state(Form.ADD_EXPENSE_AMOUNT)
    await message.answer("💸 Введите сумму расхода:", reply_markup=cancel_button())

@router.message(Form.ADD_EXPENSE_AMOUNT)
async def process_expense_amount(message: types.Message, state: FSMContext):
    """Обработка суммы расхода"""
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())
    
    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            raise ValueError
        
        # Проверяем наличие категорий расходов
        categories = fetchall(
            "SELECT name FROM categories WHERE user_id = ? AND type = 'expense'",
            (message.from_user.id,)
        )
        
        if not categories:
            await state.clear()
            return await message.answer("❌ Нет категорий расходов! Сначала создайте их через /addcategory")
        
        await state.update_data(amount=amount)
        await message.answer(
            "📋 Выберите категорию:",
            reply_markup=dynamic_list_keyboard([name for (name,) in categories])
        )
        await state.set_state(Form.ADD_EXPENSE_CATEGORY)
        
    except ValueError:
        await message.answer("❌ Введите корректную сумму!")

@router.message(Form.ADD_EXPENSE_CATEGORY)
async def process_expense_category(message: types.Message, state: FSMContext):
    """Обработка категории расхода"""
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())
    
    # Проверяем существование категории
    category = fetchone(
        "SELECT id FROM categories WHERE user_id = ? AND name = ? AND type = 'expense'",
        (message.from_user.id, message.text))
    
    if not category:
        await state.clear()
        return await message.answer("❌ Категория не найдена!", reply_markup=main_menu())
    
    await state.update_data(category_id=category[0], category_name=message.text)
    await state.set_state(Form.ADD_EXPENSE_DESCRIPTION)
    await message.answer(
        "📝 На что потратили? (Например: 'Обед в кафе')\n"
        "Можно пропустить ➡️",
        reply_markup=skip_button()
    )

@router.message(Form.ADD_EXPENSE_DESCRIPTION)
async def process_expense_description(message: types.Message, state: FSMContext):
    """Обработка описания расхода"""
    data = await state.get_data()
    description = message.text if message.text != "⏭ Пропустить" else None
    
    try:
        # Добавляем транзакцию
        execute(
            """INSERT INTO transactions 
            (user_id, amount, category_id, description) 
            VALUES (?, ?, ?, ?)""",
            (message.from_user.id, data['amount'], data['category_id'], description)
        )
        
        # Обновляем баланс
        execute(
            "UPDATE users SET balance = balance - ? WHERE user_id = ?",
            (data['amount'], message.from_user.id)
        )
        
        # Получаем новый баланс
        new_balance = fetchone(
            "SELECT balance FROM users WHERE user_id = ?",
            (message.from_user.id,)
        )[0]
        
        # Формируем сообщение
        response = (
            f"✅ Расход добавлен!\n"
            f"💸 Сумма: {data['amount']} ₽\n"
            f"📂 Категория: {data['category_name']}\n"
            f"🏦 Новый баланс: {new_balance} ₽"
        )
        
        if description:
            response += f"\n📝 Описание: {description}"
        
        await message.answer(response, reply_markup=main_menu())
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    finally:
        await state.clear()