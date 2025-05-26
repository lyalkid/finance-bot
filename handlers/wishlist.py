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
    
    # Добавляем общую сумму только на первой странице
    if page == 1:
        total_target = fetchone(
            "SELECT SUM(target_amount) FROM wishes WHERE user_id = ?",
            (user_id,)
        )[0] or 0
        text += f"💰 Общая сумма целей: {total_target:.2f} ₽\n\n"
    
    for title, target in wishes:
        progress = min(balance / target, 1.0)
        percent = int(progress * 100)
        filled = int(progress * 10)
        progress_bar = "🟩" * filled + "⬜️" * (10 - filled)
        
        text += (
            f"🎯 {title}\n"
            f"Цель: {target:.2f} ₽\n"
            f"Прогресс: {percent}% {progress_bar}\n"
            f"Осталось: {max(target - balance, 0):.2f} ₽\n\n"
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