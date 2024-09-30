from sqlalchemy import String, Text, Float, Integer, DateTime, func, Numeric, ForeignKey, BigInteger, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class Product(Base):
    __tablename__ = 'product'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    url_image: Mapped[str] = mapped_column(String(150))


class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    first_name: Mapped[str] = mapped_column(String(150), nullable=True)
    last_name: Mapped[str] = mapped_column(String(150), nullable=True)
    phone: Mapped[str] = mapped_column(String(13), nullable=True)
    bonuses: Mapped[int] = mapped_column(Integer, default=0)
    has_active_invoice: Mapped[bool] = mapped_column(Boolean, default=False)
    invoice_message_id = mapped_column(Integer, nullable=True)
    payment_id: Mapped[str] = mapped_column(String, nullable=True)


class Cart(Base):
    __tablename__ = 'cart'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    size: Mapped[str] = mapped_column(String(2), nullable=False)  # я добавил
    quantity: Mapped[int]

    user: Mapped['User'] = relationship(backref='cart')
    product: Mapped['Product'] = relationship(backref='cart')


class Orders(Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)  # Описание заказа
    phone: Mapped[str] = mapped_column(String, nullable=True)  # Номер телефона
    email: Mapped[str] = mapped_column(String, nullable=True)  # Email
    shipping_address: Mapped[str] = mapped_column(String, nullable=True)  # Адрес доставки
    status: Mapped[str] = mapped_column(String, nullable=False, default='pending')  # Статус заказа
