"""Блокировка забаненных пользователей."""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot import texts
from bot.db.constants import STAFF_ROLES


class BanMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        db_user = data.get("db_user") or {}
        if db_user.get("is_banned") and db_user.get("role") not in STAFF_ROLES:
            if isinstance(event, CallbackQuery):
                await event.answer(texts.BANNED, show_alert=True)
            elif isinstance(event, Message):
                await event.answer(texts.BANNED)
            return None
        return await handler(event, data)
