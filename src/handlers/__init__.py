from .base import router as base_router
from .balance import router as balance_router
from .categories import router as categories_router
from .transactions import router as transactions_router
from .wishlist import router as wishlist_router
from .reports import router as reports_router

__all__ = [
    "base_router",
    "balance_router",
    "categories_router",
    "transactions_router",
    "wishlist_router",
    "reports_router"
]