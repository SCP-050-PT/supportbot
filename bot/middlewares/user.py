"""Регистрирует/обновляет пользователя и кладёт его в data["db_user"]."""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.types import Chat, TelegramObject, User

from bot.db import Database
from bot.db.constants import Role


class UserMiddleware(BaseMiddleware):
    def __init__(self, db: Database, admin_ids: frozenset[int]) -> None:
        self.db = db
        self.admin_ids = admin_ids

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")
        chat: Chat | None = data.get("event_chat")
        # Бот работает только в личных сообщениях
        if user is None or user.is_bot or chat is None or chat.type != ChatType.PRIVATE:
            return None

        is_admin = user.id in self.admin_ids
        db_user = await self.db.users.upsert_from_telegram(
            user.id, user.full_name, user.username, Role.ADMIN if is_admin else Role.USER
        )
        # Роль администратора всегда синхронизирована с ADMIN_IDS из .env
        if is_admin and db_user.get("role") != Role.ADMIN:
            db_user = await self.db.users.set_role(user.id, Role.ADMIN)
        elif not is_admin and db_user.get("role") == Role.ADMIN:
            db_user = await self.db.users.set_role(user.id, Role.USER)

        data["db_user"] = db_user
        return await handler(event, data)
