from datetime import datetime
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from data.config import ID
from aiogram import Router, F, types
from keyboards import inlinekeyboard_menu, keyboard_menu
from database.orm_query import orm_add_user

router = Router(name=__name__)


@router.message(Command(commands=['start']))
@router.callback_query(F.data == 'main')
async def start(event: types.Message | types.CallbackQuery, session: AsyncSession):
    if isinstance(event, types.Message):
        user = event.from_user
        await orm_add_user(session, user_id=user.id, first_name=user.first_name, last_name=user.last_name, phone=None)
        await event.answer(text="Добро пожаловать в наш магазин", reply_markup=inlinekeyboard_menu.inkb_start_menu)
    else:
        await event.message.edit_text(text="Добро пожаловать в наш магазин",
                                     reply_markup=inlinekeyboard_menu.inkb_start_menu)


@router.message(Command(commands=['help']))
async def help_handler(message: types.Message):
    await message.answer(f'Поддержка: @callmesud0')


@router.message(F.photo)
async def photo_id(message: types.Message):
    await message.answer(message.photo[-1].file_id)
