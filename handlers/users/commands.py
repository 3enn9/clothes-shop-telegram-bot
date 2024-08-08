from datetime import datetime
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from data.config import ID
from aiogram import Router, F, types
from keyboards import inlinekeyboard_menu, keyboard_menu


router = Router(name=__name__)
tag_storage = {}


@router.message(Command(commands=['start']))
async def start(message: types.Message):
    await message.answer(text="Добро пожаловать в наш магазин", reply_markup=inlinekeyboard_menu.inkb_start_menu)


@router.message(Command(commands=['help']))
async def help_handler(message: types.Message):
    await message.answer(f'Поддержка: @callmesud0')


@router.message(F.photo)
async def photo_id(message: types.Message):
    await message.answer(message.photo[-1].file_id)