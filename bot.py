import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import aioschedule
from utils import library
from utils import database
from utils.config_parser import *
from handlers.fragment import fragment_router
from handlers.start import start_router
from handlers.profile import profile_router

CONFIG_FILE = "config.ini"

if not os.path.isfile(CONFIG_FILE):
    create_config(CONFIG_FILE)
    logging.log(logging.WARN, f"Config file {CONFIG_FILE} created. Fill it before running.")
    exit(-1)
else:
    config = read_config(CONFIG_FILE)


async def scheduler():
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def main(token: str) -> None:
    await database.init_pool()
    aioschedule.every().day.at("00:00").do(database.refund_all_free_tokens)
    asyncio.create_task(scheduler())
    dp = Dispatcher()
    dp.include_routers(
        start_router,
        fragment_router,
        profile_router
    )
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    library.remove_cache()
    asyncio.run(main(config['Bot']['bot_token']))
