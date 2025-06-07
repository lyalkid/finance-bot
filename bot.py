import os
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from utils.database import init_db
from handlers import (
    base_router,
    balance_router,
    categories_router,
    transactions_router,
    wishlist_router, 
    reports_router, 
    menu_router, 
    history_router 
)


 
# Загрузка переменных окружения
load_dotenv()

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()

# Регистрация всех роутеров
dp.include_router(base_router)
dp.include_router(balance_router)
dp.include_router(categories_router)
dp.include_router(transactions_router)
dp.include_router(wishlist_router)
dp.include_router(reports_router)
dp.include_router(menu_router)
dp.include_router(history_router)


from utils.database import execute

def update_transaction_date(old_date: str, new_date: str):
    """Обновляет все транзакции с заданной старой датой на новую"""
    execute(
        "UPDATE transactions SET created_at = ? WHERE created_at = ?",
        (new_date, old_date)
    )
update_transaction_date('2025-05-06', '2025-06-06')
update_transaction_date('2025-05-04', '2025-06-04')
update_transaction_date('2025-05-05', '2025-06-05')



if __name__ == "__main__":
    # Инициализация БД
    init_db()
    
    # Запуск бота
    print("Бот запущен! 🚀")
    dp.run_polling(bot)