import logging
import os

def setup_logger():
    """Конфигурация логгера"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("finance_bot.log"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    
    # Для SQLite логов
    sqlite_logger = logging.getLogger('sqlite3')
    sqlite_logger.setLevel(logging.WARNING)
    
    return logger

logger = setup_logger()