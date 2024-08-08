__all__ = ("router",)

from aiogram import Router
from .callbacks import router as inline_menu_router
from .commands import router as start_router
from .inline_query import router as inline_query_router

router = Router(name=__name__)

router.include_routers(
    inline_query_router,
    inline_menu_router,
    start_router
)