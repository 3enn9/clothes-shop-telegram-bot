import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from data import config

from database.engine import create_db, drop_db, session_maker
from handlers import router
from middlewares.db import DataBaseSession


async def on_startup(bot):
    # await drop_db()

    await create_db()


async def on_shutdown(bot):
    print('бот лег')


async def main():
    API_TOKEN = config.TOKEN
    bot = Bot(token=API_TOKEN)
    bot.my_admins_list = []
    dp = Dispatcher(bot=bot)
    dp.include_router(router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    logging.basicConfig(level=logging.INFO)

    await bot.delete_webhook()
    await dp.start_polling(bot)



    # # Создание веб-приложения для обработки запросов
    # app = web.Application()
    # webhook_path = '/webhook'  # Указанный путь для вебхука
    # SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=webhook_path)
    # setup_application(app, dp, bot=bot)
    #
    # # Запуск веб-приложения на всех интерфейсах и порту 443
    # runner = web.AppRunner(app)
    # await runner.setup()
    # site = web.TCPSite(runner, host='0.0.0.0', port=443)
    # await site.start()
    #
    # print(f"Bot is running on {os.getenv('URL_APP')}")
    #
    # # Ожидание сигнала завершения
    # try:
    #     while True:
    #         await asyncio.sleep(3600)  # Keep alive
    # except (KeyboardInterrupt, SystemExit):
    #     pass
    # finally:
    #     await runner.cleanup()


if __name__ == '__main__':
    asyncio.run(main())
