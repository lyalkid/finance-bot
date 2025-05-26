from aiogram import Router, types
from aiogram.filters import Command  # <-- Добавьте этот импорт
from aiogram.fsm.context import FSMContext
from states import Form
from utils.database import execute, fetchall, fetchone
from keyboards import main_menu, cancel_button, category_type_keyboard, dynamic_list_keyboard

router = Router()

@router.message(Command("addcategory"))
async def add_category_start(message: types.Message, state: FSMContext):
    await state.set_state(Form.ADD_CATEGORY_TYPE)
    await message.answer(
        "Выберите тип категории:",
        reply_markup=category_type_keyboard()
    )

@router.message(Form.ADD_CATEGORY_TYPE)
async def add_category_type(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())
    
    if message.text not in ["Доход", "Расход"]:
        return await message.answer("❌ Выберите тип из предложенных!")
    
    await state.update_data(category_type="income" if message.text == "Доход" else "expense")
    await state.set_state(Form.ADD_CATEGORY_NAME)
    await message.answer("Введите название категории:", reply_markup=cancel_button())

@router.message(Form.ADD_CATEGORY_NAME)
async def add_category_name(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())
    
    data = await state.get_data()
    try:
        execute('''INSERT INTO categories (user_id, name, type)
                 VALUES (?, ?, ?)''',
               (message.from_user.id, message.text, data['category_type']))
        await message.answer(f"✅ Категория '{message.text}' добавлена!", reply_markup=main_menu())
    except sqlite3.IntegrityError:
        await message.answer("❌ Такая категория уже существует!")
    await state.clear()

@router.message(Command("categories"))
async def show_categories(message: types.Message):
    expenses = fetchall('''SELECT name, type FROM categories 
                           WHERE user_id = ? and type = 'expense'
                        ''',
                        (message.from_user.id,))
    incomes = fetchall('''SELECT name, type FROM categories 
                           WHERE user_id = ? and type = 'income'
                        ''',
                        (message.from_user.id,))
    if (not incomes and not expenses):
        return await message.answer("❌ У вас пока нет категорий!")
    
    text = "📂 Ваши категории:\n"
    if(incomes):
        text += "Доходы:\n"
        for name, cat_type in incomes:
            text += f"- {name} {''}\n"
        text += "---------------\n"

    if(expenses):
        for name, cat_type in expenses:
            text += f"- {name} {''}\n"
        

    await message.answer(text)

@router.message(Command("deletecategory"))
async def delete_category_start(message: types.Message, state: FSMContext):
    categories = fetchall(
        "SELECT name FROM categories WHERE user_id = ?",
        (message.from_user.id,)
    )
    
    if not categories:
        return await message.answer("❌ У вас пока нет категорий.")

    category_names = [name for (name,) in categories]

    await state.set_state(Form.DELETE_CATEGORY)
    await message.answer(
        "Выберите категорию для удаления:",
        reply_markup=dynamic_list_keyboard(category_names)
    )

@router.message(Form.DELETE_CATEGORY)
async def process_delete_category(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено.", reply_markup=main_menu())
    
    # Проверим наличие категории
    category = fetchone(
        "SELECT id FROM categories WHERE user_id = ? AND name = ?",
        (message.from_user.id, message.text)
    )
    if not category:
        return await message.answer("❌ Категория не найдена!")

    # Удалим
    execute("DELETE FROM categories WHERE id = ?", (category[0],))
    await state.clear()
    await message.answer(f"✅ Категория '{message.text}' удалена!", reply_markup=main_menu())
