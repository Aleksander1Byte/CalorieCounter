import json

import httpx

from app.core.config import GEMMA_KEY


class GeminiClient:
    def __init__(self):
        self.key = GEMMA_KEY
        self.headers = {
            "Content-Type": "application/json",
        }
        self.url = (
            f"https://generativelanguage.googleapis.com/"
            f"v1beta/models/gemma-3-27b-it:generateContent?key={self.key}"
        )

        self.client = httpx.AsyncClient(timeout=30.0)
        with open("app/llm/LLM_template.txt", encoding="utf-8", mode="r") as f:
            self.prompt = f.read()

    async def process(self, text: str, image: bytes, content_type: str):
        response_json = await self.request(text, image, content_type)
        data = response_json["candidates"][0]["content"]["parts"][0]["text"]
        return GeminiClient._parse(data)

    @staticmethod
    def _parse(model_output: str):
        return json.loads(model_output[7:-4])

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
        print(r.text)
        r.raise_for_status()
        return r.json()
