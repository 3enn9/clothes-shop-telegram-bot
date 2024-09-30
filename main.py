import asyncio
import logging
import uvicorn
from aiogram import Bot, Dispatcher
from middlewares.db import DataBaseSession
from database.engine import create_db, session_maker
from database.orm_query import orm_del_invoices
from handlers import router
from data.config import bot, app  # FastAPI импортирован как `app`

async def on_startup(bot):
    # Инициализация базы данных или других ресурсов
    await create_db()


async def on_shutdown(bot):
    # Очистка ресурсов перед завершением
    async with session_maker() as session:
        await orm_del_invoices(session, bot)
    print('бот лег')


async def run_bot():
    """Запуск Telegram-бота."""
    bot.my_admins_list = [877804669]
    dp = Dispatcher(bot=bot)
    dp.include_router(router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    logging.basicConfig(level=logging.INFO)

    await dp.start_polling(bot)


async def run_fastapi():
    """Запуск FastAPI через uvicorn."""
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    # Запускаем бота и сервер FastAPI параллельно
    await asyncio.gather(
        run_bot(),
        run_fastapi()
    )


if __name__ == '__main__':
    asyncio.run(main())
