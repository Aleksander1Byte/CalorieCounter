import json
import logging

import httpx

from app.core.config import GEMMA_KEY, DEEPSEEK_KEY, ADMIN_ID_TG
from app.exceptions import StrangeRequestException
from openai import AsyncOpenAI

ADMIN_TG_USER_ID = ADMIN_ID_TG
ADMIN_DEEPSEEK_MODEL = "deepseek-v4-pro"


class GeminiClient:
    def __init__(self):
        self.counter = 0
        self.key = GEMMA_KEY
        self.headers = {
            "Content-Type": "application/json",
        }
        self.url = (
            f"https://generativelanguage.googleapis.com/"
            f"v1beta/models/gemma-3-27b-it:generateContent?key={self.key}"
        )

        self.client = httpx.AsyncClient(timeout=90.0)
        self.client_ds = AsyncOpenAI(
            timeout=90,
            api_key=DEEPSEEK_KEY,
            base_url="https://api.deepseek.com",
        )
        with open("app/llm/LLM_template.txt", encoding="utf-8", mode="r") as f:
            self.prompt = f.read()

    async def fallback_to_deepseek(
        self,
        text: str,
        image: bytes,
        model: str = "deepseek-chat",
    ):
        """Emergency method for fallbacks
        We do not want to process images with DeepSeek
        We use this ONLY if Gemma is 429, ~and ONLY for 30 requests~"""
        logging.warning(f"Called fallback to deepseek with {text=}")
        # if image and self.counter > 30:
        #     raise HTTPStatusError

        kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": text},
            ],
            "stream": False,
        }

        response = await self.client_ds.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    async def process(
        self,
        text: str,
        image: bytes,
        content_type: str,
        tg_user_id: int | None = None,
    ):
        try:
            if tg_user_id == ADMIN_TG_USER_ID:
                # Admin-only override: use DeepSeek Pro in non-thinking mode.
                data = GeminiClient._parse_ds(
                    await self.fallback_to_deepseek(
                        text=text,
                        image=image,
                        model=ADMIN_DEEPSEEK_MODEL,
                    )
                )
                logging.info(f"Called admin DeepSeek with {text=}")
            else:
                response_json = await self.request(text, image, content_type)
                data = response_json["candidates"][0]["content"]["parts"][0][
                    "text"
                ]
                logging.info(f"Called Gemma with {text=}")
        except Exception:
            if tg_user_id == ADMIN_TG_USER_ID:
                raise
            data = GeminiClient._parse_ds(
                await self.fallback_to_deepseek(text=text, image=image)
            )
        return GeminiClient._parse(data)

    @staticmethod
    def _parse_ds(model_output: str):
        return GeminiClient._parse(model_output)

    @staticmethod
    def _parse(model_output: str):
        if isinstance(model_output, dict):
            return model_output
        if not isinstance(model_output, str):
            raise StrangeRequestException

        payload = model_output.strip()
        if payload.startswith("```"):
            lines = payload.splitlines()
            if lines and lines[0].strip().lower() in ("```json", "```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            payload = "\n".join(lines).strip()

        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            raise StrangeRequestException

    async def _resumable_upload(self, image_bytes):
        response = await self.client.post(
            f"https://generativelanguage.googleapis.com/"
            f"upload/v1beta/files?key={self.key}",
            headers={
                "X-Goog-Upload-Protocol": "resumable",
                "X-Goog-Upload-Command": "start",
                "X-Goog-Upload-Header-Content-Length": str(len(image_bytes)),
                "X-Goog-Upload-Header-Content-Type": "image/jpeg",
                "Content-Type": "application/json",
            },
            json={"file": {"display_name": "cats-and-dogs"}},
        )
        upload = await self.client.post(
            response.headers["X-Goog-Upload-URL"],
            headers={
                "Content-Length": str(len(image_bytes)),
                "X-Goog-Upload-Offset": "0",
                "X-Goog-Upload-Command": "upload, finalize",
            },
            content=image_bytes,
        )
        upload.raise_for_status()
        data = upload.json()
        return data["file"]["uri"]

    async def request(self, text: str, image: bytes, content_type: str):
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{self.prompt}\n{text}"},
                    ],
                }
            ]
        }
        if image:
            payload["contents"][0]["parts"] += (
                {
                    "file_data": {
                        "mime_type": content_type,
                        "file_uri": await self._resumable_upload(image),
                    },
                },
            )
        r = await self.client.post(
            self.url, headers=self.headers, json=payload
        )
        r.raise_for_status()
        return r.json()
