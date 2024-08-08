from aiogram.types.keyboard_button import KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


item_id = 0
inkb_sizes = InlineKeyboardMarkup(row_width=3, inline_keyboard=[
    [
        InlineKeyboardButton(text='S', callback_data=f'buy_{item_id}_S'),
        InlineKeyboardButton(text='M', callback_data=f'buy_{item_id}_M'),
        InlineKeyboardButton(text='L', callback_data=f'buy_{item_id}_L')
    ],
    [
        InlineKeyboardButton(text='🛒Корзина', callback_data="Корзина")
    ],
    [
        InlineKeyboardButton(text='\U0001F519Назад', callback_data=f'Товары')
    ]
])

inkb_main_menu = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='🛒Корзина', callback_data="Корзина")],
            [InlineKeyboardButton(text='🛍Товары', callback_data="Товары")],
            [InlineKeyboardButton(text='Способы оплаты', callback_data='пусто')],
            [InlineKeyboardButton(text='Варианты доставки', callback_data='пусто')],
            [InlineKeyboardButton(text='📄О нас', callback_data='О нас')]
        ]
    )

inkb_back_main_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='\U0001F519Назад', callback_data='Магазин')]
    ]
)
inkb_back_admin_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='\U0001F519Назад', callback_data='Админ')]
    ]
)


inkb_items = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='\U0001F455Футболки', switch_inline_query_current_chat="cat_Футболка")],
            [InlineKeyboardButton(text='Свитшоты', switch_inline_query_current_chat='cat_Свитшот')],
            [InlineKeyboardButton(text='\U0001F519Назад', callback_data='Магазин')]
        ]
    )


inkb_admin_menu = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Изменить товар', switch_inline_query_current_chat="Изменить товар")],
            [InlineKeyboardButton(text='Удалить товар', switch_inline_query_current_chat='Удалить товар')],
            [InlineKeyboardButton(text='🛍Товары', switch_inline_query_current_chat='Товары')],
            [InlineKeyboardButton(text='Добавить товар', callback_data='Добавить товар')]
        ]
    )

inkb_start_menu = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='Магазин', switch_inline_query_current_chat='')
    ],
[
        InlineKeyboardButton(text='Рефералы', callback_data=f'Пусто'),
        InlineKeyboardButton(text='Доставка', callback_data=f'Пусто'),
    ]
])
inkb_basket = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Перейти к оплате', callback_data="Оплата")],
        [InlineKeyboardButton(text='Редактор заказа', callback_data="Редактировать корзину")],
        [InlineKeyboardButton(text='\U0001F519В меню', callback_data='Магазин')]
    ]
)