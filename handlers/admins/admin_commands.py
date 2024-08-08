from aiogram import Router, types, F, Bot
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent, LinkPreviewOptions, InlineKeyboardMarkup, \
    InlineKeyboardButton

from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_add_product, orm_get_products, orm_delete_product, orm_get_product_id, \
    orm_update_product
from keyboards.default import inlinekeyboard_menu
from filtres import IsAdmin, ChatTypeFilter

router = Router(name=__name__)


router.message.filter(ChatTypeFilter(["private"]), IsAdmin())

class AddProduct(StatesGroup):
    name = State()
    description = State()
    price = State()
    url_image = State()

    product_for_change = None

    texts = {
        'AddProduct:name': 'Введите название заново:',
        'AddProduct:description': 'Введите описание заново:',
        'AddProduct:price': 'Введите стоимость заново:',
        'AddProduct:url_image': 'Этот стейт последний, поэтому...',
    }


@router.message(Command(commands=['admin']))
@router.callback_query(F.data == 'Админ')
async def admin_menu(message: types.Message | types.CallbackQuery):
    if isinstance(message, types.Message):
        await message.answer_photo(
            photo='AgACAgIAAxkBAAIESGalIT54utSMH4dqVHPgiEYQRZ2GAAIv3DEbUkMpSQs47m-f67JoAQADAgADeQADNQQ',
            caption="Админ панель",
            reply_markup=inlinekeyboard_menu.inkb_admin_menu)
    else:
        await message.message.answer_photo(
            photo='AgACAgIAAxkBAAIESGalIT54utSMH4dqVHPgiEYQRZ2GAAIv3DEbUkMpSQs47m-f67JoAQADAgADeQADNQQ',
            caption="Админ панель",
            reply_markup=inlinekeyboard_menu.inkb_admin_menu)


@router.callback_query(StateFilter(None), F.data == 'Добавить товар')
async def add_item(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_caption(caption='Введите название товара: ')
    await state.set_state(AddProduct.name)


@router.message(StateFilter('*'), Command("отмена"))
@router.message(StateFilter('*'), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    if AddProduct.product_for_change:
        AddProduct.product_for_change = None

    await state.clear()
    await message.answer("Действия отменены")
    await message.answer_photo(
        photo='AgACAgIAAxkBAANfZpoz0SgDWAItgl_sgxXnX_d2ubwAAk_iMRsFv9FIpGxvPGQ7y5kBAAMCAAN4AAM1BA',
        caption="Админ панель",
        reply_markup=inlinekeyboard_menu.inkb_admin_menu)


@router.message(StateFilter('*'), Command("назад"))
@router.message(StateFilter('*'), F.text.casefold() == "назад")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()

    if current_state == AddProduct.name:
        await message.answer('Предыдущего шага нет, или введите название товара или напишите "отмена"')
        return

    previous = None
    for step in AddProduct.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f"ок, вы вернулись к прошлому шагу \n {AddProduct.texts[previous.state]}")
            return
        previous = step


@router.message(AddProduct.name, F.text)
async def add_name(message: types.Message, state: FSMContext):
    if message.text == '.':
        await state.update_data(name=AddProduct.product_for_change.name)
        await message.answer(f'Название: {AddProduct.product_for_change.name}\nВведите описание товара: ')
    else:
        await state.update_data(name=message.text)
        await message.answer(f'Название: {message.text}\nВведите описание товара: ')
    await state.set_state(AddProduct.description)


@router.message(AddProduct.name)
async def add_name(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели не допустимые данные, введите текса названия товара")


@router.message(AddProduct.description, F.text)
async def add_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data.get('name')
    if message.text == '.':
        await state.update_data(description=AddProduct.product_for_change.description)
        await message.answer(f'Название: {name}\nОписание: {AddProduct.product_for_change.description}\nВведите стоимость товара: ')
    else:
        await state.update_data(description=message.text)
        await message.answer(f'Название: {name}\nОписание: {message.text}\nВведите стоимость товара: ')
    await state.set_state(AddProduct.price)


@router.message(AddProduct.price, F.text)
async def add_url(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data.get('name')
    description = data.get('description')
    if message.text == '.':
        await state.update_data(price=AddProduct.product_for_change.price)
        await message.answer(f'Название: {name}\nОписание: {description}\nСтоимость: {AddProduct.product_for_change.price}₽\nВведите url фото: ')
    else:
        await state.update_data(price=message.text)
        await message.answer(f'Название: {name}\nОписание: {description}\nСтоимость: {message.text}\nВведите url фото: ')
    await state.set_state(AddProduct.url_image)


@router.message(AddProduct.url_image, F.text)
async def add_(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    if message.text == '.':
        await state.update_data(url_image=AddProduct.product_for_change.url_image)
    else:
        await state.update_data(url_image=message.text)
    data = await state.get_data()
    try:
        if AddProduct.product_for_change:
            await orm_update_product(session, AddProduct.product_for_change.id, data)
            await message.answer('Товар успешно изменен')
            await message.answer_photo(
                photo='AgACAgIAAxkBAAIESGalIT54utSMH4dqVHPgiEYQRZ2GAAIv3DEbUkMpSQs47m-f67JoAQADAgADeQADNQQ',
                caption='Админ панель', reply_markup=inlinekeyboard_menu.inkb_admin_menu)
            await state.clear()
        else:
            await orm_add_product(session, data)
            await message.answer('Товар успешно добавлен')
            await message.answer_photo(
                photo='AgACAgIAAxkBAAIESGalIT54utSMH4dqVHPgiEYQRZ2GAAIv3DEbUkMpSQs47m-f67JoAQADAgADeQADNQQ',
                caption='Админ панель', reply_markup=inlinekeyboard_menu.inkb_admin_menu)
            await state.clear()
    except Exception as ex:
        await message.answer(
            f'Ошибка: \n{str(ex)}\nОбратись к программеру, он опять денег хочет')
        await message.answer_photo(
            photo='AgACAgIAAxkBAAIESGalIT54utSMH4dqVHPgiEYQRZ2GAAIv3DEbUkMpSQs47m-f67JoAQADAgADeQADNQQ',
            caption='Админ панель', reply_markup=inlinekeyboard_menu.inkb_admin_menu)
        await state.clear()
    AddProduct.product_for_change = None


@router.inline_query(lambda query: query.query == "Товары")
async def starring_at_product(query: types.InlineQuery, session: AsyncSession, bot: Bot):
    items = [InlineQueryResultArticle(id=str(product.id),
                                      input_message_content=InputTextMessageContent(
                                          message_text=f'{product.name}\n{product.description}\nЦена: {product.price}₽',
                                          link_preview_options=LinkPreviewOptions(
                                              url=product.url_image)),
                                      title=f'{product.name} {product.price}₽',
                                      thumbnail_url=product.url_image,
                                      description=product.description) for product in await orm_get_products(session)]
    await bot.answer_inline_query(query.id, items)


@router.inline_query(StateFilter(None), lambda query: query.query == "Удалить товар")
async def delete_item(query: types.InlineQuery, session: AsyncSession, bot: Bot):
    items = [InlineQueryResultArticle(id=str(product.id),
                                      input_message_content=InputTextMessageContent(message_text=product.name,
                                                                                    link_preview_options=LinkPreviewOptions(
                                                                                        url=product.url_image)),
                                      title=f'{product.name} {product.price}₽',
                                      thumbnail_url=product.url_image,
                                      description=product.description, reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text='Удалить', callback_data=f"delete_{product.id}")]]))
             for product in await orm_get_products(session)]
    await bot.answer_inline_query(query.id, items)


@router.callback_query(F.data.startswith('delete_'))
async def delete(callback_query: types.CallbackQuery, session: AsyncSession, bot: Bot):
    product_id = callback_query.data.split("_")[-1]
    await orm_delete_product(session, int(product_id))
    await bot.send_message(callback_query.from_user.id, 'Товар успешно удален',
                           reply_markup=inlinekeyboard_menu.inkb_back_admin_menu)


@router.inline_query(StateFilter(None), lambda query: query.query == "Изменить товар")
async def change_item(query: types.InlineQuery, session: AsyncSession, bot: Bot):
    items = [InlineQueryResultArticle(id=str(product.id),
                                      input_message_content=InputTextMessageContent(
                                          message_text=f'{product.name}\n{product.description}\nЦена: {product.price}₽',
                                          link_preview_options=LinkPreviewOptions(
                                              url=product.url_image)),
                                      title=f'{product.name} {product.price}₽',
                                      thumbnail_url=product.url_image,
                                      description=product.description, reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text='Изменить', callback_data=f"change_{product.id}")]]))
             for product in await orm_get_products(session)]
    await bot.answer_inline_query(query.id, items)


@router.callback_query(F.data.startswith('change_'))
async def change(callback_query: types.CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    product_id = callback_query.data.split("_")[-1]
    product_for_change = await orm_get_product_id(session, int(product_id))

    AddProduct.product_for_change = product_for_change
    await bot.send_message(callback_query.from_user.id, "Введите название товара")
    await state.set_state(AddProduct.name)
