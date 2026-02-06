import asyncio
import json
import logging
import sys

import httpx
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from config import BACKEND_PORT, BACKEND_URL, SECRET_KEY, TG_BOT_KEY

TOKEN = TG_BOT_KEY

dp = Dispatcher()
backend_url = f"http://{BACKEND_URL}:{BACKEND_PORT}/v1"


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
        f"Здравствуй, {html.bold(message.from_user.full_name)}!"
        f"\nОтправь мне описание блюда и я посчитаю его КБЖУ, а также "
        f"покажу 5 витаминов и минералов которых в нём больше всего :)"
        f"\n(Также можете попробовать /today)"
    )


def form_answer(json_data: json) -> str:
    ans = (
        f"По моим _примерным_ расчётам вы съели:\n"
        f"*{json_data['calories']}* калорий 🍴\n"
        f"*{json_data['protein']}* белков 💪\n"
        f"*{json_data['fat']}* жиров 🧈\n"
        f"*{json_data['carbs']}* углеводов 🍚\n"
    )
    return ans


@dp.message(Command("today"))
async def today_handler(message: Message) -> None:
    headers = {
        "x-tg-user-id": str(message.from_user.id),
        "Authorization": f"Bearer {SECRET_KEY}",
        "Content-Type": "application/json",
    }
    logging.info("tg_user_id=%s method=TODAY", message.from_user.id)

    try:
        result = await client.get(backend_url + "/meal/today", headers=headers)
    except httpx.ConnectError:
        await message.answer("Что-то пошло не так")
        logging.critical("Не произошло подключение к backend")
        return

    if result.status_code == 200:
        await message.answer(form_answer(result.json()), parse_mode="markdown")
    elif result.status_code == 404:
        await message.answer("За сегодня у вас не было подсчётов")


@dp.message()
async def message_handler(message: Message) -> None:
    if not message.text:
        await message.answer("Я понимаю только текстовое описание блюда")
        return
    headers = {
        "x-tg-user-id": str(message.from_user.id),
        "Authorization": f"Bearer {SECRET_KEY}",
        "Content-Type": "application/json",
    }
    logging.info(
        "tg_user_id=%s text=%s", message.from_user.id, message.text[:200]
    )
    try:
        result = await client.post(
            backend_url + "/meal/",
            headers=headers,
            json={"text": message.text},
        )
    except httpx.ConnectError:
        await message.answer("Что-то пошло не так")
        logging.critical("Не произошло подключение к backend")
        return

    if result.status_code == 200:
        await message.answer(form_answer(result.json()), parse_mode="markdown")

    elif result.status_code == 400:
        await message.answer(
            "С вашим запросом что-то не так, попробуйте переформулировать"
        )
    elif result.status_code == 429:
        logging.critical("Подключение к LLM не удалось")
        await message.answer("Попробуйте позже")
    else:
        logging.error(f"Ошибка {result.status_code}; Запрос {result.request}")
        await message.answer(f"Что-то очень пошло не так {result.status_code}")


async def check_connection():
    res = await client.get(backend_url + "/health")
    if res.status_code == 200:
        logging.info("Установлено соединение с backend")
    else:
        logging.critical("Не установлено соединение с backend")
        raise ConnectionError


async def main() -> None:
    bot = Bot(
        token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    await check_connection()
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    client = httpx.AsyncClient(timeout=30.0)
    asyncio.run(main())
