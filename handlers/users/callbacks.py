import asyncio

from aiogram import types, F, Router, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Cart, Product
from database.orm_query import orm_add_user, orm_add_to_cart, orm_delete_from_cart, orm_reduce_product_in_cart, \
    orm_clear_cart
from keyboards import inlinekeyboard_menu

router = Router(name=__name__)


class Discount(StatesGroup):
    promo_code = State()


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

    query_bonuses = select(User.bonuses).where(User.user_id == callback_query.from_user.id)
    result_bonuses = await session.execute(query_bonuses)
    user_bonuses = result_bonuses.scalar_one_or_none() or 0

    if not cart_items:
        await bot.edit_message_text(
            text=f'У вас {user_bonuses} бонусных рублей\n\nВаша корзина пуста',
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
    finnaly_cost = max(10, cost - user_bonuses)
    cart_text += f'\nУ вас {user_bonuses} бонусных рублей\nМинимальная сумма заказа 10 руб.\n\nИтого по счету: {cost} руб - {cost - finnaly_cost} бонусов = {finnaly_cost} руб.'

    await bot.edit_message_text(
        text=f'[Корзина]\n\n{cart_text}',
        inline_message_id=callback_query.inline_message_id,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='Перейти к оплате', callback_data=f"Оплата_{finnaly_cost}")],
                [InlineKeyboardButton(text='Редактор заказа', callback_data="Редактировать корзину")],
                [InlineKeyboardButton(text='\U0001F519В меню', callback_data='Магазин')]
            ]
        ),
        parse_mode='Markdown'
    )


@router.callback_query(StateFilter(None), F.data == 'Промокод')
async def main_menu(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    await bot.edit_message_text(
        text='Введите промокод',
        inline_message_id=callback_query.inline_message_id,
        parse_mode='Markdown',
    )
    await state.set_state(Discount.promo_code)


@router.message(Discount.promo_code, F.text)
async def add_name(message: types.Message, state: FSMContext):
    await state.update_data(promo_code=message.text)
    await state.clear()
    await message.answer(
        f'Промокод на {message.text} успешно применен!\nНаличие скидки можете посмотреть в корзине с товарами!')


@router.callback_query(F.data.startswith('buy_'))
async def add_in_basket(callback_query: types.CallbackQuery, session: AsyncSession):
    user = callback_query.from_user
    product_id = int(callback_query.data.split('_')[1])
    size = callback_query.data.split('_')[2]
    await orm_add_to_cart(session, user_id=user.id, product_id=product_id, size=size)
    await callback_query.answer(text=f'Товар успешно добавлен в корзину',
                                show_alert=True)


@router.callback_query(F.data == "Редактировать корзину")
async def remove_from_basket(callback_query: types.CallbackQuery, session: AsyncSession, bot: Bot):
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
                              callback_data=f"edit_{item.product_id}_{item.size}")]
        for item in cart_items
    ]

    buttons.append([InlineKeyboardButton(text="Назад", callback_data="Корзина")])

    await bot.edit_message_text(
        text=f'Выберите товар для редактирования',
        inline_message_id=callback_query.inline_message_id,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode='Markdown'
    )


@router.callback_query(F.data.startswith('edit_'))
async def edit_product(callback_query: types.CallbackQuery, session: AsyncSession, bot: Bot):
    user = callback_query.from_user
    size = callback_query.data.split('_')[2]
    product_id = int(callback_query.data.split('_')[1])
    select_product = select(Product).where(Product.id == product_id)
    result_product = await session.execute(select_product)
    product = result_product.scalar_one_or_none()

    await bot.edit_message_text(
        text=f'[Добавить/Удалить]({product.url_image})',
        inline_message_id=callback_query.inline_message_id,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕", callback_data=f'add_{product_id}_{size}')],
            [InlineKeyboardButton(text="➖", callback_data=f'remove_{product_id}_{size}')],
            [InlineKeyboardButton(text="Назад", callback_data='Редактировать корзину')]

        ]),
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


@router.callback_query(F.data.startswith('add_'))
async def add_product(callback_query: types.CallbackQuery, session: AsyncSession, bot: Bot):
    user = callback_query.from_user
    size = callback_query.data.split('_')[2]
    product_id = int(callback_query.data.split('_')[1])

    await orm_add_to_cart(session, user_id=user.id, product_id=product_id, size=size)
    await callback_query.answer(text=f'Товар добавлен в корзину',
                                show_alert=True)


@router.callback_query(F.data.startswith("Оплата"))
async def pay(callback_query: types.CallbackQuery, bot: Bot, session: AsyncSession):
    user_id = callback_query.from_user.id

    # Проверка наличия активного счета
    query_user = select(User).where(User.user_id == user_id)
    result_user = await session.execute(query_user)
    user = result_user.scalar_one_or_none()

    if user and user.has_active_invoice:
        await callback_query.answer(text="У вас уже есть активный счет на оплату.", show_alert=True)
        return

    query_cart = select(Cart).where(Cart.user_id == user_id)
    result_cart = await session.execute(query_cart)
    cart_items = result_cart.scalars().all()

    product_ids = [item.product_id for item in cart_items]
    query_products = select(Product).where(Product.id.in_(product_ids))
    result_products = await session.execute(query_products)
    products = {product.id: product for product in result_products.scalars().all()}

    description = [f"{products[item.product_id].name} {item.size} {item.quantity} шт." for item in cart_items]

    cost = int(callback_query.data.split('_')[1]) * 100
    invoice_message = await bot.send_invoice(
        chat_id=callback_query.from_user.id,
        title="Оплата заказа №",
        description='\n'.join(description),
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
        protect_content=True,
        reply_to_message_id=None,
        allow_sending_without_reply=True,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f'Заплатить {cost // 100} RUB', pay=True)],
                [InlineKeyboardButton(text="Отменить оплату", callback_data="Отменить оплату")]]
        ),
        request_timeout=15
    )

    # Обновление флага активного счета
    user.has_active_invoice = True
    user.invoice_message_id = invoice_message.message_id  # Сохраняем ID сообщения
    await session.commit()

    # Удаление инвойса через 15 минут
    await asyncio.sleep(900)  # 900 секунд = 15 минут

    # Проверяем, не было ли отменено пользователем
    updated_user = await session.get(User, user.id)
    if updated_user.has_active_invoice:  # Если инвойс всё ещё активен
        try:
            await bot.delete_message(chat_id=user_id, message_id=invoice_message.message_id)
        except Exception as e:
            print(f"Не удалось удалить сообщение с инвойсом: {e}")
        finally:
            updated_user.has_active_invoice = False
            await session.commit()


@router.callback_query(F.data == "Отменить оплату")
async def cancel_payment(callback_query: types.CallbackQuery, session: AsyncSession, bot: Bot):
    user_id = callback_query.from_user.id

    # Сброс активного счета
    query_user = select(User).where(User.user_id == user_id)
    result_user = await session.execute(query_user)
    user = result_user.scalar_one_or_none()

    if user:
        user.has_active_invoice = False
        await session.commit()

    await callback_query.answer(text="Оплата была отменена.", show_alert=True)

    if user and user.invoice_message_id:
        try:
            await bot.delete_message(
                chat_id=callback_query.message.chat.id,
                message_id=user.invoice_message_id
            )
        except Exception as e:
            # Обработка ошибки, если сообщение не удалось удалить
            print(f"Ошибка при удалении сообщения с инвойсом: {e}")


@router.message(F.successful_payment)
async def successful_payment(message: types.Message, session: AsyncSession):
    user_id = message.from_user.id

    # Очистка корзины
    await orm_clear_cart(session, user_id)

    # Сброс активного счета
    query_user = select(User).where(User.user_id == user_id)
    result_user = await session.execute(query_user)
    user = result_user.scalar_one_or_none()

    if user:
        user.has_active_invoice = False
        await session.commit()

    await message.reply(text="Спасибо за оплату! Если есть вопросы напишите в поддержку @nzenn")
    await message.answer(text="Добро пожаловать в наш магазин", reply_markup=inlinekeyboard_menu.inkb_start_menu)


@router.pre_checkout_query()
async def pre_check_query(pre_checkout_query: types.PreCheckoutQuery, bot: Bot):
    print('я сработал')
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
