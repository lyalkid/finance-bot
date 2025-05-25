import sqlite3
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

def init_db():
    """Инициализация структуры базы данных"""
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    
    try:
        # Пользователи
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    balance REAL DEFAULT 0)''')
        
        # Категории
        c.execute('''CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT CHECK(type IN ('income', 'expense')),
                    UNIQUE(user_id, name, type))''')
        
        # Транзакции
        c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount REAL NOT NULL,  
                    category_id INTEGER NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Вишлист
        c.execute('''CREATE TABLE IF NOT EXISTS wishes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    target_amount REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        conn.commit()
        logger.info("Database initialized successfully")
        
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
        raise
    finally:
        conn.close()

def execute(query: str, args: tuple = ()) -> None:
    """Выполнение запроса на запись"""
    try:
        conn = sqlite3.connect('finance.db')
        c = conn.cursor()
        c.execute(query, args)
        conn.commit()
        logger.debug(f"Executed: {query} | Args: {args}")
    except sqlite3.Error as e:
        logger.error(f"Execute error: {e} | Query: {query}")
        raise
    finally:
        conn.close()

def fetchone(query: str, args: tuple = ()) -> Optional[tuple]:
    """Получение одной записи"""
    try:
        conn = sqlite3.connect('finance.db')
        c = conn.cursor()
        c.execute(query, args)
        result = c.fetchone()
        logger.debug(f"Fetched one: {result} | Query: {query}")
        return result
    except sqlite3.Error as e:
        logger.error(f"Fetchone error: {e} | Query: {query}")
        raise
    finally:
        conn.close()

def fetchall(query: str, args: tuple = ()) -> List[Tuple]:
    """Получение всех записей"""
    try:
        conn = sqlite3.connect('finance.db')
        c = conn.cursor()
        c.execute(query, args)
        result = c.fetchall()
        logger.debug(f"Fetched {len(result)} rows | Query: {query}")
        return result
    except sqlite3.Error as e:
        logger.error(f"Fetchall error: {e} | Query: {query}")
        raise
    finally:
        conn.close()