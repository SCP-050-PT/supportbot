"""Обязательная подписка на канал (включается в админ-панели)."""
from __future__ import annotations

import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot import texts
from bot.db import Database
from bot.db.constants import STAFF_ROLES
from bot.keyboards.callbacks import CHECK_SUB
from bot.keyboards.inline import subscribe_kb
from bot.services.subscription import is_subscribed


class SubscriptionMiddleware(BaseMiddleware):
    def __init__(self, db: Database, ttl: int = 300) -> None:
        self.db = db
        self.ttl = ttl
        self._cache: dict[int, float] = {}  # user_id -> до какого момента не проверять

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        db_user = data.get("db_user")
        if db_user is None or db_user.get("role") in STAFF_ROLES:
            return await handler(event, data)
        if isinstance(event, CallbackQuery) and event.data == CHECK_SUB:
            return await handler(event, data)

        channel = await self.db.settings.get("channel")
        if not channel.get("enabled") or not channel.get("chat_id"):
            return await handler(event, data)

        user_id = db_user["_id"]
        now = time.monotonic()
        if self._cache.get(user_id, 0.0) > now:
            return await handler(event, data)

        bot: Bot = data["bot"]
        if await is_subscribed(bot, channel["chat_id"], user_id):
            if len(self._cache) > 10_000:
                self._cache.clear()
            self._cache[user_id] = now + self.ttl
            return await handler(event, data)

        text = texts.SUBSCRIBE_REQUIRED.format(title=texts.esc(channel.get("title") or "канал"))
        kb = subscribe_kb(channel.get("url", ""), channel.get("button_text") or "📢 Подписаться")
        if isinstance(event, CallbackQuery):
            await event.answer()
            await bot.send_message(user_id, text, reply_markup=kb)
        elif isinstance(event, Message):
            await event.answer(text, reply_markup=kb)
        return None
