"""Проверка подписки пользователя на канал."""
from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

logger = logging.getLogger(__name__)

_SUBSCRIBED = {"creator", "administrator", "member"}


async def is_subscribed(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
    except TelegramAPIError as exc:
        # Если бот потерял доступ к каналу — не блокируем пользователей
        logger.warning("Не удалось проверить подписку %s в %s: %s", user_id, chat_id, exc)
        return True
    status = str(getattr(member.status, "value", member.status))
    if status in _SUBSCRIBED:
        return True
    if status == "restricted":
        return bool(getattr(member, "is_member", False))
    return False
