import json

import httpx

from app.core.config import GEMINI_KEY


class GeminiClient:
    def __init__(self):
        self.key = GEMINI_KEY
        self.headers = {
            "x-goog-api-key": self.key,
            "Content-Type": "application/json",
        }
        self.url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/gemini-2.5-flash:generateContent"
        )

        self.client = httpx.AsyncClient(timeout=30.0)
        with open("app/llm/LLM_template.txt", encoding="utf-8", mode="r") as f:
            self.prompt = f.read()

    async def process(self, text):
        response_json = await self.request(text)
        data = response_json["candidates"][0]["content"]["parts"][0]["text"]
        return GeminiClient._parse(data)

    @staticmethod
    def _parse(model_output: str):
        return json.loads(model_output[7:-4])

    async def request(self, text):
        payload = {
            "contents": [{"parts": [{"text": f"{self.prompt}\n{text}"}]}]
        }
        r = await self.client.post(
            self.url, headers=self.headers, json=payload
        )
        r.raise_for_status()
        return r.json()
