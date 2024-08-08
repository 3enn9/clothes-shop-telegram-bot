__all__ = ("router",)

from aiogram import Router

from .admins import router as admins_router
from .users import router as users_router
from .group import router as group_router

router = Router(name=__name__)

router.include_routers(admins_router, users_router, group_router)
