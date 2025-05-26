import os
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from dotenv import load_dotenv
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("finance_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()

# ------------ Состояния ------------
class Form(StatesGroup):
    SET_BALANCE = State()
    ADD_CATEGORY_NAME = State()
    ADD_CATEGORY_TYPE = State()
    DELETE_CATEGORY = State()
    ADD_INCOME_AMOUNT = State()
    ADD_INCOME_CATEGORY = State()
    ADD_EXPENSE_AMOUNT = State()
    ADD_EXPENSE_CATEGORY = State()
    ADD_WISH_TITLE = State()
    ADD_WISH_AMOUNT = State()
    DELETE_WISH = State()
    WISHLIST_PAGINATION = State()
    ADD_WISHES_LIST = State()

# ------------ Вспомогательные функции ------------
def init_db():
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance REAL DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                type TEXT CHECK(type IN ('income', 'expense')),
                UNIQUE(user_id, name, type))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category_id INTEGER NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS wishes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                target_amount REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

def execute(query, args=()):
    try:
        conn = sqlite3.connect('finance.db')
        c = conn.cursor()
        c.execute(query, args)
        conn.commit()
        logger.debug(f"Executed query: {query} with args {args}")
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()

def fetchone(query, args=()):
    try:
        conn = sqlite3.connect('finance.db')
        c = conn.cursor()
        c.execute(query, args)
        result = c.fetchone()
        logger.debug(f"Fetched one: {result} for query {query}")
        return result
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()

def fetchall(query, args=()):
    try:
        conn = sqlite3.connect('finance.db')
        c = conn.cursor()
        c.execute(query, args)
        result = c.fetchall()
        logger.debug(f"Fetched all: {result} for query {query}")
        return result
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()

# ------------ Клавиатуры ------------
def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="/balance"))
    builder.add(types.KeyboardButton(text="/add_income"))
    builder.add(types.KeyboardButton(text="/add_expense"))
    builder.add(types.KeyboardButton(text="/categories"))
    builder.add(types.KeyboardButton(text="/add_wish"))
    builder.add(types.KeyboardButton(text="/wishlist"))
    builder.add(types.KeyboardButton(text="/delete_wish"))
    builder.add(types.KeyboardButton(text="/deletecategory"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def cancel_button():
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

# ------------ Обработчики команд ------------
@dp.message(Command("start", "help"))
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

@dp.message(Command("setbalance"))
async def set_balance_start(message: types.Message, state: FSMContext):
    await state.set_state(Form.SET_BALANCE)
    await message.answer("Введите ваш текущий баланс:", reply_markup=cancel_button())

@dp.message(Form.SET_BALANCE)
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

@dp.message(Command("balance"))
async def show_balance(message: types.Message):
    balance = fetchone("SELECT balance FROM users WHERE user_id = ?", 
                      (message.from_user.id,))[0]
    await message.answer(f"🏦 Текущий баланс: {balance} ₽")

# ------------ Обработчики категорий ------------
@dp.message(Command("addcategory"))
async def add_category_start(message: types.Message, state: FSMContext):
    await state.set_state(Form.ADD_CATEGORY_TYPE)
    await message.answer(
        "Выберите тип категории:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="Доход"), types.KeyboardButton(text="Расход")],
                [types.KeyboardButton(text="❌ Отмена")]
            ],
            resize_keyboard=True
        )
    )

@dp.message(Form.ADD_CATEGORY_TYPE)
async def add_category_type(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())
    
    if message.text not in ["Доход", "Расход"]:
        return await message.answer("❌ Выберите тип из предложенных!")
    
    await state.update_data(category_type="income" if message.text == "Доход" else "expense")
    await state.set_state(Form.ADD_CATEGORY_NAME)
    await message.answer("Введите название категории:", reply_markup=cancel_button())

@dp.message(Form.ADD_CATEGORY_NAME)
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

@dp.message(Command("deletecategory"))
async def delete_category_start(message: types.Message, state: FSMContext):
    categories = fetchall('''SELECT name FROM categories 
                           WHERE user_id = ?''',
                        (message.from_user.id,))
    
    if not categories:
        return await message.answer("❌ У вас нет категорий для удаления!")
    
    keyboard = ReplyKeyboardBuilder()
    for (name,) in categories:
        keyboard.add(types.KeyboardButton(text=name))
    keyboard.add(types.KeyboardButton(text="❌ Отмена"))
    keyboard.adjust(2)
    
    await state.set_state(Form.DELETE_CATEGORY)
    await message.answer("Выберите категорию для удаления:",
                        reply_markup=keyboard.as_markup(resize_keyboard=True))

@dp.message(Form.DELETE_CATEGORY)
async def process_delete_category(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())
    
    category = fetchone('''SELECT id FROM categories 
                         WHERE user_id = ? AND name = ?''',
                      (message.from_user.id, message.text))
    
    if category:
        execute("DELETE FROM categories WHERE id = ?", (category[0],))
        await message.answer(f"✅ Категория '{message.text}' удалена!", reply_markup=main_menu())
    else:
        await message.answer("❌ Категория не найдена!")
    
    await state.clear()

@dp.message(Command("categories"))
async def show_categories(message: types.Message):
    categories = fetchall('''SELECT name, type FROM categories 
                           WHERE user_id = ?''',
                        (message.from_user.id,))
    
    if not categories:
        return await message.answer("❌ У вас пока нет категорий!")
    
    text = "📂 Ваши категории:\n"
    for name, cat_type in categories:
        text += f"- {name} ({'доход' if cat_type == 'income' else 'расход'})\n"
    
    await message.answer(text)

# ------------ Обработчики операций ------------
@dp.message(Command("add_income"))
async def add_income_start(message: types.Message, state: FSMContext):
    await state.set_state(Form.ADD_INCOME_AMOUNT)
    await message.answer("Введите сумму дохода:", reply_markup=cancel_button())

@dp.message(Form.ADD_INCOME_AMOUNT)
async def add_income_amount(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())
    
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
        
        categories = fetchall('''SELECT name FROM categories 
                               WHERE user_id = ? AND type = 'income' ''',
                            (message.from_user.id,))
        
        if not categories:
            await state.clear()
            return await message.answer("❌ Нет категорий доходов! Сначала создайте их.")
        
        await state.update_data(amount=amount)
        keyboard = ReplyKeyboardBuilder()
        for (name,) in categories:
            keyboard.add(types.KeyboardButton(text=name))
        keyboard.add(types.KeyboardButton(text="❌ Отмена"))
        keyboard.adjust(2)
        
        await state.set_state(Form.ADD_INCOME_CATEGORY)
        await message.answer("Выберите категорию:", reply_markup=keyboard.as_markup(resize_keyboard=True))
    except ValueError:
        await message.answer("❌ Введите положительное число!")

@dp.message(Form.ADD_INCOME_CATEGORY)
async def add_income_category(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())
    
    data = await state.get_data()
    category = fetchone('''SELECT id FROM categories 
                         WHERE user_id = ? AND name = ? AND type = 'income' ''',
                      (message.from_user.id, message.text))
    
    if not category:
        await state.clear()
        return await message.answer("❌ Категория не найдена!", reply_markup=main_menu())
    
    execute('''INSERT INTO transactions (user_id, amount, category_id)
             VALUES (?, ?, ?)''',
          (message.from_user.id, data['amount'], category[0]))
    
    execute("UPDATE users SET balance = balance + ? WHERE user_id = ?",
          (data['amount'], message.from_user.id))
    
    balance = fetchone("SELECT balance FROM users WHERE user_id = ?",
                     (message.from_user.id,))[0]
    
    await message.answer(
        f"✅ Доход добавлен!\n"
        f"💵 Сумма: {data['amount']} ₽\n"
        f"📂 Категория: {message.text}\n"
        f"🏦 Новый баланс: {balance} ₽",
        reply_markup=main_menu()
    )
    await state.clear()

@dp.message(Command("add_expense"))
async def add_expense_start(message: types.Message, state: FSMContext):
    await state.set_state(Form.ADD_EXPENSE_AMOUNT)
    await message.answer("Введите сумму расхода:", reply_markup=cancel_button())

@dp.message(Form.ADD_EXPENSE_AMOUNT)
async def add_expense_amount(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())
    
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
        
        categories = fetchall('''SELECT name FROM categories 
                               WHERE user_id = ? AND type = 'expense' ''',
                            (message.from_user.id,))
        
        if not categories:
            await state.clear()
            return await message.answer("❌ Нет категорий расходов! Сначала создайте их.")
        
        await state.update_data(amount=amount)
        keyboard = ReplyKeyboardBuilder()
        for (name,) in categories:
            keyboard.add(types.KeyboardButton(text=name))
        keyboard.add(types.KeyboardButton(text="❌ Отмена"))
        keyboard.adjust(2)
        
        await state.set_state(Form.ADD_EXPENSE_CATEGORY)
        await message.answer("Выберите категорию:", reply_markup=keyboard.as_markup(resize_keyboard=True))
    except ValueError:
        await message.answer("❌ Введите положительное число!")

@dp.message(Form.ADD_EXPENSE_CATEGORY)
async def add_expense_category(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())
    
    data = await state.get_data()
    category = fetchone('''SELECT id FROM categories 
                         WHERE user_id = ? AND name = ? AND type = 'expense' ''',
                      (message.from_user.id, message.text))
    
    if not category:
        await state.clear()
        return await message.answer("❌ Категория не найдена!", reply_markup=main_menu())
    
    execute('''INSERT INTO transactions (user_id, amount, category_id)
             VALUES (?, ?, ?)''',
          (message.from_user.id, data['amount'], category[0]))
    
    execute("UPDATE users SET balance = balance - ? WHERE user_id = ?",
          (data['amount'], message.from_user.id))
    
    balance = fetchone("SELECT balance FROM users WHERE user_id = ?",
                     (message.from_user.id,))[0]
    
    await message.answer(
        f"✅ Расход добавлен!\n"
        f"💸 Сумма: {data['amount']} ₽\n"
        f"📂 Категория: {message.text}\n"
        f"🏦 Новый баланс: {balance} ₽",
        reply_markup=main_menu()
    )
    await state.clear()

# ------------ Обработчики wishlist ------------
@dp.message(Command("add_wish"))
async def add_wish_start(message: types.Message, state: FSMContext):
    await state.set_state(Form.ADD_WISH_TITLE)
    await message.answer("Введите название желаемой покупки:", reply_markup=cancel_button())

@dp.message(Form.ADD_WISH_TITLE)
async def process_wish_title(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())
    
    await state.update_data(title=message.text)
    await state.set_state(Form.ADD_WISH_AMOUNT)
    await message.answer("Введите стоимость покупки:", reply_markup=cancel_button())

@dp.message(Form.ADD_WISH_AMOUNT)
async def process_wish_amount(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())
    
    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            raise ValueError
        
        data = await state.get_data()
        execute('''INSERT INTO wishes (user_id, title, target_amount)
                 VALUES (?, ?, ?)''',
               (message.from_user.id, data['title'], amount))
        
        await message.answer(f"✅ Желание '{data['title']}' добавлено!", reply_markup=main_menu())
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите корректную сумму!")

    
    
   

ITEMS_PER_PAGE = 5

async def get_wishlist_page(user_id: int, page: int):
    offset = (page - 1) * ITEMS_PER_PAGE
    wishes = fetchall('''SELECT title, target_amount FROM wishes 
                      WHERE user_id = ? 
                      LIMIT ? OFFSET ?''',
                   (user_id, ITEMS_PER_PAGE, offset))
    
    total = fetchone("SELECT COUNT(*) FROM wishes WHERE user_id = ?", (user_id,))[0]
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    return wishes, total_pages

async def create_pagination_keyboard(page: int, total_pages: int):
    keyboard = InlineKeyboardBuilder()
    
    if page > 1:
        keyboard.add(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"wishlist_page_{page-1}"
        ))
    
    if page < total_pages:
        keyboard.add(InlineKeyboardButton(
            text="➡️ Вперед",
            callback_data=f"wishlist_page_{page+1}"
        ))
    
    return keyboard.as_markup()

@dp.message(Command("wishlist"))
async def show_wishlist(message: types.Message):
    await show_wishlist_page(message.from_user.id, 1, message)

async def show_wishlist_page(user_id: int, page: int, message: types.Message, edit: bool = False):
    balance = fetchone("SELECT balance FROM users WHERE user_id = ?", (user_id,))[0]
    wishes, total_pages = await get_wishlist_page(user_id, page)
    
    if not wishes:
        return await message.answer("Список желаний пуст 🌈")
    
    text = f"📋 Список желаний (Страница {page}/{total_pages}):\n\n"
    
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
    
    markup = await create_pagination_keyboard(page, total_pages)
    
    if edit:
        await message.edit_text(text, reply_markup=markup)
    else:
        await message.answer(text, reply_markup=markup)

@dp.callback_query(F.data.startswith("wishlist_page_"))
async def pagination_handler(callback: types.CallbackQuery):
    page = int(callback.data.split("_")[-1])
    await show_wishlist_page(callback.from_user.id, page, callback.message, edit=True)
    await callback.answer()

@dp.message(Command("delete_wish"))
async def delete_wish_start(message: types.Message, state: FSMContext):
    wishes = fetchall('''SELECT id, title FROM wishes 
                       WHERE user_id = ?''',
                    (message.from_user.id,))
    
    if not wishes:
        return await message.answer("❌ Список желаний пуст!")
    
    keyboard = ReplyKeyboardBuilder()
    for wish_id, title in wishes:
        keyboard.add(types.KeyboardButton(text=f"{title}"))
    keyboard.add(types.KeyboardButton(text="❌ Отмена"))
    keyboard.adjust(2)
    
    await state.set_state(Form.DELETE_WISH)
    await message.answer("Выберите желание для удаления:",
                        reply_markup=keyboard.as_markup(resize_keyboard=True))

@dp.message(Form.DELETE_WISH)
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

# Новый обработчик
@dp.message(Command("add_wishes"))
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

@dp.message(Form.ADD_WISHES_LIST)
async def process_wishes_list(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено", reply_markup=main_menu())
    
    lines = message.text.split('\n')
    successes = 0
    errors = []
    
    for i, line in enumerate(lines, 1):
        try:
            if '-' not in line:
                raise ValueError
                
            title, amount_str = line.split('-', 1)
            title = title.strip()
            amount = float(amount_str.strip())
            
            if amount <= 0:
                raise ValueError
                
            execute('''INSERT INTO wishes (user_id, title, target_amount)
                     VALUES (?, ?, ?)''',
                   (message.from_user.id, title, amount))
            successes += 1
        except Exception as e:
            errors.append(f"Строка {i}: {line}")
    
    await state.clear()
    
    result_message = f"✅ Успешно добавлено: {successes}\n"
    if errors:
        result_message += "\n❌ Ошибки в строках:\n" + '\n'.join(errors)
    
    await message.answer(result_message, reply_markup=main_menu())

if __name__ == "__main__":
    init_db()
    dp.run_polling(bot)