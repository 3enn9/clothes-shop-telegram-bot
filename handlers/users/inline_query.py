from aiogram import Router, Bot, types
from sqlalchemy.ext.asyncio import AsyncSession

from clothes import clothes
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent, \
    LinkPreviewOptions, LabeledPrice, InlineQuery

from database.orm_query import orm_get_product_name
from keyboards.default import inlinekeyboard_menu

router = Router(name=__name__)


@router.inline_query(lambda query: query.query.startswith('cat_'))
async def process_inline_query(query: types.InlineQuery, session: AsyncSession, bot: Bot):
    name_product = query.query.split('_')[1]
    items = [InlineQueryResultArticle(id=str(product.id),
                                      input_message_content=InputTextMessageContent(
                                          message_text=f'{product.name}\n{product.description}\nЦена: {product.price}₽\nВыберите размер для добавления в корзину!',
                                          link_preview_options=LinkPreviewOptions(
                                              url=product.url_image)),
                                      title=f'{product.name} {product.price}₽',
                                      thumbnail_url=product.url_image,
                                      description=product.description,
                                      reply_markup=InlineKeyboardMarkup(row_width=3, inline_keyboard=[
                                          [
                                              InlineKeyboardButton(text='S', callback_data=f'buy_{product.id}_S'),
                                              InlineKeyboardButton(text='M', callback_data=f'buy_{product.id}_M'),
                                              InlineKeyboardButton(text='L', callback_data=f'buy_{product.id}_L')
                                          ],
                                          [
                                              InlineKeyboardButton(text='🛒Корзина', callback_data="Корзина")
                                          ],
                                          [
                                              InlineKeyboardButton(text='\U0001F519Назад', callback_data=f'Товары')
                                          ]
                                      ])) for product in
             await orm_get_product_name(session=session, product_name=name_product)]
    await bot.answer_inline_query(query.id, items)


@router.inline_query()
async def process_inline_query(query: types.InlineQuery):
    items = [InlineQueryResultArticle(id='1245',
                                      input_message_content=InputTextMessageContent(
                                          message_text='[Добро пожаловать в магазин!](https://i.ibb.co/dWJdGLB/photo-2024-07-27-08-31-17.jpg)',
                                          parse_mode='Markdown'
                                      ),
                                      title='Daily Wear',
                                      thumbnail_url='https://i.ibb.co/dWJdGLB/photo-2024-07-27-08-31-17.jpg',
                                      description='Магазин одежды',
                                      reply_markup=inlinekeyboard_menu.inkb_main_menu)]
    await query.answer(results=items, cache_time=1)
