import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from utils import library
from utils.config_parser import *
from handlers.fragment import fragment_router
from handlers.start import start_router

CONFIG_FILE = "config.ini"

if not os.path.isfile(CONFIG_FILE):
    create_config(CONFIG_FILE)
    logging.log(logging.WARN, f"Config file {CONFIG_FILE} created. Fill it before running.")
    exit(-1)
else:
    config = read_config(CONFIG_FILE)


async def main(token: str) -> None:
    dp = Dispatcher()
    dp.include_routers(
        start_router,
        fragment_router
    )
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    library.remove_cache()
    asyncio.run(main(config['Bot']['bot_token']))
