from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from states import Form
from aiogram.filters import Command  # <-- Добавьте этот импорт
from utils.database import execute, fetchone, fetchall
from keyboards import (
    main_menu,
    cancel_button,
    dynamic_list_keyboard,
    wishlist_pagination
)
from typing import List, Tuple
# Где-то в начале файла (например, после импортов)
def format_amount(amount: float) -> str:
    """Форматирует число с разделителем тысяч и двумя знаками после запятой"""
    return "{:,.2f}".format(amount).replace(",", " ").replace(".", ",")

router = Router()
ITEMS_PER_PAGE = 5

# ------------------- Добавление желаний -------------------
@router.message(Command("add_wish"))
async def add_wish_start(message: types.Message, state: FSMContext):
    await state.set_state(Form.ADD_WISH_TITLE)
    await message.answer("Введите название желаемой покупки:", reply_markup=cancel_button())

@router.message(Form.ADD_WISH_TITLE)
async def process_wish_title(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())
    
    await state.update_data(title=message.text)
    await state.set_state(Form.ADD_WISH_DESCRIPTION)
    await message.answer("Что это? добавь описание, зачем тебя эта покупка ?", reply_markup=cancel_button())

@router.message(Form.ADD_WISH_DESCRIPTION)
async def process_with_description(message: types.Message, state:FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())
    await state.update_data(description=message.text)
    await state.set_state(Form.ADD_WISH_AMOUNT)
    await message.answer("Введите стоимость покупки:", reply_markup=cancel_button())



@router.message(Form.ADD_WISH_AMOUNT)
async def process_wish_amount(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())
    
    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            raise ValueError
        
        data = await state.get_data()
        execute('''INSERT INTO wishes (user_id, title, description, target_amount)
                 VALUES (?, ?, ?, ?)''',
               (message.from_user.id, data['title'], data['description'], amount))
        
        await message.answer(f"✅ Желание '{data['title']}' добавлено!", reply_markup=main_menu())
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите корректную сумму!")

# ------------------- Просмотр вишлиста -------------------
async def get_wishlist_page(user_id: int, page: int) -> Tuple[List[Tuple], int]:
    offset = (page - 1) * ITEMS_PER_PAGE
    wishes = fetchall('''SELECT title, target_amount FROM wishes 
                      WHERE user_id = ? 
                      ORDER BY target_amount ASC
                      LIMIT ? OFFSET ?''',
                   (user_id, ITEMS_PER_PAGE, offset))
    
    total = fetchone("SELECT COUNT(*) FROM wishes WHERE user_id = ?", (user_id,))[0]
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    return wishes, total_pages

@router.message(Command("wishlist"))
async def show_wishlist(message: types.Message):
    await show_wishlist_page(
        user_id=message.from_user.id,
        page=1,
        message=message
    )

async def show_wishlist_page(
    user_id: int, 
    page: int, 
    message: types.Message, 
    edit: bool = False
):
    balance = fetchone("SELECT balance FROM users WHERE user_id = ?", (user_id,))[0]
    wishes, total_pages = await get_wishlist_page(user_id, page)
    
    if not wishes:
        return await message.answer("Список желаний пуст 🌈")
    
    text = f"📋 Список желаний (Страница {page}/{total_pages}):\n\n"
    
    if page == 1:
        total_target = fetchone(
            "SELECT SUM(target_amount) FROM wishes WHERE user_id = ?",
            (user_id,)
        )[0] or 0
        # Форматируем общую сумму
        text += f"💰 Общая сумма целей: {format_amount(total_target)} ₽\n\n"
    
    for title, target in wishes:
        progress = min(balance / target, 1.0)
        percent = int(progress * 100)
        filled = int(progress * 10)
        progress_bar = "🟩" * filled + "⬜️" * (10 - filled)
        
        # Форматируем отдельные суммы
        formatted_target = format_amount(target)
        formatted_remaining = format_amount(max(target - balance, 0))
        
        text += (
            f"🎯 {title}\n"
            f"Цель: {formatted_target} ₽\n"
            f"Прогресс: {percent}%\n {progress_bar}\n"
            f"Осталось: {formatted_remaining} ₽\n\n"
        )
    
    markup = wishlist_pagination(page, total_pages)
    
    if edit:
        await message.edit_text(text, reply_markup=markup)
    else:
        await message.answer(text, reply_markup=markup)

@router.callback_query(F.data.startswith("wishlist_page_"))
async def pagination_handler(callback: types.CallbackQuery):
    page = int(callback.data.split("_")[-1])
    await show_wishlist_page(
        user_id=callback.from_user.id,
        page=page,
        message=callback.message,
        edit=True
    )
    await callback.answer()

# ------------------- Удаление желаний -------------------
@router.message(Command("delete_wish"))
async def delete_wish_start(message: types.Message, state: FSMContext):
    wishes = fetchall('''SELECT title FROM wishes 
                       WHERE user_id = ?''',
                    (message.from_user.id,))
    
    if not wishes:
        return await message.answer("❌ Список желаний пуст!")
    
    await state.set_state(Form.DELETE_WISH)
    await message.answer(
        "Выберите желание для удаления:",
        reply_markup=dynamic_list_keyboard([title for (title,) in wishes])
    )

@router.message(Form.DELETE_WISH)
async def process_delete_wish(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())
    
    wish = fetchone('''SELECT id FROM wishes 
                     WHERE user_id = ? AND title = ?''',
                  (message.from_user.id, message.text))
    
    if wish:
        execute("DELETE FROM wishes WHERE id = ?", (wish[0],))
        await message.answer(f"✅ Желание '{message.text}' удалено!", reply_markup=main_menu())
    else:
        await message.answer("❌ Желание не найдено!")
    
    await state.clear()

# ------------------- Массовое добавление -------------------
@router.message(Command("add_wishes"))
async def add_wishes_start(message: types.Message, state: FSMContext):
    await state.set_state(Form.ADD_WISHES_LIST)
    await message.answer(
        "📝 Введите список желаний в формате:\n"
        "Название - Сумма\n"
        "Каждое желание с новой строки\n\n"
        "Пример:\n"
        "Ноутбук - 100000\n"
        "Велосипед - 50000\n"
        "Путешествие - 200000",
        reply_markup=cancel_button()
    )

@router.message(Form.ADD_WISHES_LIST)
async def process_wishes_list(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())
    
    lines = message.text.split('\n')
    successes = 0
    errors = []
    
    for i, line in enumerate(lines, 1):
        try:
            title_part, amount_part = line.split('-', 1)
            title = title_part.strip()
            amount = float(amount_part.strip())
            
            if amount <= 0:
                raise ValueError
                
            execute('''INSERT INTO wishes (user_id, title, target_amount)
                     VALUES (?, ?, ?)''',
                   (message.from_user.id, title, amount))
            successes += 1
        except Exception:
            errors.append(f"Строка {i}: {line}")
    
    await state.clear()
    result = f"✅ Успешно добавлено: {successes}\n"
    if errors:
        result += "\n❌ Ошибки в строках:\n" + '\n'.join(errors)

    await message.answer(result, reply_markup=main_menu())
    

# from keyboards import dynamic_list_keyboard, cancel_button, main_menu

from keyboards import dynamic_list_keyboard, cancel_button, main_menu
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Старт выбора желания для редактирования (inline)
@router.message(Command("edit_wish"))
async def edit_wish_start(message: types.Message, state: FSMContext):
    wishes = fetchall("SELECT id, title FROM wishes WHERE user_id = ?", (message.from_user.id,))
    if not wishes:
        return await message.answer("❌ Список желаний пуст!")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=title, callback_data=f"edit_select_{wish_id}")]
        for wish_id, title in wishes
    ])
    await state.set_state(Form.EDIT_WISH_SELECT)
    await message.answer("Выберите желание для редактирования:", reply_markup=keyboard)

# Обработка выбора желания (inline)
@router.callback_query(Form.EDIT_WISH_SELECT)
async def edit_wish_choice(callback: types.CallbackQuery, state: FSMContext):
    if not callback.data.startswith("edit_select_"):
        return await callback.answer("❌ Некорректный выбор")

    wish_id = int(callback.data.split("_")[-1])
    wish = fetchone("SELECT * FROM wishes WHERE user_id = ? AND id = ?", (callback.from_user.id, wish_id))
    if not wish:
        await state.clear()
        return await callback.answer("❌ Желание не найдено", show_alert=True)

    await state.update_data(wish_id=wish_id)
    await state.set_state(Form.EDIT_WISH_CHOICE)

    fields = ["✏️ Название", "💬 Описание", "💰 Сумму", "🧾 Всё сразу", "✅ Завершить"]
    await callback.message.answer("Что хотите изменить?", reply_markup=dynamic_list_keyboard(fields))
    await callback.answer()

# Выбор поля редактирования (reply)
@router.message(Form.EDIT_WISH_CHOICE)
async def handle_edit_field_choice(message: types.Message, state: FSMContext):
    text = message.text.strip()

    if text == "✏️ Название":
        await state.set_state(Form.EDIT_WISH_TITLE)
        await message.answer("Введите новое название:", reply_markup=cancel_button())
    elif text == "💬 Описание":
        await state.set_state(Form.EDIT_WISH_DESCRIPTION)
        await message.answer("Введите новое описание:", reply_markup=cancel_button())
    elif text == "💰 Сумму":
        await state.set_state(Form.EDIT_WISH_AMOUNT)
        await message.answer("Введите новую сумму:", reply_markup=cancel_button())
    elif text == "🧾 Всё сразу":
        await state.set_state(Form.EDIT_WISH_ALL)
        await message.answer("Введите через новую строку:\n1. Название\n2. Описание\n3. Сумма", reply_markup=cancel_button())
    elif text == "✅ Завершить":
        await state.clear()
        await message.answer("Редактирование завершено ✅", reply_markup=main_menu())
    else:
        await message.answer("❌ Пожалуйста, выберите вариант из списка.")

# Обновление названия
@router.message(Form.EDIT_WISH_TITLE)
async def edit_title(message: types.Message, state: FSMContext):
    data = await state.get_data()
    execute("UPDATE wishes SET title = ? WHERE id = ?", (message.text.strip(), data['wish_id']))

    await state.set_state(Form.EDIT_WISH_CHOICE)
    fields = ["✏️ Название", "💬 Описание", "💰 Сумму", "🧾 Всё сразу", "✅ Завершить"]
    await message.answer("✅ Название обновлено! Что хотите изменить ещё?", reply_markup=dynamic_list_keyboard(fields))

# Обновление описания
@router.message(Form.EDIT_WISH_DESCRIPTION)
async def edit_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    execute("UPDATE wishes SET description = ? WHERE id = ?", (message.text.strip(), data['wish_id']))

    await state.set_state(Form.EDIT_WISH_CHOICE)
    fields = ["✏️ Название", "💬 Описание", "💰 Сумму", "🧾 Всё сразу", "✅ Завершить"]
    await message.answer("✅ Описание обновлено! Что хотите изменить ещё?", reply_markup=dynamic_list_keyboard(fields))

# Обновление суммы
@router.message(Form.EDIT_WISH_AMOUNT)
async def edit_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            raise ValueError

        data = await state.get_data()
        execute("UPDATE wishes SET target_amount = ? WHERE id = ?", (amount, data['wish_id']))

        await state.set_state(Form.EDIT_WISH_CHOICE)
        fields = ["✏️ Название", "💬 Описание", "💰 Сумму", "🧾 Всё сразу", "✅ Завершить"]
        await message.answer("✅ Сумма обновлена! Что хотите изменить ещё?", reply_markup=dynamic_list_keyboard(fields))

    except ValueError:
        await message.answer("❌ Введите корректную сумму!")

# Обновление всех полей
@router.message(Form.EDIT_WISH_ALL)
async def edit_all(message: types.Message, state: FSMContext):
    try:
        lines = message.text.strip().split('\n')
        if len(lines) < 3:
            raise ValueError

        title = lines[0].strip()
        description = lines[1].strip()
        amount = float(lines[2].replace(',', '.'))

        if amount <= 0:
            raise ValueError

        data = await state.get_data()
        execute("UPDATE wishes SET title = ?, description = ?, target_amount = ? WHERE id = ?",
                (title, description, amount, data['wish_id']))

        await message.answer("✅ Все поля обновлены!", reply_markup=main_menu())
    except Exception:
        await message.answer("❌ Ошибка формата. Введите 3 строки:\n1. Название\n2. Описание\n3. Сумма")
    finally:
        await state.clear()
