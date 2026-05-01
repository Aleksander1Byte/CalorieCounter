import asyncio
import json
import logging
import os
import re
import io
import tempfile
from typing import Tuple

import httpx
from faster_whisper import WhisperModel
from aiogram import Router, html, F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from config import backend_url, REACTION_EMOJIS, WHISPER_MODEL_SIZE
from middleware import HeaderMiddleware
from random import choice

router = Router()
router.message.middleware(HeaderMiddleware())
client = httpx.AsyncClient(timeout=30.0)
NO_EMOJIS_RE = re.compile(r"[^a-zA-Zа-яА-ЯЁё0-9 %()\n]")
_whisper_model = None


async def check_connection():
    res = await client.get(
        backend_url + "/health",
    )
    if res.status_code == 200:
        logging.info("Установлено соединение с backend")
    else:
        logging.critical("Не установлено соединение с backend")
        raise ConnectionError


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
        f"Здравствуй, {html.bold(message.from_user.full_name)}!"
        f"\nОтправь мне описание блюда или его изображение"
        f" и я посчитаю его КБЖУ, а также "
        f"покажу 5 витаминов и минералов которых в нём больше всего :)"
        f"\n(Также можете попробовать /today /last /delete_last)"
    )


@router.message(Command("delete_last"))
async def delete_last_handler(message: Message, headers: dict) -> None:
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
            parse_mode="html",
        )
    elif result.status_code == 404:
        await message.answer("У вас не было подсчётов")


@router.message(Command("last"))
async def get_last_handler(message: Message, headers: dict) -> None:
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
                f"По моим <i>примерным</i> расчётам в "
                f"последнем блюде что вы съели "
                f"({text[:35]}{'...' if len(text) > 35 else ''}) было:"
            )
        else:
            msg = (
                "По моим <i>примерным</i> расчётам в "
                "последнем блюде что вы съели было:"
            )

        await message.answer(
            form_answer(
                result.json(),
                initial_message=msg,
                include_micro=True,
            ),
            parse_mode="html",
        )
    elif result.status_code == 404:
        await message.answer("У вас не было подсчётов")


def form_answer(
    json_data: json,
    initial_message: str = "По моим <i>примерным</i> расчётам вы съели:",
    include_micro: bool = False,
    image: bool = False,
) -> str:
    if json_data["calories"] is None:
        return "Тут ничего нет :)"

    if image:
        initial_message = (
            "Похоже, что это:"
            "\n<b>"
            + json_data["text"].capitalize()
            + "</b>\n\nВ этом содержится <i>примерно</i>:"
        )

    ans = (
        initial_message + "\n" + f"<b>{json_data['calories']}</b> калорий 🍴\n"
        f"<b>{json_data['protein']}</b> белков 💪\n"
        f"<b>{json_data['fat']}</b> жиров 🧈\n"
        f"<b>{json_data['carbs']}</b> углеводов 🍚\n"
    )

    llm_raw = json_data.get("llm_raw") or {}
    if not isinstance(llm_raw, dict):
        llm_raw = {}

    estimated_weight_g = llm_raw.get("estimated_weight_g")
    if isinstance(estimated_weight_g, (int, float)) and estimated_weight_g > 0:
        ans += (
            "Примерный вес порции: "
            f"<b>{round(estimated_weight_g)} г</b> ⚖️\n"
        )

    if include_micro:
        if not llm_raw.get("micro"):
            logging.warning(
                "При включеном include_micro не оказалось"
                " данных о витаминах и минералах"
            )
            return ans
        ans += "\nПомимо этого там содержалось:\n"
        for item in llm_raw["micro"]:
            ans += f"{item['name']} {item['percent_dv']}%\n"
        ans += (
            "\n<i>(Проценты рассчитаны от дневной нормы "
            "витаминов/минералов "
            "среднестатистического 25-летнего мужчины)</i>"
        )
    return ans


@router.message(Command("today"))
async def today_handler(message: Message, headers: dict) -> None:
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
                initial_message="По моим <i>примерным</i> "
                "расчётам за сегодня вы съели:",
            ),
            parse_mode="html",
        )
    elif result.status_code == 404:
        await message.answer("За сегодня у вас не было подсчётов")


async def _download_tg_file(
    bot: Bot,
    file_id: str,
) -> Tuple[io.BytesIO, str]:
    file = await bot.get_file(file_id)
    buf = io.BytesIO()
    await bot.download_file(file.file_path, destination=buf)
    buf.seek(0)
    return buf, file.file_path


@router.message(F.voice)
async def voice_handler(message: Message, headers: dict) -> None:
    voice = message.voice
    logging.info(
        "tg_user_id=%s method=VOICE duration=%s",
        message.from_user.id,
        voice.duration if voice else None,
    )

    if not voice:
        await message.answer(
            "С вашим запросом что-то не так, попробуйте переформулировать"
        )
        return

    if voice.duration and voice.duration > 120:
        logging.info(
            "tg_user_id=%s voice rejected by duration=%s",
            message.from_user.id,
            voice.duration,
        )
        await message.answer(
            "Голосовые длиннее 2 минут я не принимаю. "
            "Попробуйте отправить более короткую запись."
        )
        return

    temp_msg = None
    temp_path = None
    try:
        buf, tg_file_path = await _download_tg_file(
            message.bot,
            voice.file_id,
        )
        _, suffix = os.path.splitext(tg_file_path or "")
        if not suffix:
            suffix = ".oga"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(buf.read())
            temp_path = tmp.name

        temp_msg = await message.answer("Подумаю 🤔")

        def transcribe_voice():
            global _whisper_model
            if _whisper_model is None:
                _whisper_model = WhisperModel(
                    WHISPER_MODEL_SIZE,
                    device="cpu",
                    compute_type="int8",
                )
            segments, _ = _whisper_model.transcribe(temp_path)
            return " ".join(
                segment.text.strip() for segment in segments if segment.text
            ).strip()

        transcription = await asyncio.to_thread(transcribe_voice)
    except Exception:
        logging.exception(
            "tg_user_id=%s voice transcription failed",
            message.from_user.id,
        )
        await message.answer(
            "С вашим запросом что-то не так, попробуйте переформулировать"
        )
        if temp_msg:
            try:
                await temp_msg.delete()
            except Exception:
                logging.warning("Не удалось удалить временное сообщение")
        return
    finally:
        if temp_path:
            try:
                os.remove(temp_path)
            except OSError:
                logging.warning("Не удалось удалить временный voice-файл")

    text = "".join(NO_EMOJIS_RE.split(transcription))
    if not text:
        logging.warning(
            "tg_user_id=%s voice transcription is empty",
            message.from_user.id,
        )
        await message.answer(
            "С вашим запросом что-то не так, попробуйте переформулировать"
        )
        if temp_msg:
            try:
                await temp_msg.delete()
            except Exception:
                logging.warning("Не удалось удалить временное сообщение")
        return

    logging.info(
        "tg_user_id=%s voice transcription succeeded length=%s",
        message.from_user.id,
        len(text),
    )

    transcription_message = f'Я распознал:\n\n"{text}"'
    for start in range(0, len(transcription_message), 3900):
        await message.answer(transcription_message[start: start + 3900])

    try:
        result = await client.post(
            backend_url + "/meal/",
            headers=headers,
            data={"text": text},
        )
    except httpx.ConnectError:
        await message.answer("Что-то пошло не так")
        logging.critical("Не произошло подключение к backend")
        return
    finally:
        if temp_msg:
            try:
                await temp_msg.delete()
            except Exception:
                logging.warning("Не удалось удалить временное сообщение")

    await manage_response(message, result)


@router.message(F.photo)
async def photo_handler(message: Message, headers: dict) -> None:
    if message.photo:
        file_id = message.photo[-1].file_id
    else:
        file_id = message.document.file_id

    buf, tg_file_path = await _download_tg_file(message.bot, file_id)
    temp_msg = await message.answer("Подумаю 🤔")
    result = await client.post(
        backend_url + "/meal/",
        headers=headers,
        files={
            "file": ("image.jpg", buf, "image/jpeg"),
        },
        data={"text": message.caption or "Проанализируй это изображение"},
    )
    try:
        await temp_msg.delete()
    except Exception:
        logging.warning("Не удалось удалить временное сообщение")
    await manage_response(message, result, image=True)


@router.message(F.text)
async def message_handler(message: Message, headers: dict) -> None:
    text = message.text
    if not text or text is None:
        await message.answer(
            "Я понимаю только текстовое описание блюда или картинки"
        )
        return
    text = "".join(NO_EMOJIS_RE.split(message.text))
    if not text:
        await message.answer("Используйте только текст")
        return

    logging.info("tg_user_id=%s text=%s", message.from_user.id, text)
    temp_msg = await message.answer("Подумаю 🤔")
    try:
        result = await client.post(
            backend_url + "/meal/",
            headers=headers,
            data={"text": text},
        )
    except httpx.ConnectError:
        await message.answer("Что-то пошло не так")
        logging.critical("Не произошло подключение к backend")
        return

    try:
        await temp_msg.delete()
    except Exception:
        logging.warning("Не удалось удалить временное сообщение")

    await manage_response(message, result)


async def manage_response(message, result, **kwargs):
    if result.status_code == 200:
        await message.answer(
            form_answer(result.json(), include_micro=True, **kwargs),
            parse_mode="html",
        )
        await message.react([choice(REACTION_EMOJIS)])
    elif result.status_code == 400:
        await message.answer(
            "С вашим запросом что-то не так, попробуйте переформулировать"
        )
    elif result.status_code == 429:
        logging.critical("Подключение к LLM не удалось")
        await message.answer("Попробуйте позже")
    else:
        logging.error(f"Ошибка {result.status_code}; Запрос {result.request}")
        await message.answer("Что-то пошло не так")
