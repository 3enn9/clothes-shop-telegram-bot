import asyncio
import logging
import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import Request
from middlewares.db import DataBaseSession
from database.engine import create_db, session_maker
from database.orm_query import orm_del_invoices
from handlers import router
from data.config import bot, app, URL_APP



@app.post('/webhook')
async def handle_webhook(request: Request):
    """Обработка вебхуков от Telegram."""
    data = await request.json()
    update = Update(**data)

    # Обработка обновления через диспетчер
    await dp._process_update(bot, update)

    return {"status": "ok"}

async def set_webhook():
    """Установка вебхука вручную при запуске приложения."""
    webhook_set = await bot.set_webhook(URL_APP + '/webhook')
    if webhook_set:
        print("Webhook установлен успешно")
    else:
        print("Ошибка установки webhook")


async def on_startup():
    """Инициализация при старте: установка вебхука и инициализация базы данных."""
    await create_db()  # Инициализация базы данных
    await set_webhook()


async def on_shutdown():
    """Очистка ресурсов перед завершением работы."""
    async with session_maker() as session:
        await orm_del_invoices(session, bot)

    # Удаление вебхука
    await bot.delete_webhook()
    print('бот лег')


async def run_bot():
    """Запуск Telegram-бота с вебхуками."""
    global dp
    bot.my_admins_list = [877804669]  # Список администраторов
    dp = Dispatcher(bot=bot)
    dp.include_router(router)

    # Регистрация событий завершения работы
    dp.shutdown.register(on_shutdown)

    # Применение middleware для работы с сессией базы данных
    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    logging.basicConfig(level=logging.INFO)

    # Не запускаем polling, так как используется вебхук


async def run_fastapi():
    """Запуск FastAPI через uvicorn."""
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    """Запускаем бота, вебхуки и сервер FastAPI параллельно."""
    await on_startup()  # Вызов on_startup для установки вебхуков перед запуском
    await asyncio.gather(
        run_bot(),
        run_fastapi()
    )


if __name__ == '__main__':
    asyncio.run(main())
