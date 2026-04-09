from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class AllowedUsersMiddleware(BaseMiddleware):
    """Drop message events whose sender is not in the configured allowlist."""

    def __init__(self, allowed_user_ids: frozenset[int]) -> None:
        self._allowed_user_ids = allowed_user_ids

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not hasattr(event, "from_user"):
            return await handler(event, data)
        user = event.from_user
        if user is None or user.id not in self._allowed_user_ids:
            return None
        return await handler(event, data)
