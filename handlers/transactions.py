from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command  # <-- Добавьте этот импорт
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
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


@router.message(Command("add_income_list"))
async def start_income_list(message: types.Message, state: FSMContext):
    await state.set_state(Form.ADD_INCOME_LIST_DATE)
    await message.answer("📅 Введите дату доходов в формате ДД.ММ.ГГГГ:", reply_markup=cancel_button())


from datetime import datetime

@router.message(Form.ADD_INCOME_LIST_DATE)
async def receive_income_date(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())

    try:
        date = datetime.strptime(message.text, "%d.%m.%Y").date()
        await state.update_data(date=date.strftime("%Y-%m-%d"))
        await state.set_state(Form.ADD_INCOME_LIST_ITEMS)
        await message.answer(
            "📝 Введите список доходов в формате:\n"
            "`Категория - Сумма - Описание`\n"
            "Описание необязательно. Каждая строка — новый доход.\n\n"
            "Пример:\n"
            "Зарплата - 10000 - за май\n"
            "Фриланс - 5000",
            reply_markup=cancel_button()
        )
    except ValueError:
        await message.answer("❌ Неверный формат даты! Пример: 24.05.2025")

@router.message(Form.ADD_INCOME_LIST_ITEMS)
async def process_income_list(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())

    user_id = message.from_user.id
    data = await state.get_data()
    date_str = data["date"]
    lines = message.text.strip().split('\n')
    successes = 0
    errors = []

    for i, line in enumerate(lines, 1):
        try:
            parts = [p.strip() for p in line.split('-')]
            if len(parts) < 2:
                raise ValueError("Недостаточно данных")

            category, amount_str = parts[0], parts[1]
            description = parts[2] if len(parts) > 2 else None
            amount = float(amount_str.replace(',', '.'))

            category_id = fetchone(
                "SELECT id FROM categories WHERE user_id = ? AND name = ? AND type = 'income'",
                (user_id, category)
            )
            if not category_id:
                raise ValueError(f"Категория '{category}' не найдена")

            execute(
                "INSERT INTO transactions (user_id, amount, category_id, description, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, amount, category_id[0], description, date_str)
            )
            execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
            successes += 1
        except Exception as e:
            errors.append(f"Строка {i}: {str(e)}")

    result = f"✅ Добавлено доходов: {successes}\n"
    if errors:
        result += "❌ Ошибки:\n" + "\n".join(errors)

    await message.answer(result, reply_markup=main_menu())
    await state.clear()

# ==================== Удаление транзакций с выбором ====================
@router.message(Command("delete_transactions"))
async def start_delete_transactions(message: types.Message, state: FSMContext):
    transactions = fetchall(
        '''
        SELECT t.id, t.amount, c.name, c.type, t.description, strftime('%d.%m.%Y', t.created_at)
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        WHERE t.user_id = ?
        ORDER BY t.created_at DESC
        LIMIT 10
        ''',
        (message.from_user.id,)
    )

    if not transactions:
        return await message.answer("❌ Нет транзакций для удаления.")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    tx_map = {}

    for i, (tx_id, amount, category, type_, desc, date) in enumerate(transactions, 1):
        icon = "💵" if type_ == "income" else "💸"
        text = f"{i}. {date} | {icon} {category} - {amount} ₽"
        if desc:
            text += f" | 📝 {desc}"
        callback_data = f"toggle:{tx_id}"
        keyboard.inline_keyboard.append([InlineKeyboardButton(text=text, callback_data=callback_data)])
        tx_map[str(tx_id)] = False

    # Кнопка подтверждения
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="✅ Удалить выбранные", callback_data="confirm_delete")
    ])

    await state.set_state(Form.DELETE_MULTI_TRANSACTIONS)
    await state.update_data(tx_choices=tx_map)
    await message.answer("🗑 Выберите транзакции для удаления:", reply_markup=keyboard)

@router.callback_query(Form.DELETE_MULTI_TRANSACTIONS, lambda c: c.data.startswith("toggle:"))
async def toggle_transaction_selection(callback: CallbackQuery, state: FSMContext):
    tx_id = callback.data.split(":")[1]
    data = await state.get_data()
    tx_choices = data.get("tx_choices", {})

    if tx_id in tx_choices:
        tx_choices[tx_id] = not tx_choices[tx_id]
        await state.update_data(tx_choices=tx_choices)
        await callback.answer("Выбор обновлен")
    else:
        await callback.answer("Транзакция не найдена", show_alert=True)

@router.callback_query(Form.DELETE_MULTI_TRANSACTIONS, lambda c: c.data == "confirm_delete")
async def confirm_delete_multiple(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tx_choices = data.get("tx_choices", {})
    selected_ids = [int(tx_id) for tx_id, selected in tx_choices.items() if selected]

    if not selected_ids:
        return await callback.answer("❌ Ничего не выбрано", show_alert=True)

    deleted = 0
    for tx_id in selected_ids:
        tx = fetchone(
            "SELECT amount, c.type FROM transactions t JOIN categories c ON t.category_id = c.id WHERE t.id = ?",
            (tx_id,)
        )
        if not tx:
            continue
        amount, type_ = tx
        sign = 1 if type_ == "income" else -1

        execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
        execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount * sign, callback.from_user.id))
        deleted += 1

    await callback.message.edit_text(f"✅ Удалено транзакций: {deleted}", reply_markup=None)
    await state.clear()