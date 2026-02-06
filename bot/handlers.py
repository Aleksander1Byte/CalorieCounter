import json
import logging

import httpx
from aiogram import Router, html
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from config import SECRET_KEY, backend_url

router = Router()
client = httpx.AsyncClient(timeout=30.0)


async def check_connection():
    res = await client.get(backend_url + "/health")
    if res.status_code == 200:
        logging.info("Установлено соединение с backend")
    else:
        logging.critical("Не установлено соединение с backend")
        raise ConnectionError


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
        f"Здравствуй, {html.bold(message.from_user.full_name)}!"
        f"\nОтправь мне описание блюда и я посчитаю его КБЖУ, а также "
        f"покажу 5 витаминов и минералов которых в нём больше всего :)"
        f"\n(Также можете попробовать /today /last /delete_last)"
    )


@router.message(Command("delete_last"))
async def delete_last_handler(message: Message) -> None:
    headers = {
        "x-tg-user-id": str(message.from_user.id),
        "Authorization": f"Bearer {SECRET_KEY}",
        "Content-Type": "application/json",
    }
    logging.info("tg_user_id=%s method=DELETE LAST", message.from_user.id)
    try:
        result = await client.delete(
            backend_url + "/meal/last", headers=headers
        )
    except httpx.ConnectError:
        await message.answer("Что-то пошло не так")
        logging.critical("Не произошло подключение к backend")
        return

    if result.status_code == 200:
        text = result.json()["text"]
        msg = (
            f"Вы успешно удалили запись "
            f"({text[:35]}{'...' if len(text) > 35 else ''})."
            f" В этом блюде содержалось:"
        )

        await message.answer(
            form_answer(
                result.json(),
                initial_message=msg,
            ),
            parse_mode="markdown",
        )
    elif result.status_code == 404:
        await message.answer("У вас не было подсчётов")


@router.message(Command("last"))
async def get_last_handler(message: Message) -> None:
    headers = {
        "x-tg-user-id": str(message.from_user.id),
        "Authorization": f"Bearer {SECRET_KEY}",
        "Content-Type": "application/json",
    }
    logging.info("tg_user_id=%s method=GET LAST", message.from_user.id)
    try:
        result = await client.get(backend_url + "/meal/last", headers=headers)
    except httpx.ConnectError:
        await message.answer("Что-то пошло не так")
        logging.critical("Не произошло подключение к backend")
        return

    if result.status_code == 200:
        text = result.json()["text"]
        if text:
            msg = (
                f"По моим _примерным_ расчётам в "
                f"последнем блюде что вы съели "
                f"({text[:35]}{'...' if len(text) > 35 else ''}) было:"
            )
        else:
            msg = (
                "По моим _примерным_ расчётам в "
                "последнем блюде что вы съели было:"
            )

        await message.answer(
            form_answer(
                result.json(),
                initial_message=msg,
            ),
            parse_mode="markdown",
        )
    elif result.status_code == 404:
        await message.answer("У вас не было подсчётов")


def form_answer(
    json_data: json,
    initial_message: str = "По моим _примерным_ расчётам вы съели:",
    include_micro=False,
) -> str:
    ans = (
        initial_message + "\n" + f"*{json_data['calories']}* калорий 🍴\n"
        f"*{json_data['protein']}* белков 💪\n"
        f"*{json_data['fat']}* жиров 🧈\n"
        f"*{json_data['carbs']}* углеводов 🍚\n"
    )
    if include_micro:
        pass  # TODO
    return ans


@router.message(Command("today"))
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
        await message.answer(
            form_answer(
                result.json(),
                initial_message="По моим _примерным_ "
                "расчётам за сегодня вы съели:",
            ),
            parse_mode="markdown",
        )
    elif result.status_code == 404:
        await message.answer("За сегодня у вас не было подсчётов")


@router.message()
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
        await message.answer(
            form_answer(result.json(), include_micro=True),
            parse_mode="markdown",
        )

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
