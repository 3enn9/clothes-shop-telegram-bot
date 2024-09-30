import asyncio
import logging
import uuid

from aiogram import types, F, Router, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, ReplyKeyboardMarkup, KeyboardButton
from aiohttp import ClientSession

from fastapi.responses import JSONResponse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from yookassa import Payment, Configuration
from yookassa.domain.notification import WebhookNotificationEventType
from yookassa.domain.response import PaymentResponse

from database.engine import session_maker
from database.models import User, Cart, Product, Orders
from database.orm_query import orm_add_user, orm_add_to_cart, orm_delete_from_cart, orm_reduce_product_in_cart, \
    orm_clear_cart
from keyboards import inlinekeyboard_menu
from data.config import API_KEY

router = Router(name=__name__)


class Discount(StatesGroup):
    promo_code = State()


@router.callback_query(F.data == 'О нас')
async def about_us(callback_query: types.CallbackQuery, bot: Bot):
    await bot.edit_message_text(text='Мы небольшая компания, которая только набирает свою популярность 🌟 и старается '
                                     'предложить лучший сервис для наших клиентов 🤝. Спасибо, что выбрали нас! 🙏',
                                inline_message_id=callback_query.inline_message_id,
                                reply_markup=inlinekeyboard_menu.inkb_back_main_menu)


@router.callback_query(F.data.startswith('Погода'))
async def about_us(callback_query: types.CallbackQuery, bot: Bot):
    if callback_query.data.split('_')[1] == 'страны':
        await callback_query.message.delete()
        await callback_query.message.answer(
            text='Выберите город',
            inline_message_id=callback_query.inline_message_id,
            reply_markup=inlinekeyboard_menu.inkb_citys)
    else:
        await callback_query.message.edit_text(
            text='Выберите город',
            inline_message_id=callback_query.inline_message_id,
            reply_markup=inlinekeyboard_menu.inkb_citys
        )


@router.callback_query(F.data.startswith('weather_'))
async def city_weather(callback_query: types.CallbackQuery):
    coordinates = {
        "Москва": {"lat": 55.7558, "lon": 37.6176,
                   'photo_id': 'AgACAgIAAxkBAAIGwmbQhDFJfGtqQ7aE_QbBOzvdymITAAKw4jEbTcqJSt4qMV1GpFg7AQADAgADeAADNQQ'},
        "Париж": {"lat": 48.8566, "lon": 2.3522,
                  'photo_id': 'AgACAgIAAxkBAAIGw2bQhDVDwZmcTUOzPqZT3e3cQSU5AAKx4jEbTcqJSihLxXbRDolzAQADAgADeQADNQQ'},
        "ОАЭ": {"lat": 25.276987, "lon": 55.296249,
                'photo_id': 'AgACAgIAAxkBAAIGxmbQhDtjpehIDOJfB363M7hW33F_AAKy4jEbTcqJSjyc0IqKI64QAQADAgADeAADNQQ'}
    }

    city = callback_query.data.split('_')[1]

    # Извлеките широту и долготу
    lat = coordinates[city]["lat"]
    lon = coordinates[city]["lon"]
    # photo_id = coordinates[city]["photo_id"]
    photo_id = 'AgACAgIAAxkBAAIGxmbQhDtjpehIDOJfB363M7hW33F_AAKy4jEbTcqJSjyc0IqKI64QAQADAgADeAADNQQ'

    # Постройте URL для запроса к API
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    logging.info(f"Запрос URL: {url}")

    # async with ClientSession() as session:
    #     try:
    #         async with session.get(url) as response:
    #             if response.status == 200:
    #
    #                 # data = await response.json()
    #                 # weather_description = data['weather'][0]['description']
    #                 # temperature = data['main']['temp']
    #                 await callback_query.message.edit_text(
    #                     text=f"Погода: {city}:\n"
    #                          f"Температура: {temperature}°C\n"
    #                          f"Описание: {weather_description.capitalize()}",
    #                     reply_markup=InlineKeyboardMarkup(
    #                         inline_keyboard=[[InlineKeyboardButton(text='Назад', callback_data='Погода')]])
    #                 )
    #             else:
    #                 logging.error(f"Ошибка при запросе данных: {response.status}")
    #                 await callback_query.message.edit_text(text="Не удалось получить данные о погоде.",
    #                                                        reply_markup=InlineKeyboardMarkup(
    #                                                            inline_keyboard=[[InlineKeyboardButton(text='Назад',
    #                                                                                                   callback_data='Погода')]])
    #                                                        )
    #     except Exception as e:
    #         logging.error(f"Ошибка соединения: {str(e)}")
    #         await callback_query.message.edit_text(text="Ошибка соединения. Попробуйте позже.",
    #                                                reply_markup=InlineKeyboardMarkup(
    #                                                    inline_keyboard=[[InlineKeyboardButton(text='Назад',
    #                                                                                           callback_data='Погода')]])
    #                                                )
    weather_description = 'skfjsjf'
    temperature = '20'
    await callback_query.message.delete()
    await callback_query.message.answer_photo(
        photo=photo_id,
        caption=f"Погода в {city}:\n"
                f"Температура: {temperature}°C\n"
                f"Описание: {weather_description.capitalize()}",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text='Назад', callback_data='Погода_страны')]])
    )


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
                [InlineKeyboardButton(text='Перейти к оплате', callback_data=f"Оплата")],
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
async def add_name(message: types.Message, state: FSMContext, bot: Bot):
    await state.update_data(promo_code=message.text)
    await state.clear()
    await message.answer(
        f'Промокод {message.text} успешно применен!\nНаличие скидки можете посмотреть в корзине с товарами!',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text='\U0001F519Назад', switch_inline_query_current_chat='')]]))


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





### Проба
class AddPayment(StatesGroup):
    phone = State()
    address = State()


@router.callback_query(StateFilter(None), F.data == 'Оплата')
async def get_phone_number(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    # Получаем данные пользователя
    query_user = select(User).where(User.user_id == callback.from_user.id)
    result_user = await session.execute(query_user)
    user = result_user.scalar_one_or_none()

    if user and user.has_active_invoice:
        await callback.answer(text="У вас уже есть активный счет на оплату.", show_alert=True)
        return

    # Создаем клавиатуру с кнопкой для запроса контакта
    contact_keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text='Отправить контакт', request_contact=True)]
        ]
    )
    await bot.send_message(chat_id=callback.from_user.id,
                           text='Напишите ваш номер телефона для связи или отправьте контакт',
                           reply_markup=contact_keyboard)
    await state.set_state(AddPayment.phone)


@router.message(AddPayment.phone, F.contact)
async def get_phone_number(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(phone=str(message.contact.phone_number))
    await message.answer(text='Напишите ваш адрес', reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AddPayment.address)


@router.message(AddPayment.phone, F.text)
async def get_phone_number(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(phone=message.text)
    await message.answer(text='Напишите ваш адрес', reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AddPayment.address)


@router.message(AddPayment.address, F.text)
async def address(message: types.Message, state: FSMContext, bot: Bot, session: AsyncSession):
    user_id = message.from_user.id

    # Обновляем состояние данными адреса
    await state.update_data(address=message.text)

    data = await state.get_data()
    phone = data.get('phone')

    # Получаем данные пользователя
    query_user = select(User).where(User.user_id == user_id)
    result_user = await session.execute(query_user)
    user = result_user.scalar_one_or_none()

    # Получение товаров из корзины
    query_cart = select(Cart).where(Cart.user_id == user_id)
    result_cart = await session.execute(query_cart)
    cart_items = result_cart.scalars().all()

    if not cart_items:
        await message.answer("Ваша корзина пуста.")
        await state.clear()
        return

    # Получение информации о продуктах
    product_ids = [item.product_id for item in cart_items]
    query_products = select(Product).where(Product.id.in_(product_ids))
    result_products = await session.execute(query_products)
    products = {product.id: product for product in result_products.scalars().all()}

    # Подсчет стоимости и составление описания
    cost = 0
    description_parts = []

    for item in cart_items:
        product = products.get(item.product_id)
        if product:
            total_price = item.quantity * product.price
            cost += total_price
            description_parts.append(f"{product.name} {item.size} {item.quantity} шт.")
    description_parts.append(f'Адрес: {message.text}')
    description_parts.append(f'Номер телефона: {phone}')

    # Получаем бонусы пользователя
    query_bonuses = select(User.bonuses).where(User.user_id == user_id)
    result_bonuses = await session.execute(query_bonuses)
    user_bonuses = result_bonuses.scalar_one_or_none() or 0

    # Расчет финальной стоимости с учетом бонусов
    finnaly_cost = max(10, cost - user_bonuses)

    # Описание заказа
    description = '\n'.join(description_parts)

    # Создание платежа через ЮKassa
    payment_id = str(uuid.uuid4())
    payment = Payment.create({
        "amount": {
            "value": finnaly_cost,
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://your-site.com/return-url"  # URL, куда перенаправит после оплаты
        },
        "capture": True,
        "description": description,
        "metadata": {
            "user_id": user_id,
            "payment_id": payment_id  # ваш ID платежа для внутреннего учета
        }
    })

    # Получение URL для перенаправления на оплату
    confirmation_url = payment.confirmation.confirmation_url

    # Отправка ссылки на оплату пользователю
    inkb_delete_invoice = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Оплатить', url=confirmation_url)],
            [InlineKeyboardButton(text='Отменить', callback_data='Отменить оплату')]
        ]
    )

    message_invoice = await bot.send_message(
        chat_id=user_id,
        text=f"Ваш заказ:\n{description}\n\nСумма к оплате: {finnaly_cost} RUB",
        reply_markup=inkb_delete_invoice
    )

    # Сохраняем ID инвойса и обновляем состояние пользователя
    user.invoice_message_id = message_invoice.message_id
    user.has_active_invoice = True
    user.payment_id = payment_id
    await session.commit()

    # Очищаем состояние FSM
    await state.clear()

    # Устанавливаем таймер на 10 минут для удаления сообщения с инвойсом
    await asyncio.sleep(600)  # 600 секунд = 10 минут

    # Проверяем статус счета
    updated_user = await session.get(User, user.id)
    if updated_user.has_active_invoice:
        try:
            await bot.delete_message(chat_id=user_id, message_id=message_invoice.message_id)
        except Exception as e:
            print(f"Не удалось удалить сообщение с инвойсом: {e}")
        finally:
            updated_user.has_active_invoice = False
            await session.commit()

from data.config import app, bot

async def get_session() -> AsyncSession:
    async with session_maker() as session:
        yield session
@app.post("/api/payment/notifications")
async def payment_notifications(data: dict):
    # Логика обработки уведомления о платеже
    async with session_maker() as session:
        if data.get('event') == 'payment.succeeded':
            payment_id = data['object']['id']
            user_id = int(data['object']['metadata']['user_id'])
            # Очистка корзины
            await orm_clear_cart(session, user_id)

            # Сброс активного счета
            query_user = select(User).where(User.user_id == user_id)
            result_user = await session.execute(query_user)
            user = result_user.scalar_one_or_none()

            if user:
                user.has_active_invoice = False
                await session.commit()

            await bot.send_message(chat_id=user_id, text="Ваш платеж успешно обработан!\nВ ближайшее время с вами свяжется наш менеджер ")

    return JSONResponse(content={"status": "ok"}, status_code=200)