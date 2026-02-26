import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNetworkError

from config import TG_BOT_KEY
from handlers import check_connection, router

TOKEN = TG_BOT_KEY

dp = Dispatcher()


async def main() -> None:
    bot = Bot(
        token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp.include_router(router)

    await check_connection()
    try:
        await bot.delete_webhook(drop_pending_updates=True, request_timeout=30)
    except TelegramNetworkError as e:
        print(f"delete_webhook failed: {e}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    asyncio.run(main())
