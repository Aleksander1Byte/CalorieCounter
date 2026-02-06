from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

from config import SECRET_KEY


class HeaderMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        self.headers = {
            "x-tg-user-id": str(event.from_user.id),
            "Authorization": f"Bearer {SECRET_KEY}",
            "Content-Type": "application/json",
        }
        data["headers"] = self.headers
        return await handler(event, data)
