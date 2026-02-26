import json
import logging

import httpx
from httpx import HTTPStatusError

from app.core.config import GEMMA_KEY, DEEPSEEK_KEY
from app.exceptions import StrangeRequestException
from openai import AsyncOpenAI


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

        self.client = httpx.AsyncClient(timeout=30.0)
        self.client_ds = AsyncOpenAI(
            timeout=30,
            api_key=DEEPSEEK_KEY,
            base_url="https://api.deepseek.com",
        )
        with open("app/llm/LLM_template.txt", encoding="utf-8", mode="r") as f:
            self.prompt = f.read()

    async def fallback_to_deepseek(self, text: str, image: bytes):
        """Emergency method for fallbacks
        We do not want to process images with DeepSeek
        We use this ONLY if Gemma is 429, and ONLY for 30 requests"""
        logging.warning("Fallback to deepseek with text=", text)
        if image and self.counter > 30:
            raise HTTPStatusError

        response = await self.client_ds.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": text},
            ],
            stream=False
        )
        return response.choices[0].message.content

    async def process(self, text: str, image: bytes, content_type: str):
        try:
            response_json = await self.request(text, image, content_type)
            data = response_json["candidates"][0]["content"]["parts"][0][
                "text"
            ]
        except Exception:
            data = GeminiClient._parse_ds(
                await self.fallback_to_deepseek(text=text, image=image)
            )
        return GeminiClient._parse(data)

    @staticmethod
    def _parse_ds(model_output: str):
        try:
            return json.loads(model_output)
        except Exception:
            raise HTTPStatusError

    @staticmethod
    def _parse(model_output: str):
        try:
            return json.loads(model_output[7:-4])
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
