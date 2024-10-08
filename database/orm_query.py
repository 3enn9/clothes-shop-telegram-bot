from aiogram import Bot
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import Product, User, Cart


############ Админка: добавить/изменить/удалить товар ########################

async def orm_add_product(session: AsyncSession, data: dict):
    obj = Product(
        name=data["name"],
        description=data["description"],
        price=int(data["price"]),
        url_image=data["url_image"]
    )
    session.add(obj)
    await session.commit()


async def orm_get_products(session: AsyncSession):
    query = select(Product)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_product_id(session: AsyncSession, product_id: int):
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_get_product_name(session: AsyncSession, product_name: str):
    query = select(Product).where(Product.name.like(f"%{product_name}%"))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_update_product(session: AsyncSession, product_id: int, data):
    query = update(Product).where(Product.id == product_id).values(
        name=data["name"],
        description=data["description"],
        price=int(data["price"]),
        url_image=data["url_image"], )
    await session.execute(query)
    await session.commit()


async def orm_delete_product(session: AsyncSession, product_id: int):
    query = delete(Product).where(Product.id == product_id)
    await session.execute(query)
    await session.commit()


##################### Добавляем юзера в БД #####################################

async def orm_add_user(
        session: AsyncSession,
        user_id: int,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
        bonuses: int = 0,
        has_active_invoice: bool = False,
        invoice_message_id: int | None = None,
        payment_id: str | None = None
):
    query = select(User).where(User.user_id == user_id)
    result = await session.execute(query)
    if result.first() is None:
        session.add(
            User(user_id=user_id, first_name=first_name, last_name=last_name, phone=phone, bonuses=bonuses,
                 has_active_invoice=has_active_invoice, invoice_message_id=invoice_message_id, payment_id=payment_id)
        )
        await session.commit()


######################## Работа с корзинами #######################################

async def orm_add_to_cart(session: AsyncSession, user_id: int, product_id: int, size: str):
    query = select(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id, Cart.size == size)
    cart = await session.execute(query)
    cart = cart.scalar()
    if cart:
        cart.quantity += 1
        await session.commit()
        return cart
    else:
        session.add(Cart(user_id=user_id, product_id=product_id, size=size, quantity=1))
        await session.commit()


async def orm_get_user_carts(session: AsyncSession, user_id):
    query = select(Cart).filter(Cart.user_id == user_id).options(joinedload(Cart.product))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_delete_from_cart(session: AsyncSession, user_id: int, product_id: int, size: str):
    query = delete(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id, Cart.size == size)
    await session.execute(query)
    await session.commit()


async def orm_reduce_product_in_cart(session: AsyncSession, user_id: int, product_id: int, size: str):
    query = select(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id, Cart.size == size)
    cart = await session.execute(query)
    cart = cart.scalar()

    if not cart:
        return
    if cart.quantity > 1:
        cart.quantity -= 1
        await session.commit()
        return True
    else:
        await orm_delete_from_cart(session, user_id, product_id, size)
        await session.commit()
        return False


async def orm_clear_cart(session: AsyncSession, user_id: int):
    query = delete(Cart).where(Cart.user_id == user_id)
    await session.execute(query)
    await session.commit()


##################### Удалить инвойсы #####################################

async def orm_del_invoices(session: AsyncSession, bot: Bot):
    result = await session.execute(select(User).filter(User.invoice_message_id.isnot(None)))
    users = result.scalars().all()

    for user in users:
        if user.invoice_message_id:  # Проверяем, что invoice_message_id не None
            try:
                await bot.delete_message(chat_id=user.user_id, message_id=user.invoice_message_id)
                user.invoice_message_id = None  # Устанавливаем значение в None после удаления
                user.has_active_invoice = False
                user.payment_id = None
            except Exception as e:
                print(f"Не удалось удалить сообщение для пользователя {user.user_id}: {e}")

    await session.commit()  # Сохраняем изменения в базе данных
