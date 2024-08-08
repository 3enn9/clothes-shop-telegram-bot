from aiogram import types, F, Router, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, InlineQueryResultArticle, \
    InputTextMessageContent, LinkPreviewOptions, InputMediaPhoto
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Cart, Product
from database.orm_query import orm_add_user, orm_add_to_cart, orm_delete_from_cart, orm_reduce_product_in_cart, \
    orm_clear_cart
from keyboards import inlinekeyboard_menu, keyboard_menu

router = Router(name=__name__)


@router.callback_query(F.data == 'О нас')
async def about_us(callback_query: types.CallbackQuery, bot: Bot):
    await bot.edit_message_text(text='Мы небольшая компания, которая только набирает свою популярность и '
                                     'старается предложить лучший сервис для наших клиентов. Спасибо, что выбрали нас!',
                                inline_message_id=callback_query.inline_message_id,
                                reply_markup=inlinekeyboard_menu.inkb_back_main_menu)


@router.callback_query(F.data == 'Магазин')
async def main_menu(callback_query: types.CallbackQuery, bot: Bot):
    await bot.edit_message_text(
        text='[Добро пожаловать в наш магазин!](https://i.ibb.co/dWJdGLB/photo-2024-07-27-08-31-17.jpg)',
        inline_message_id=callback_query.inline_message_id,
        reply_markup=inlinekeyboard_menu.inkb_main_menu,
        parse_mode='Markdown',
    )


@router.callback_query(F.data == 'Товары')
async def choose_category(callback_query: types.CallbackQuery, bot: Bot):
    await bot.edit_message_text(text='[Категории](https://i.ibb.co/dWJdGLB/photo-2024-07-27-08-31-17.jpg)',
                                inline_message_id=callback_query.inline_message_id,
                                reply_markup=inlinekeyboard_menu.inkb_items,
                                parse_mode='Markdown',
                                )


@router.callback_query(F.data == 'Корзина')
async def basket(callback_query: types.CallbackQuery, bot: Bot, session: AsyncSession):
    query_cart = select(Cart).where(Cart.user_id == callback_query.from_user.id)
    result_cart = await session.execute(query_cart)
    cart_items = result_cart.scalars().all()
    if not cart_items:
        await bot.edit_message_text(
            text='[Ваша корзина пуста]',
            inline_message_id=callback_query.inline_message_id,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text='Назад', callback_data='Магазин')]]),
            parse_mode='Markdown'
        )
        return
    product_ids = [item.product_id for item in cart_items]

    query_products = select(Product).where(Product.id.in_(product_ids))
    result_products = await session.execute(query_products)
    products = {product.id: product for product in result_products.scalars().all()}
    cost = 0

    cart_text = "Товары в корзине:\n\n"
    for index, item in enumerate(cart_items):
        product = products.get(item.product_id)
        if product:
            total_price = item.quantity * product.price
            cost += total_price
            cart_text += f"{index + 1}. {product.name}, Размер: {item.size} {item.quantity}шт. - {total_price} руб.\n"
    cart_text += f'\nИтого по счету: {cost} руб.'

    await bot.edit_message_text(
        text=f'[Корзина]\n\n{cart_text}',
        inline_message_id=callback_query.inline_message_id,
        reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
        [InlineKeyboardButton(text='Перейти к оплате', callback_data=f"Оплата_{cost}")],
        [InlineKeyboardButton(text='Редактор заказа', callback_data="Редактировать корзину")],
        [InlineKeyboardButton(text='\U0001F519В меню', callback_data='Магазин')]
    ]
),
        parse_mode='Markdown'
    )


@router.callback_query(F.data.startswith('buy_'))
async def add_in_basket(callback_query: types.CallbackQuery, session: AsyncSession):
    user = callback_query.from_user
    product_id = int(callback_query.data.split('_')[1])
    size = callback_query.data.split('_')[2]
    await orm_add_user(session, user_id=user.id, first_name=user.first_name, last_name=user.last_name, phone=None)
    await orm_add_to_cart(session, user_id=user.id, product_id=product_id, size=size)
    await callback_query.answer(text=f'Товар успешно добавлен в корзину',
                                show_alert=True)


@router.callback_query(F.data == "Редактировать корзину")
async def remove_from_basket(callback_query: types.CallbackQuery, session: AsyncSession, bot: Bot):
    user_id = callback_query.from_user.id
    query_cart = select(Cart).where(Cart.user_id == user_id)
    result_cart = await session.execute(query_cart)
    cart_items = result_cart.scalars().all()

    if not cart_items:
        await bot.edit_message_text(
            text=f'Ваша корзина пуста',
            inline_message_id=callback_query.inline_message_id,
            parse_mode='Markdown')
        return

    product_ids = [item.product_id for item in cart_items]
    query_products = select(Product).where(Product.id.in_(product_ids))
    result_products = await session.execute(query_products)
    products = {product.id: product for product in result_products.scalars().all()}

    buttons = [
        [InlineKeyboardButton(text=f"{products[item.product_id].name} {item.size} {item.quantity} шт.",
                              callback_data=f"remove_{item.product_id}_{item.size}")]
        for item in cart_items
    ]

    buttons.append([InlineKeyboardButton(text="Назад", callback_data="Корзина")])

    await bot.edit_message_text(
        text=f'Выберите товар для редактирования',
        inline_message_id=callback_query.inline_message_id,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode='Markdown'
    )


@router.callback_query(F.data.startswith('remove_'))
async def remove_product(callback_query: types.CallbackQuery, session: AsyncSession, bot: Bot):
    user = callback_query.from_user
    size = callback_query.data.split('_')[2]
    product_id = int(callback_query.data.split('_')[1])

    await orm_reduce_product_in_cart(session, user_id=user.id, product_id=product_id, size=size)
    await callback_query.answer(text=f'Товар удален из корзины',
                                show_alert=True)
    user_id = callback_query.from_user.id
    query_cart = select(Cart).where(Cart.user_id == user_id)
    result_cart = await session.execute(query_cart)
    cart_items = result_cart.scalars().all()
    product_ids = [item.product_id for item in cart_items]
    query_products = select(Product).where(Product.id.in_(product_ids))
    result_products = await session.execute(query_products)
    products = {product.id: product for product in result_products.scalars().all()}

    buttons = [
        [InlineKeyboardButton(text=f"{products[item.product_id].name} {item.size} {item.quantity} шт.",
                              callback_data=f"remove_{item.product_id}_{item.size}")]
        for item in cart_items
    ]

    buttons.append([InlineKeyboardButton(text="Назад", callback_data="Корзина")])
    await bot.edit_message_text(
        text=f'Выберите товар для редактирования',
        inline_message_id=callback_query.inline_message_id,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode='Markdown'
    )


@router.callback_query(F.data.startswith("Оплата"))
async def pay(callback_query: types.CallbackQuery, bot: Bot):
    cost = int(callback_query.data.split('_')[1]) * 100
    await bot.send_invoice(
        chat_id=callback_query.from_user.id,
        title="Оплата заказа",
        description="Платеж №",
        payload='Payment throught a bot',
        provider_token="401643678:TEST:478c874c-3bf2-4b7e-880e-b93ff769b016",
        currency='rub',
        prices=[
            LabeledPrice(label='К оплате',
                         amount=cost,
                         )
        ],
        max_tip_amount=5000,
        suggested_tip_amounts=[1000, 2000, 3000, 4000],
        # start_parameter=''
        provider_data=None,
        photo_url='https://i.ibb.co/fGLKsYP/photo-2024-07-27-08-31-17.jpg',
        # photo_size=100,
        # photo_width=800,
        # photo_height=450,
        need_name=True,
        need_phone_number=True,
        need_email=True,
        need_shipping_address=True,
        send_phone_number_to_provider=False,
        send_email_to_provider=False,
        is_flexible=False,
        disable_notification=False,
        protect_content=False,
        reply_to_message_id=None,
        allow_sending_without_reply=True,
        reply_markup=None,
        request_timeout=15
    )


@router.pre_checkout_query()
async def pre_check_query(pre_checkout_query: types.PreCheckoutQuery, bot: Bot):
    print('я сработал')
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: types.Message, session: AsyncSession):
    await orm_clear_cart(session, message.from_user.id)
    await message.reply(text="Спасибо за оплату! Если есть вопросы напишите в поддержку @nzenn")
    await message.answer(text="Добро пожаловать в наш магазин", reply_markup=inlinekeyboard_menu.inkb_start_menu)
